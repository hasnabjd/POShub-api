#!/usr/bin/env python3
"""
Script pour déployer la queue SQS et configurer les paramètres SSM.

Usage:
    python scripts/deploy_sqs_queue.py --stage dev
    python scripts/deploy_sqs_queue.py --stage dev --deploy-stack
"""

import argparse
import boto3
import json
import sys
from typing import Optional

def get_queue_url(stage: str, region: str = "eu-north-1") -> Optional[str]:
    """
    Récupère l'URL de la queue SQS depuis AWS.
    
    Args:
        stage: Environnement (dev, staging, prod)
        region: Région AWS
        
    Returns:
        URL de la queue ou None si non trouvée
    """
    try:
        sqs = boto3.client('sqs', region_name=region)
        queue_name = f"poshub-orders-{stage}-h"
        
        response = sqs.get_queue_url(QueueName=queue_name)
        return response['QueueUrl']
    except Exception as e:
        print(f"⚠️ Queue {queue_name} non trouvée: {e}")
        return None

def create_queue_manually(stage: str, region: str = "eu-north-1") -> bool:
    """
    Crée la queue SQS manuellement (alternative à la console).
    
    Args:
        stage: Environnement (dev, staging, prod)
        region: Région AWS
        
    Returns:
        True si succès, False sinon
    """
    try:
        sqs = boto3.client('sqs', region_name=region)
        queue_name = f"poshub-orders-{stage}-h"
        dlq_name = f"poshub-orders-dlq-{stage}-h"
        
        print(f"🚀 Création des queues SQS pour l'environnement: {stage}")
        
        # Créer la Dead Letter Queue d'abord
        dlq_response = sqs.create_queue(
            QueueName=dlq_name,
            Attributes={
                'MessageRetentionPeriod': '1209600',  # 14 jours
            }
        )
        dlq_url = dlq_response['QueueUrl']
        print(f"✅ Dead Letter Queue créée: {dlq_url}")
        
        # Récupérer l'ARN de la DLQ
        dlq_attributes = sqs.get_queue_attributes(
            QueueUrl=dlq_url,
            AttributeNames=['QueueArn']
        )
        dlq_arn = dlq_attributes['Attributes']['QueueArn']
        
        # Créer la queue principale
        redrive_policy = {
            "deadLetterTargetArn": dlq_arn,
            "maxReceiveCount": 3
        }
        
        queue_response = sqs.create_queue(
            QueueName=queue_name,
            Attributes={
                'VisibilityTimeout': '30',
                'MessageRetentionPeriod': '1209600',  # 14 jours
                'ReceiveMessageWaitTimeSeconds': '20',  # Long polling
                'RedrivePolicy': json.dumps(redrive_policy)
            }
        )
        queue_url = queue_response['QueueUrl']
        print(f"✅ Queue principale créée: {queue_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des queues: {e}")
        return False

def update_ssm_parameter(stage: str, queue_url: str, region: str = "eu-north-1") -> bool:
    """
    Met à jour le paramètre SSM avec l'URL réelle de la queue.
    
    Args:
        stage: Environnement (dev, staging, prod)
        queue_url: URL de la queue SQS
        region: Région AWS
        
    Returns:
        True si succès, False sinon
    """
    try:
        ssm = boto3.client('ssm', region_name=region)
        parameter_name = f"/pos/{stage}/queue-url"
        
        ssm.put_parameter(
            Name=parameter_name,
            Value=queue_url,
            Type='String',
            Description=f'URL de la queue SQS pour les commandes - {stage}',
            Overwrite=True
        )
        
        print(f"✅ Paramètre SSM mis à jour: {parameter_name} = {queue_url}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du paramètre SSM: {e}")
        return False

def deploy_sam_stack(stage: str) -> bool:
    """
    Déploie le stack SAM avec les nouvelles ressources.
    
    Args:
        stage: Environnement (dev, staging, prod)
        
    Returns:
        True si succès, False sinon
    """
    import subprocess
    
    try:
        print(f"🚀 Déploiement du stack SAM pour l'environnement: {stage}")
        
        # Construire le stack
        build_cmd = ["sam", "build", "--template-file", "sam-min.yml"]
        print(f"📦 Construction: {' '.join(build_cmd)}")
        
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Erreur lors de la construction: {result.stderr}")
            return False
        
        print("✅ Construction terminée")
        
        # Déployer le stack
        deploy_cmd = [
            "sam", "deploy",
            "--template-file", "sam-min.yml",
            "--parameter-overrides", f"Stage={stage}",
            "--capabilities", "CAPABILITY_IAM",
            "--resolve-s3"
        ]
        
        print(f"🚀 Déploiement: {' '.join(deploy_cmd)}")
        
        result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Erreur lors du déploiement: {result.stderr}")
            return False
        
        print("✅ Déploiement terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du déploiement SAM: {e}")
        return False

def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description="Déploie la queue SQS et configure les paramètres SSM"
    )
    
    parser.add_argument(
        "--stage",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Environnement de déploiement"
    )
    
    parser.add_argument(
        "--region",
        default="eu-north-1",
        help="Région AWS (défaut: eu-north-1)"
    )
    
    parser.add_argument(
        "--deploy-stack",
        action="store_true",
        help="Déploie automatiquement le stack SAM"
    )
    
    parser.add_argument(
        "--create-queue",
        action="store_true",
        help="Crée la queue SQS manuellement (alternative à la console)"
    )
    
    args = parser.parse_args()
    
    print(f"🌍 Région AWS: {args.region}")
    print(f"🎯 Environnement: {args.stage}")
    
    success = True
    
    if args.deploy_stack:
        # Option 1: Déployer via SAM (recommandé)
        print("\n📋 Option 1: Déploiement via SAM Template")
        if not deploy_sam_stack(args.stage):
            success = False
        else:
            # Attendre un peu pour que la queue soit créée
            import time
            print("⏳ Attente de la création de la queue...")
            time.sleep(10)
            
            # Récupérer l'URL de la queue créée
            queue_url = get_queue_url(args.stage, args.region)
            if queue_url:
                print(f"✅ Queue URL récupérée: {queue_url}")
            else:
                print("⚠️ Impossible de récupérer l'URL de la queue")
                
    elif args.create_queue:
        # Option 2: Création manuelle
        print("\n📋 Option 2: Création manuelle des queues")
        if create_queue_manually(args.stage, args.region):
            queue_url = get_queue_url(args.stage, args.region)
            if queue_url and update_ssm_parameter(args.stage, queue_url, args.region):
                print("✅ Configuration terminée avec succès!")
            else:
                success = False
        else:
            success = False
            
    else:
        # Instructions pour création manuelle dans la console
        print("\n📋 Instructions pour la création manuelle dans la console AWS:")
        print(f"1. Aller dans SQS Console dans la région {args.region}")
        print(f"2. Créer une queue Standard avec le nom: poshub-orders-{args.stage}")
        print("3. Configurer:")
        print("   - Visibility Timeout: 30 secondes")
        print("   - Message Retention Period: 14 jours")
        print("   - Receive Message Wait Time: 20 secondes (Long polling)")
        print("4. Optionnel: Créer une Dead Letter Queue: poshub-orders-dlq-{args.stage}")
        print("\n5. Après création, exécuter:")
        print(f"   python scripts/setup_ssm_parameters.py --stage {args.stage} --overwrite")
        print("\nOu utiliser:")
        print(f"   python scripts/deploy_sqs_queue.py --stage {args.stage} --deploy-stack")
        print(f"   python scripts/deploy_sqs_queue.py --stage {args.stage} --create-queue")
    
    if success:
        print(f"\n🎉 Configuration de la queue SQS terminée pour l'environnement: {args.stage}")
        print(f"📝 Paramètre SSM configuré: /pos/{args.stage}/queue-url")
    else:
        print(f"\n❌ Échec de la configuration pour l'environnement: {args.stage}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
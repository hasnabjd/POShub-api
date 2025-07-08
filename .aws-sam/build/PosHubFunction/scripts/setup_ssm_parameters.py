#!/usr/bin/env python3
"""
Script pour créer les paramètres SSM nécessaires au fonctionnement de l'API POSHub.

Usage:
    python scripts/setup_ssm_parameters.py --stage dev
    python scripts/setup_ssm_parameters.py --stage prod --api-key "real-production-key"
"""

import argparse
import sys
from typing import Optional

import boto3
from botocore.exceptions import ClientError


def create_ssm_parameter(
    ssm_client,
    parameter_name: str,
    parameter_value: str,
    parameter_type: str = "SecureString",
    description: str = "",
    overwrite: bool = False,
) -> bool:
    """
    Crée ou met à jour un paramètre SSM.

    Args:
        ssm_client: Client boto3 SSM
        parameter_name: Nom du paramètre (ex: /pos/api-key)
        parameter_value: Valeur du paramètre
        parameter_type: Type du paramètre (String, StringList, SecureString)
        description: Description du paramètre
        overwrite: Si True, écrase le paramètre existant

    Returns:
        True si succès, False sinon
    """
    try:
        print(f"📝 Création du paramètre: {parameter_name}")

        response = ssm_client.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Type=parameter_type,
            Description=description,
            Overwrite=overwrite,
        )

        print(f"✅ Paramètre créé - Version: {response['Version']}")
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ParameterAlreadyExists":
            print(f"⚠️ Paramètre déjà existant: {parameter_name}")
            print("   Utilisez --overwrite pour le remplacer")
        else:
            print(f"❌ Erreur lors de la création: {error_code} - {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False


def setup_poshub_parameters(
    stage: str, api_key: Optional[str] = None, overwrite: bool = False
):
    """
    Configure tous les paramètres SSM nécessaires pour POSHub API.

    Args:
        stage: Environnement (dev, staging, prod)
        api_key: Clé API personnalisée (sinon génère une clé de test)
        overwrite: Si True, écrase les paramètres existants
    """
    print(f"🚀 Configuration des paramètres SSM pour l'environnement: {stage}")

    # Initialiser le client SSM
    try:
        ssm_client = boto3.client("ssm")
        print("✅ Client SSM initialisé")
    except Exception as e:
        print(f"❌ Impossible d'initialiser le client SSM: {e}")
        print("   Vérifiez vos credentials AWS et votre région")
        return False

    # Définir la clé API selon l'environnement
    if not api_key:
        if stage == "prod":
            print(
                "❌ ERREUR: Une clé API doit être fournie pour la production"
            )
            print("   Utilisez: --api-key 'votre-clé-sécurisée'")
            return False
        else:
            # Clé de test pour dev/staging
            api_key = f"test-api-key-{stage}-123456"
            print(f"🔧 Utilisation d'une clé de test: {api_key}")

    # Paramètres à créer
    parameters = [
        {
            "name": "/pos/api-key",
            "value": api_key,
            "type": "SecureString",
            "description": f"Clé API pour POSHub - Environnement: {stage}",
        },
        {
            "name": f"/pos/{stage}/config/timeout",
            "value": "30",
            "type": "String",
            "description": f"Timeout des requêtes HTTP - {stage}",
        },
        {
            "name": f"/pos/{stage}/config/max-connections",
            "value": "100",
            "type": "String",
            "description": f"Nombre maximum de connexions HTTP - {stage}",
        },
        {
            "name": f"/pos/{stage}/queue-url",
            "value": f"https://sqs.eu-north-1.amazonaws.com/ACCOUNT_ID/poshub-orders-{stage}-h",
            "type": "String",
            "description": f"URL de la queue SQS pour les commandes - {stage}",
        },
    ]

    # Créer les paramètres
    success_count = 0
    for param in parameters:
        success = create_ssm_parameter(
            ssm_client=ssm_client,
            parameter_name=param["name"],
            parameter_value=param["value"],
            parameter_type=param["type"],
            description=param["description"],
            overwrite=overwrite,
        )
        if success:
            success_count += 1

    # Résumé
    print(
        f"\n📊 Résumé: {success_count}/{len(parameters)} paramètres configurés"
    )

    if success_count == len(parameters):
        print("✅ Configuration SSM terminée avec succès!")
        print(f"\n🔗 Paramètres créés:")
        for param in parameters:
            print(f"   - {param['name']}")
        return True
    else:
        print("⚠️ Configuration partielle - Vérifiez les erreurs ci-dessus")
        return False


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description="Configure les paramètres SSM pour POSHub API"
    )

    parser.add_argument(
        "--stage",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Environnement de déploiement",
    )

    parser.add_argument(
        "--api-key", help="Clé API personnalisée (obligatoire pour prod)"
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Écrase les paramètres existants",
    )

    parser.add_argument(
        "--region", default="eu-north-1", help="Région AWS (défaut: eu-north-1)"
    )

    args = parser.parse_args()

    # Configurer la région AWS
    import os

    os.environ["AWS_DEFAULT_REGION"] = args.region

    print(f"🌍 Région AWS: {args.region}")

    # Exécuter la configuration
    success = setup_poshub_parameters(
        stage=args.stage, api_key=args.api_key, overwrite=args.overwrite
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

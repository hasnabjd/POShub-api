#!/usr/bin/env python3
"""
Script de déploiement manuel pour POSHub API.

Ce script :
1. Crée le layer et le publie sur AWS
2. Zippe le code de l'application
3. Crée ou met à jour la fonction Lambda
4. Teste l'invocation

Usage:
    python scripts/deploy_manual.py --stage dev
    python scripts/deploy_manual.py --stage prod --region eu-west-1
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


def run_aws_command(cmd: list, check: bool = True) -> dict:
    """
    Exécute une commande AWS CLI et retourne le résultat JSON.

    Args:
        cmd: Commande AWS CLI sous forme de liste
        check: Si True, lève une exception en cas d'erreur

    Returns:
        Dictionnaire avec le résultat JSON
    """
    try:
        print(f"🔧 AWS CLI: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=check
        )

        if result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"output": result.stdout.strip()}

        return {"success": True}

    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur AWS CLI: {e}")
        if e.stderr:
            print(f"🔴 Stderr: {e.stderr}")
        raise


def create_deployment_package() -> str:
    """
    Crée le package de déploiement (zip) pour la fonction Lambda.

    Returns:
        Chemin vers le fichier zip créé
    """
    print("📦 Création du package de déploiement...")

    # Créer un répertoire temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "package"
        package_dir.mkdir()

        # Copier le code source
        src_dir = Path("src")
        if src_dir.exists():
            shutil.copytree(src_dir, package_dir / "src")
            print("✅ Code source copié")
        else:
            raise FileNotFoundError("Répertoire 'src' non trouvé")

        # Créer le zip
        zip_path = "function.zip"
        if os.path.exists(zip_path):
            os.remove(zip_path)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(package_dir)
                    zf.write(file_path, arc_path)

        # Vérifier la taille
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"✅ Package créé: {zip_path} ({size_mb:.1f} MB)")

        return zip_path


def publish_layer(layer_name: str, region: str) -> str:
    """
    Publie le layer de dépendances sur AWS.

    Args:
        layer_name: Nom du layer
        region: Région AWS

    Returns:
        ARN du layer publié
    """
    print(f"📤 Publication du layer: {layer_name}")

    # Vérifier que layer.zip existe
    if not os.path.exists("layer.zip"):
        raise FileNotFoundError(
            "layer.zip non trouvé. Exécutez d'abord: "
            "python scripts/build_lambda_layer.py"
        )

    # Publier le layer
    cmd = [
        "aws",
        "lambda",
        "publish-layer-version",
        "--layer-name",
        layer_name,
        "--description",
        "Dépendances Python pour POSHub API",
        "--zip-file",
        "fileb://layer.zip",
        "--compatible-runtimes",
        "python3.11",
        "--region",
        region,
    ]

    result = run_aws_command(cmd)
    layer_arn = result["LayerVersionArn"]

    print(f"✅ Layer publié: {layer_arn}")
    return layer_arn


def create_execution_role(role_name: str, region: str) -> str:
    """
    Crée le rôle d'exécution pour la fonction Lambda.

    Args:
        role_name: Nom du rôle
        region: Région AWS

    Returns:
        ARN du rôle créé
    """
    print(f"🔐 Création du rôle d'exécution: {role_name}")

    # Document de confiance
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    # Créer le rôle
    try:
        cmd = [
            "aws",
            "iam",
            "create-role",
            "--role-name",
            role_name,
            "--assume-role-policy-document",
            json.dumps(trust_policy),
            "--region",
            region,
        ]
        result = run_aws_command(cmd)
        role_arn = result["Role"]["Arn"]
        print(f"✅ Rôle créé: {role_arn}")

    except subprocess.CalledProcessError as e:
        if "already exists" in str(e):
            # Rôle existe déjà, récupérer son ARN
            cmd = [
                "aws",
                "iam",
                "get-role",
                "--role-name",
                role_name,
                "--region",
                region,
            ]
            result = run_aws_command(cmd)
            role_arn = result["Role"]["Arn"]
            print(f"✅ Rôle existant utilisé: {role_arn}")
        else:
            raise

    # Attacher les politiques
    policies = [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    ]

    for policy_arn in policies:
        try:
            cmd = [
                "aws",
                "iam",
                "attach-role-policy",
                "--role-name",
                role_name,
                "--policy-arn",
                policy_arn,
                "--region",
                region,
            ]
            run_aws_command(cmd)
            print(f"✅ Politique attachée: {policy_arn}")
        except subprocess.CalledProcessError:
            print(f"⚠️ Politique déjà attachée: {policy_arn}")

    # Politique personnalisée pour SSM
    ssm_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["ssm:GetParameter", "ssm:GetParameters"],
                "Resource": "arn:aws:ssm:*:*:parameter/pos/*",
            }
        ],
    }

    try:
        cmd = [
            "aws",
            "iam",
            "put-role-policy",
            "--role-name",
            role_name,
            "--policy-name",
            "SSMParameterAccess",
            "--policy-document",
            json.dumps(ssm_policy),
            "--region",
            region,
        ]
        run_aws_command(cmd)
        print("✅ Politique SSM attachée")
    except subprocess.CalledProcessError:
        print("⚠️ Politique SSM déjà attachée")

    # Attendre que le rôle soit prêt
    print("⏳ Attente de la propagation du rôle...")
    time.sleep(10)

    return role_arn


def create_or_update_function(
    function_name: str, role_arn: str, layer_arn: str, stage: str, region: str
) -> str:
    """
    Crée ou met à jour la fonction Lambda.

    Args:
        function_name: Nom de la fonction
        role_arn: ARN du rôle d'exécution
        layer_arn: ARN du layer
        stage: Environnement
        region: Région AWS

    Returns:
        ARN de la fonction
    """
    print(f"🚀 Création/mise à jour de la fonction: {function_name}")

    # Variables d'environnement
    environment = {
        "Variables": {
            "STAGE": stage,
            "LOG_LEVEL": "INFO",
            "API_KEY_PARAM": f"/pos/{stage}/api-key",
            "AWS_REGION": region,
            "PYTHONPATH": "/var/task/src",
        }
    }

    # Vérifier si la fonction existe
    try:
        cmd = [
            "aws",
            "lambda",
            "get-function",
            "--function-name",
            function_name,
            "--region",
            region,
        ]
        result = run_aws_command(cmd)
        function_exists = True
        function_arn = result["Configuration"]["FunctionArn"]
        print(f"✅ Fonction existante trouvée: {function_arn}")

    except subprocess.CalledProcessError:
        function_exists = False
        print("🆕 Fonction non trouvée, création en cours...")

    if function_exists:
        # Mettre à jour le code
        cmd = [
            "aws",
            "lambda",
            "update-function-code",
            "--function-name",
            function_name,
            "--zip-file",
            "fileb://function.zip",
            "--region",
            region,
        ]
        run_aws_command(cmd)
        print("✅ Code de la fonction mis à jour")

        # Mettre à jour la configuration
        cmd = [
            "aws",
            "lambda",
            "update-function-configuration",
            "--function-name",
            function_name,
            "--layers",
            layer_arn,
            "--environment",
            json.dumps(environment),
            "--region",
            region,
        ]
        result = run_aws_command(cmd)
        function_arn = result["FunctionArn"]
        print("✅ Configuration de la fonction mise à jour")

    else:
        # Créer la fonction
        cmd = [
            "aws",
            "lambda",
            "create-function",
            "--function-name",
            function_name,
            "--runtime",
            "python3.11",
            "--role",
            role_arn,
            "--handler",
            "src.poshub_api.main.lambda_handler",
            "--zip-file",
            "fileb://function.zip",
            "--layers",
            layer_arn,
            "--environment",
            json.dumps(environment),
            "--timeout",
            "30",
            "--memory-size",
            "512",
            "--region",
            region,
        ]
        result = run_aws_command(cmd)
        function_arn = result["FunctionArn"]
        print(f"✅ Fonction créée: {function_arn}")

    return function_arn


def test_function(function_name: str, region: str) -> bool:
    """
    Teste l'invocation de la fonction Lambda.

    Args:
        function_name: Nom de la fonction
        region: Région AWS

    Returns:
        True si le test réussit, False sinon
    """
    print(f"🧪 Test de la fonction: {function_name}")

    # Payload de test (simulate API Gateway event)
    test_payload = {
        "httpMethod": "GET",
        "path": "/health",
        "headers": {},
        "queryStringParameters": {},
        "body": None,
    }

    # Écrire le payload dans un fichier temporaire
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(test_payload, f)
        payload_file = f.name

    try:
        # Invoquer la fonction
        cmd = [
            "aws",
            "lambda",
            "invoke",
            "--function-name",
            function_name,
            "--payload",
            f"fileb://{payload_file}",
            "--region",
            region,
            "response.json",
        ]

        run_aws_command(cmd)

        # Lire la réponse
        if os.path.exists("response.json"):
            with open("response.json", "r") as f:
                response = json.load(f)

            print("✅ Réponse de la fonction:")
            print(json.dumps(response, indent=2))

            # Nettoyer
            os.remove("response.json")

            return True
        else:
            print("❌ Pas de réponse de la fonction")
            return False

    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    finally:
        # Nettoyer le fichier payload
        if os.path.exists(payload_file):
            os.remove(payload_file)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Déploiement manuel de POSHub API sur AWS Lambda"
    )

    parser.add_argument(
        "--stage",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Environnement de déploiement",
    )

    parser.add_argument(
        "--region", default="eu-west-1", help="Région AWS (défaut: eu-west-1)"
    )

    parser.add_argument(
        "--skip-layer",
        action="store_true",
        help="Ignorer la création du layer",
    )

    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Ignorer le test de la fonction",
    )

    args = parser.parse_args()

    # Configuration
    stage = args.stage
    region = args.region
    function_name = f"poshub-api-{stage}"
    layer_name = f"poshub-dependencies-{stage}"
    role_name = f"poshub-execution-role-{stage}"

    print(f"🚀 Déploiement manuel de POSHub API")
    print(f"   Stage: {stage}")
    print(f"   Region: {region}")
    print(f"   Function: {function_name}")
    print(f"   Layer: {layer_name}")
    print(f"   Role: {role_name}")

    try:
        # Étape 1: Créer le package de déploiement
        zip_path = create_deployment_package()

        # Étape 2: Publier le layer (si demandé)
        if not args.skip_layer:
            layer_arn = publish_layer(layer_name, region)
        else:
            print("⏩ Création du layer ignorée")
            # Récupérer l'ARN du layer existant
            cmd = ["aws", "lambda", "list-layers", "--region", region]
            result = run_aws_command(cmd)
            layer_arn = None
            for layer in result.get("Layers", []):
                if layer["LayerName"] == layer_name:
                    layer_arn = layer["LatestMatchingVersion"][
                        "LayerVersionArn"
                    ]
                    break

            if not layer_arn:
                print("❌ Layer non trouvé, création requise")
                layer_arn = publish_layer(layer_name, region)

        # Étape 3: Créer le rôle d'exécution
        role_arn = create_execution_role(role_name, region)

        # Étape 4: Créer ou mettre à jour la fonction
        function_arn = create_or_update_function(
            function_name, role_arn, layer_arn, stage, region
        )

        # Étape 5: Tester la fonction (si demandé)
        if not args.skip_test:
            test_success = test_function(function_name, region)
            if not test_success:
                print("⚠️ Test de la fonction échoué")
        else:
            print("⏩ Test de la fonction ignoré")

        # Nettoyage
        if os.path.exists(zip_path):
            os.remove(zip_path)

        print(f"\n🎉 Déploiement terminé avec succès!")
        print(f"   Function ARN: {function_arn}")
        print(f"   Layer ARN: {layer_arn}")
        print(f"   Role ARN: {role_arn}")

    except Exception as e:
        print(f"\n❌ Erreur lors du déploiement: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

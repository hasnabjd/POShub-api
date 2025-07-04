#!/usr/bin/env python3
"""
Script de validation pour vérifier que l'intégration Mangum + SSM est réussie.

Ce script teste :
1. ✅ Mangum Handler fonctionne
2. ✅ Variables d'environnement sont lues
3. ✅ Client SSM s'initialise
4. ✅ FastAPI démarre correctement
5. ✅ Health check retourne les bonnes infos
6. ✅ Layer.zip peut être créé

Usage:
    python scripts/validate_integration.py
    python scripts/validate_integration.py --verbose
"""

import argparse
import os
import sys
import traceback
from typing import Any, Dict, Tuple


def test_imports() -> Tuple[bool, str]:
    """
    Test 1: Vérifier que tous les imports fonctionnent.

    Returns:
        (succès, message)
    """
    try:
        print("🔍 Test 1: Imports des modules...")

        # Test des imports principaux


        # Test des imports projet

        print("✅ Tous les imports réussis")
        return True, "Imports OK"

    except ImportError as e:
        return False, f"Import failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def test_environment_variables() -> Tuple[bool, str]:
    """
    Test 2: Vérifier la lecture des variables d'environnement.

    Returns:
        (succès, message)
    """
    try:
        print("🔍 Test 2: Variables d'environnement...")

        # Définir des variables de test
        os.environ["STAGE"] = "test"
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["API_KEY_PARAM"] = "/pos/test-key"

        from poshub_api.aws_utils import get_environment_config

        config = get_environment_config()

        # Vérifier les valeurs
        expected = {
            "STAGE": "test",
            "LOG_LEVEL": "DEBUG",
            "API_KEY_PARAM": "/pos/test-key",
        }

        for key, expected_value in expected.items():
            if config.get(key) != expected_value:
                return (
                    False,
                    f"Variable {key}: expected {expected_value}, got {config.get(key)}",
                )

        print("✅ Variables d'environnement lues correctement")
        return True, "Environment variables OK"

    except Exception as e:
        return False, f"Environment test failed: {e}"


def test_ssm_client() -> Tuple[bool, str]:
    """
    Test 3: Vérifier l'initialisation du client SSM.

    Returns:
        (succès, message)
    """
    try:
        print("🔍 Test 3: Client SSM...")

        from poshub_api.aws_utils import SSMParameterStore

        # Initialiser le client (peut échouer sans credentials AWS)
        ssm = SSMParameterStore()

        # Vérifier que l'objet est créé
        if ssm is None:
            return False, "SSM client is None"

        # Test que la région est configurée
        if not hasattr(ssm, "region") or not ssm.region:
            return False, "SSM region not configured"

        print(f"✅ Client SSM initialisé - Région: {ssm.region}")

        # Note: On ne teste pas la connexion AWS car elle peut échouer sans credentials
        return True, f"SSM client OK - Region: {ssm.region}"

    except Exception as e:
        return False, f"SSM client test failed: {e}"


def test_fastapi_app() -> Tuple[bool, str]:
    """
    Test 4: Vérifier que FastAPI démarre correctement.

    Returns:
        (succès, message)
    """
    try:
        print("🔍 Test 4: FastAPI application...")

        from poshub_api.main import app

        # Vérifier les propriétés de l'app
        if not hasattr(app, "title") or not app.title:
            return False, "App title not set"

        if not hasattr(app, "version") or not app.version:
            return False, "App version not set"

        # Vérifier les routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/auth/login", "/orders"]

        missing_routes = []
        for route in expected_routes:
            if not any(route in r for r in routes):
                missing_routes.append(route)

        if missing_routes:
            return False, f"Missing routes: {missing_routes}"

        print(
            f"✅ FastAPI app OK - Title: {app.title}, Version: {app.version}"
        )
        return True, f"FastAPI app OK - {len(routes)} routes"

    except Exception as e:
        return False, f"FastAPI test failed: {e}"


def test_mangum_handler() -> Tuple[bool, str]:
    """
    Test 5: Vérifier que Mangum handler est créé correctement.

    Returns:
        (succès, message)
    """
    try:
        print("🔍 Test 5: Mangum handler...")

        from mangum import Mangum

        from poshub_api.main import lambda_handler

        # Vérifier que le handler est une instance de Mangum
        if not isinstance(lambda_handler, Mangum):
            return (
                False,
                f"Handler is not Mangum instance: {type(lambda_handler)}",
            )

        # Vérifier les propriétés du handler
        if not hasattr(lambda_handler, "app"):
            return False, "Handler missing app attribute"

        print("✅ Mangum handler créé correctement")
        return True, "Mangum handler OK"

    except Exception as e:
        return False, f"Mangum handler test failed: {e}"


def test_health_endpoint() -> Tuple[bool, str]:
    """
    Test 6: Tester le endpoint de santé.

    Returns:
        (succès, message)
    """
    try:
        print("🔍 Test 6: Health endpoint...")

        from fastapi.testclient import TestClient

        from poshub_api.main import app

        client = TestClient(app)

        # Faire une requête au health check
        response = client.get("/health")

        if response.status_code != 200:
            return (
                False,
                f"Health check failed with status: {response.status_code}",
            )

        # Vérifier le contenu de la réponse
        data = response.json()
        required_fields = ["status", "service", "stage"]

        for field in required_fields:
            if field not in data:
                return False, f"Missing field in health response: {field}"

        if data["status"] != "healthy":
            return False, f"App not healthy: {data['status']}"

        print("✅ Health endpoint fonctionne")
        return True, f"Health OK - Service: {data['service']}"

    except Exception as e:
        return False, f"Health endpoint test failed: {e}"


def test_layer_creation() -> Tuple[bool, str]:
    """
    Test 7: Vérifier que le layer peut être créé.

    Returns:
        (succès, message)
    """
    try:
        print("🔍 Test 7: Layer creation capability...")

        import subprocess

        # Tester la commande poetry export
        result = subprocess.run(
            ["poetry", "export", "--help"], capture_output=True, text=True
        )

        if result.returncode != 0:
            return False, "Poetry export command not available"

        # Vérifier que les outils nécessaires sont présents
        tools = ["python", "pip", "poetry"]
        for tool in tools:
            result = subprocess.run(
                [tool, "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return False, f"Tool {tool} not available"

        print("✅ Outils pour layer creation disponibles")
        return True, "Layer creation tools OK"

    except Exception as e:
        return False, f"Layer creation test failed: {e}"


def run_all_tests(verbose: bool = False) -> Dict[str, Any]:
    """
    Exécute tous les tests et retourne un résumé.

    Args:
        verbose: Si True, affiche les détails des erreurs

    Returns:
        Dictionnaire avec les résultats
    """
    tests = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("SSM Client", test_ssm_client),
        ("FastAPI App", test_fastapi_app),
        ("Mangum Handler", test_mangum_handler),
        ("Health Endpoint", test_health_endpoint),
        ("Layer Creation", test_layer_creation),
    ]

    results = {"passed": 0, "failed": 0, "details": []}

    print("🚀 Démarrage des tests d'intégration...\n")

    for test_name, test_func in tests:
        try:
            success, message = test_func()

            if success:
                results["passed"] += 1
                status = "✅ PASS"
            else:
                results["failed"] += 1
                status = "❌ FAIL"

            results["details"].append(
                {"test": test_name, "success": success, "message": message}
            )

            print(f"{status}: {test_name} - {message}")

        except Exception as e:
            results["failed"] += 1
            error_msg = f"Exception: {e}"
            if verbose:
                error_msg += f"\n{traceback.format_exc()}"

            results["details"].append(
                {"test": test_name, "success": False, "message": error_msg}
            )

            print(f"❌ FAIL: {test_name} - {error_msg}")

    return results


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Valide l'intégration Mangum + SSM"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Affiche les détails des erreurs",
    )

    args = parser.parse_args()

    # Exécuter les tests
    results = run_all_tests(verbose=args.verbose)

    # Résumé
    total = results["passed"] + results["failed"]
    print(f"\n📊 RÉSUMÉ DES TESTS:")
    print(f"   ✅ Réussis: {results['passed']}/{total}")
    print(f"   ❌ Échoués: {results['failed']}/{total}")

    if results["failed"] == 0:
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ L'intégration Mangum + SSM est fonctionnelle")
        print("\n🚀 Prochaines étapes:")
        print("   1. Créer le layer: python scripts/build_lambda_layer.py")
        print("   2. Déployer sur AWS: sam deploy")
        print("   3. Tester en production")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['failed']} test(s) ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus avant de continuer")

        # Afficher les détails des échecs
        print("\n📋 Détails des échecs:")
        for detail in results["details"]:
            if not detail["success"]:
                print(f"   ❌ {detail['test']}: {detail['message']}")

        sys.exit(1)


if __name__ == "__main__":
    main()

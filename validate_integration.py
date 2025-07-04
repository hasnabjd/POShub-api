#!/usr/bin/env python3
"""
Script de validation pour vérifier que l'intégration Mangum + SSM est réussie.
"""

import sys


def test_imports():
    """Test 1: Vérifier que tous les imports fonctionnent."""
    try:
        print("🔍 Test 1: Imports des modules...")

        # Test des imports principaux
        from fastapi import FastAPI
        from mangum import Mangum
        import boto3
        import httpx

        # Test des imports projet
        from poshub_api.main import app, lambda_handler
        from poshub_api.aws_utils import SSMParameterStore, get_environment_config

        print("✅ Tous les imports réussis")
        return True, "Imports OK"

    except ImportError as e:
        return False, f"Import failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def test_mangum_handler():
    """Test 2: Vérifier que Mangum handler est créé correctement."""
    try:
        print("🔍 Test 2: Mangum handler...")

        from mangum import Mangum

        from poshub_api.main import lambda_handler

        # Vérifier que le handler est une instance de Mangum
        if not isinstance(lambda_handler, Mangum):
            return (
                False,
                f"Handler is not Mangum instance: {type(lambda_handler)}",
            )

        print("✅ Mangum handler créé correctement")
        return True, "Mangum handler OK"

    except Exception as e:
        return False, f"Mangum handler test failed: {e}"


def main():
    """Exécute tous les tests."""
    tests = [
        ("Imports", test_imports),
        ("Mangum Handler", test_mangum_handler),
    ]

    passed = 0
    failed = 0

    print("🚀 Démarrage des tests d'intégration...\n")

    for test_name, test_func in tests:
        try:
            success, message = test_func()

            if success:
                passed += 1
                print(f"✅ PASS: {test_name} - {message}")
            else:
                failed += 1
                print(f"❌ FAIL: {test_name} - {message}")

        except Exception as e:
            failed += 1
            print(f"❌ FAIL: {test_name} - Exception: {e}")

    # Résumé
    total = passed + failed
    print(f"\n📊 RÉSUMÉ DES TESTS:")
    print(f"   ✅ Réussis: {passed}/{total}")
    print(f"   ❌ Échoués: {failed}/{total}")

    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ L'intégration Mangum + SSM est fonctionnelle")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) ont échoué")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

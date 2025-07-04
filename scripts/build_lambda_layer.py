#!/usr/bin/env python3
"""
Script pour construire un Lambda Layer avec les dépendances Poetry.

Ce script :
1. Exporte les dépendances Poetry vers requirements.txt
2. Installe les dépendances dans un dossier layer/
3. Crée un fichier layer.zip prêt pour AWS Lambda

Usage:
    python scripts/build_lambda_layer.py
    python scripts/build_lambda_layer.py --production
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def run_command(cmd: str, cwd: str = None) -> bool:
    """
    Exécute une commande système et retourne True si succès.

    Args:
        cmd: Commande à exécuter
        cwd: Répertoire de travail (optionnel)

    Returns:
        True si succès, False sinon
    """
    try:
        print(f"🔧 Exécution: {cmd}")
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Succès")
            if result.stdout:
                print(f"📋 Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Erreur (code {result.returncode})")
            if result.stderr:
                print(f"🔴 Stderr: {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def export_poetry_dependencies(include_dev: bool = False) -> bool:
    """
    Exporte les dépendances Poetry vers requirements.txt.

    Args:
        include_dev: Si True, inclut les dépendances de développement

    Returns:
        True si succès, False sinon
    """
    print("📦 Export des dépendances Poetry...")

    # Commande d'export
    cmd = "poetry export -f requirements.txt --output requirements.txt"
    if not include_dev:
        cmd += " --without-hashes"

    success = run_command(cmd)

    if success and os.path.exists("requirements.txt"):
        # Vérifier le contenu
        with open("requirements.txt", "r") as f:
            content = f.read()
            lines = [line for line in content.split("\n") if line.strip()]
            print(f"✅ {len(lines)} dépendances exportées")

            # Montrer quelques dépendances
            print("📋 Principales dépendances:")
            for line in lines[:5]:
                pkg_name = (
                    line.split("==")[0]
                    if "==" in line
                    else line.split(">=")[0]
                )
                print(f"   - {pkg_name}")
            if len(lines) > 5:
                print(f"   ... et {len(lines) - 5} autres")

        return True
    else:
        print("❌ Échec de l'export des dépendances")
        return False


def create_layer_structure() -> bool:
    """
    Crée la structure de dossiers pour le Lambda Layer.

    Structure attendue par AWS Lambda:
    layer/
    └── python/
        └── lib/
            └── python3.11/
                └── site-packages/
                    └── [packages]

    Returns:
        True si succès, False sinon
    """
    print("🏗️ Création de la structure Layer...")

    # Supprimer l'ancien layer s'il existe
    if os.path.exists("layer"):
        shutil.rmtree("layer")
        print("🗑️ Ancien layer supprimé")

    # Créer la structure
    layer_path = Path("layer/python/lib/python3.11/site-packages")
    layer_path.mkdir(parents=True, exist_ok=True)

    print(f"✅ Structure créée: {layer_path}")
    return True


def install_dependencies_to_layer() -> bool:
    """
    Installe les dépendances dans le dossier layer.

    Returns:
        True si succès, False sinon
    """
    print("⬇️ Installation des dépendances dans le layer...")

    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt non trouvé")
        return False

    # Installer dans le layer
    target_dir = "layer/python/lib/python3.11/site-packages"
    cmd = f"pip install -r requirements.txt -t {target_dir} --no-deps"

    success = run_command(cmd)

    if success:
        # Vérifier l'installation
        installed_packages = os.listdir(target_dir)
        print(f"✅ {len(installed_packages)} packages installés dans le layer")

        # Calculer la taille
        total_size = sum(
            os.path.getsize(os.path.join(target_dir, f))
            for f in installed_packages
            if os.path.isfile(os.path.join(target_dir, f))
        )
        size_mb = total_size / (1024 * 1024)
        print(f"📊 Taille du layer: {size_mb:.1f} MB")

        return True
    else:
        print("❌ Échec de l'installation des dépendances")
        return False


def create_layer_zip() -> bool:
    """
    Crée le fichier layer.zip à partir du dossier layer.

    Returns:
        True si succès, False sinon
    """
    print("🗜️ Création du fichier layer.zip...")

    if not os.path.exists("layer"):
        print("❌ Dossier layer non trouvé")
        return False

    # Supprimer l'ancien zip
    if os.path.exists("layer.zip"):
        os.remove("layer.zip")
        print("🗑️ Ancien layer.zip supprimé")

    # Créer le zip
    with zipfile.ZipFile("layer.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk("layer"):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, "layer")
                zf.write(file_path, arc_path)

    # Vérifier le zip
    if os.path.exists("layer.zip"):
        size_mb = os.path.getsize("layer.zip") / (1024 * 1024)
        print(f"✅ layer.zip créé - Taille: {size_mb:.1f} MB")

        # Vérifier la limite AWS Lambda
        if size_mb > 250:
            print("⚠️ ATTENTION: Taille > 250MB (limite AWS Lambda)")
            return False
        elif size_mb > 50:
            print("⚠️ WARNING: Taille > 50MB (peut ralentir le déploiement)")

        return True
    else:
        print("❌ Échec de la création du zip")
        return False


def cleanup_temp_files():
    """Nettoie les fichiers temporaires."""
    print("🧹 Nettoyage des fichiers temporaires...")

    files_to_remove = ["requirements.txt"]
    dirs_to_remove = ["layer"]

    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ {file} supprimé")

    for dir in dirs_to_remove:
        if os.path.exists(dir):
            shutil.rmtree(dir)
            print(f"🗑️ {dir}/ supprimé")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Construit un Lambda Layer avec les dépendances Poetry"
    )

    parser.add_argument(
        "--production",
        action="store_true",
        help="Exclut les dépendances de développement",
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Garde les fichiers temporaires",
    )

    args = parser.parse_args()

    print("🚀 Construction du Lambda Layer...")
    print(f"📦 Mode: {'Production' if args.production else 'Développement'}")

    try:
        # Étape 1: Export des dépendances
        if not export_poetry_dependencies(include_dev=not args.production):
            sys.exit(1)

        # Étape 2: Création de la structure
        if not create_layer_structure():
            sys.exit(1)

        # Étape 3: Installation des dépendances
        if not install_dependencies_to_layer():
            sys.exit(1)

        # Étape 4: Création du zip
        if not create_layer_zip():
            sys.exit(1)

        print("\n🎉 Lambda Layer construit avec succès!")
        print("📁 Fichier créé: layer.zip")
        print("\n🚀 Prochaines étapes:")
        print("   1. Déployez le layer sur AWS Lambda")
        print("   2. Référencez le layer dans votre fonction Lambda")
        print("   3. Supprimez les dépendances de votre code fonction")

    except KeyboardInterrupt:
        print("\n⏸️ Construction interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)
    finally:
        # Nettoyage
        if not args.keep_temp:
            cleanup_temp_files()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script simple pour construire un Lambda Layer.
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path


def create_requirements_txt():
    """Crée requirements.txt à partir des dépendances connues."""
    print("📝 Création de requirements.txt...")
    
    dependencies = [
        "fastapi>=0.115.14,<0.116.0",
        "uvicorn[standard]>=0.35.0,<0.36.0", 
        "pydantic>=2.11.7,<3.0.0",
        "httpx>=0.28.1,<0.29.0",
        "tenacity>=9.1.2,<10.0.0",
        "structlog>=25.4.0,<26.0.0",
        "python-jose[cryptography]>=3.5.0,<4.0.0",
        "passlib[bcrypt]>=1.7.4,<2.0.0",
        "mangum>=0.19.0,<0.20.0",
        "boto3>=1.34.0,<2.0.0"
    ]
    
    with open("requirements.txt", "w") as f:
        for dep in dependencies:
            f.write(dep + "\n")
    
    print("✅ requirements.txt créé")
    return True


def create_layer():
    """Crée le layer Lambda."""
    print("🚀 Construction du Lambda Layer...")
    
    # 1. Créer requirements.txt
    create_requirements_txt()
    
    # 2. Supprimer ancien layer
    if os.path.exists("layer"):
        shutil.rmtree("layer")
        print("🗑️ Ancien layer supprimé")
    
    # 3. Créer structure
    layer_path = Path("layer/python")
    layer_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Structure créée: {layer_path}")
    
    # 4. Installer dépendances
    print("⬇️ Installation des dépendances...")
    cmd = f"pip install -r requirements.txt -t layer/python --no-cache-dir"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Dépendances installées")
    else:
        print(f"❌ Erreur installation: {result.stderr}")
        return False
    
    # 5. Créer ZIP
    print("🗜️ Création de layer.zip...")
    
    if os.path.exists("layer.zip"):
        os.remove("layer.zip")
    
    with zipfile.ZipFile("layer.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk("layer"):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, "layer")
                zf.write(file_path, arc_path)
    
    # 6. Vérifier taille
    size_mb = os.path.getsize("layer.zip") / (1024 * 1024)
    print(f"✅ layer.zip créé - Taille: {size_mb:.1f} MB")
    
    # 7. Nettoyer
    if os.path.exists("requirements.txt"):
        os.remove("requirements.txt")
    if os.path.exists("layer"):
        shutil.rmtree("layer")
    
    print("🎉 Layer construit avec succès!")
    return True


if __name__ == "__main__":
    create_layer() 
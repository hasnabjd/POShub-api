#!/usr/bin/env python3
"""
Script pour exporter la spécification OpenAPI de l'API POSHub.
"""

import json
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from poshub_api.main import app

def export_openapi_spec():
    """Exporte la spécification OpenAPI au format JSON."""
    
    # Créer le répertoire openapi s'il n'existe pas
    openapi_dir = Path(__file__).parent.parent / "openapi"
    openapi_dir.mkdir(exist_ok=True)
    
    # Chemin du fichier de sortie
    output_file = openapi_dir / "poshub-api.json"
    
    # Générer la spécification OpenAPI
    openapi_spec = app.openapi()
    
    # Écrire dans le fichier JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Spécification OpenAPI exportée vers: {output_file}")
    print(f"📊 Nombre d'endpoints: {len(openapi_spec.get('paths', {}))}")
    print(f"🔧 Nombre de schémas: {len(openapi_spec.get('components', {}).get('schemas', {}))}")
    
    return output_file

def export_openapi_yaml():
    """Exporte la spécification OpenAPI au format YAML."""
    try:
        import yaml
    except ImportError:
        print("❌ PyYAML non installé. Installer avec: poetry add pyyaml")
        return None
    
    # Créer le répertoire openapi s'il n'existe pas
    openapi_dir = Path(__file__).parent.parent / "openapi"
    openapi_dir.mkdir(exist_ok=True)
    
    # Chemin du fichier de sortie
    output_file = openapi_dir / "poshub-api.yaml"
    
    # Générer la spécification OpenAPI
    openapi_spec = app.openapi()
    
    # Écrire dans le fichier YAML
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(openapi_spec, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ Spécification OpenAPI YAML exportée vers: {output_file}")
    
    return output_file

if __name__ == "__main__":
    print("🚀 Export de la spécification OpenAPI...")
    
    try:
        # Exporter en JSON
        json_file = export_openapi_spec()
        
        # Exporter en YAML
        yaml_file = export_openapi_yaml()
        
        print("\n📋 Résumé:")
        print(f"   JSON: {json_file}")
        if yaml_file:
            print(f"   YAML: {yaml_file}")
        
        print("\n🌐 Pour visualiser la documentation:")
        print("   http://localhost:8000/docs")
        print("   http://localhost:8000/redoc")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")
        sys.exit(1) 
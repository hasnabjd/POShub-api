import os
import sys
from typing import Dict, Any

# Gestion des imports avec fallback pour les tests locaux
try:
    from fastapi import FastAPI
    from mangum import Mangum
    FASTAPI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: FastAPI/Mangum import failed: {e}")
    FASTAPI_AVAILABLE = False

# Configuration depuis les variables d'environnement
STAGE = os.getenv("STAGE", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_KEY_PARAM = os.getenv("API_KEY_PARAM", "/pos/api-key")

print(f"Démarrage de l'application - Stage: {STAGE}, Log Level: {LOG_LEVEL}")

if FASTAPI_AVAILABLE:
    # Version complète avec FastAPI
    app = FastAPI(
        title="POSHub API",
        version="1.0.0",
        description=f"API sécurisée pour système POS - Stage: {STAGE}",
    )

    @app.get("/health")
    async def health_check():
        """Health check endpoint simplifié pour les tests locaux."""
        return {
            "status": "healthy",
            "service": "poshub-api",
            "stage": STAGE,
            "log_level": LOG_LEVEL,
            "api_key_param": API_KEY_PARAM,
            "mode": "local-test",
            "imports_available": "fastapi,mangum"
        }

    @app.get("/")
    async def root():
        """Endpoint racine."""
        return {
            "message": "POSHub API - Running locally",
            "stage": STAGE,
            "endpoints": ["/health", "/"]
        }

    # Création du handler AWS Lambda
    lambda_handler = Mangum(
        app,
        lifespan="off",
        api_gateway_base_path=None,
    )

else:
    # Version fallback sans FastAPI
    def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handler fallback si FastAPI n'est pas disponible."""
        return {
            "statusCode": 200,
            "body": '{"error": "FastAPI not available", "stage": "' + STAGE + '"}',
            "headers": {"Content-Type": "application/json"}
        }

# Pour les tests locaux
if __name__ == "__main__":
    print("Mode test local")
    print(f"FASTAPI_AVAILABLE: {FASTAPI_AVAILABLE}")
    print(f"STAGE: {STAGE}")
    print(f"LOG_LEVEL: {LOG_LEVEL}") 
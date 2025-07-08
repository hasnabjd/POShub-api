"""
Health Handler pour POSHub REST API - Chapitre 4
Handler Lambda autonome pour le health check avec throttling
"""
import os
import sys
from datetime import datetime

# Ajouter le chemin src au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from fastapi import FastAPI
from mangum import Mangum

from poshub_api.logging_config import configure_logging, get_logger
from poshub_api.middleware import CorrelationIDMiddleware

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

STAGE = os.getenv("STAGE", "dev")

logger.info(f"Démarrage HealthApiFunction (Chapitre 4) - Stage: {STAGE}")

# Application FastAPI spécifique pour health check - Chapitre 4
app = FastAPI(
    title="POSHub Health API - Chapitre 4",
    version="1.0.0",
    description=f"API Health Check pour POSHub (Chapitre 4 - REST API) - Stage: {STAGE}",
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

@app.get("/health")
async def health_check():
    """
    Health check endpoint avec throttling spécialisé.
    Configuré pour 50 req/s, burst 10 dans API Gateway.
    """
    logger.info("Health check requested (Chapitre 4)")
    
    health_data = {
        "status": "healthy",
        "service": "poshub-health-api",
        "chapter": "4",
        "stage": STAGE,
        "timestamp": datetime.utcnow().isoformat(),
        "throttling": {
            "rate_limit": "50 req/s",
            "burst_limit": "10 req",
            "configured_in": "API Gateway MethodSettings"
        },
        "features": [
            "Custom throttling",
            "CORS support",
            "CloudWatch integration"
        ]
    }
    
    return health_data

@app.get("/")
async def root():
    """Endpoint racine pour le health service."""
    return {
        "message": "POSHub Health API - Chapitre 4",
        "endpoints": {
            "health": "/health"
        }
    }

# AWS Lambda Handler pour HealthApiFunction - Chapitre 4
lambda_handler = Mangum(
    app,
    lifespan="off",
    api_gateway_base_path=None,
) 
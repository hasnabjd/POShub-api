"""
Orders Handler pour POSHub REST API - Chapitre 4
Handler Lambda autonome pour la gestion des commandes
"""
import os
import sys

# Ajouter le chemin src au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from fastapi import FastAPI
from mangum import Mangum

from poshub_api.auth_router import router as auth_router
from poshub_api.aws_utils import initialize_aws_resources
from poshub_api.logging_config import configure_logging, get_logger
from poshub_api.middleware import CorrelationIDMiddleware
from poshub_api.orders.router import router as orders_router

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Configuration depuis les variables d'environnement
STAGE = os.getenv("STAGE", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logger.info(f"Démarrage OrderApiFunction (Chapitre 4) - Stage: {STAGE}")

# Application FastAPI spécifique pour les orders - Chapitre 4
app = FastAPI(
    title="POSHub Orders API - Chapitre 4",
    version="1.0.0",
    description=f"API Orders pour POSHub (Chapitre 4 - REST API) - Stage: {STAGE}",
    docs_url="/docs",  # Swagger UI disponible
    redoc_url="/redoc"  # ReDoc disponible
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

@app.on_event("startup")
async def startup():
    """Initialisation de l'application Orders."""
    logger.info("Starting Orders API (Chapitre 4)")
    
    # Initialiser les ressources AWS pour l'authentification
    try:
        aws_resources = initialize_aws_resources()
        app.state.aws = aws_resources
        app.state.config = aws_resources["config"]
        app.state.api_key = aws_resources["api_key"]
        logger.info("AWS resources initialized for Orders API")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation AWS: {e}")
        app.state.aws = None
        app.state.config = {"STAGE": STAGE, "LOG_LEVEL": LOG_LEVEL}
        app.state.api_key = None

@app.on_event("shutdown")
async def shutdown():
    """Nettoyage des ressources."""
    logger.info("Shutting down Orders API (Chapitre 4)")

# Include routers pour l'authentification et les orders
app.include_router(auth_router)
app.include_router(orders_router)

@app.get("/")
async def root():
    """Endpoint racine pour vérifier que l'API fonctionne."""
    return {
        "message": "POSHub Orders API - Chapitre 4",
        "stage": STAGE,
        "endpoints": {
            "orders": "/orders",
            "auth": "/token",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_orders():
    """Health check spécifique aux orders."""
    logger.info("Orders API health check requested")
    return {
        "status": "healthy",
        "service": "poshub-orders-api",
        "chapter": "4",
        "stage": STAGE,
        "features": [
            "JWT Authorization",
            "API Key validation", 
            "CORS support",
            "Throttling"
        ]
    }

# AWS Lambda Handler pour OrderApiFunction - Chapitre 4
lambda_handler = Mangum(
    app,
    lifespan="off",
    api_gateway_base_path=None,
) 
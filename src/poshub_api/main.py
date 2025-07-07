import os

import httpx
from fastapi import FastAPI
from mangum import Mangum

from poshub_api.auth_router import router as auth_router
from poshub_api.aws_utils import initialize_aws_resources
from poshub_api.demo.router import router as demo_router
from poshub_api.logging_config import configure_logging, get_logger
from poshub_api.middleware import CorrelationIDMiddleware
from poshub_api.orders.router import router as orders_router

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Configuration depuis les variables d'environnement
STAGE = os.getenv("STAGE", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_KEY_PARAM = os.getenv("API_KEY_PARAM", "/pos/api-key")

logger.info(
    f"Démarrage de l'application - Stage: {STAGE}, Log Level: {LOG_LEVEL}"
)

app = FastAPI(
    title="POSHub API",
    version="1.0.0",
    description=f"API sécurisée pour système POS avec authentification JWT "
    f"et gestion des scopes - Stage: {STAGE}",
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)


@app.on_event("startup")
async def startup():
    logger.info("Starting POSHub API")

    # Initialiser le client HTTP
    app.state.http = httpx.AsyncClient(timeout=10.0)
    logger.info("HTTP client initialized")

    # Initialiser les ressources AWS (SSM, configuration)
    try:
        aws_resources = initialize_aws_resources()
        app.state.aws = aws_resources
        app.state.config = aws_resources["config"]
        app.state.api_key = aws_resources["api_key"]
        logger.info(" AWS resources initialized")

        # Log de l'API key pour la démo (⚠️ JAMAIS en production !)
        if app.state.api_key:
            logger.warning(f"DEMO - API Key chargée: {app.state.api_key}")
        else:
            logger.warning("API Key non disponible")

    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation AWS: {e}")
        # Continuer sans AWS resources en mode dégradé
        app.state.aws = None
        app.state.config = {
            "STAGE": STAGE,
            "LOG_LEVEL": LOG_LEVEL,
            "API_KEY_PARAM": API_KEY_PARAM,
        }
        app.state.api_key = None

    logger.info(f" POSHub API démarrée - Stage: {STAGE}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down POSHub API")

    # Fermer le client HTTP
    await app.state.http.aclose()
    logger.info("HTTP client closed")

    # Nettoyer les ressources AWS si nécessaire
    if hasattr(app.state, "aws") and app.state.aws:
        logger.info("AWS resources cleaned up")

    logger.info("POSHub API fermée proprement")


# Include routers
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(demo_router)


@app.get("/health")
async def health_check():
    """Health check endpoint with correlation ID logging and environment info."""
    logger.info("Health check requested")

    # Récupérer la configuration depuis l'état de l'application
    config = getattr(app.state, "config", {})
    api_key_available = getattr(app.state, "api_key", None) is not None

    health_data = {
        "status": "healthy",
        "service": "poshub-api",
        "stage": config.get("STAGE", "unknown"),
        "log_level": config.get("LOG_LEVEL", "unknown"),
        "api_key_param": config.get("API_KEY_PARAM", "unknown"),
        "api_key_loaded": api_key_available,
        "aws_resources": getattr(app.state, "aws", None) is not None,
        "timestamp": None,  # FastAPI ajoutera automatiquement
    }

    # Log des informations de santé (sans secrets)
    logger.info(
        f"Health check - Stage: {health_data['stage']}, "
        f"AWS Resources: {health_data['aws_resources']}, "
        f"API Key: {api_key_available}"
    )

    return health_data


# ========================================================================
# AWS Lambda Handler avec Mangum
# ========================================================================

# Création du handler AWS Lambda
# Mangum est un adaptateur ASGI pour AWS Lambda qui permet d'exécuter
# des applications FastAPI dans un environnement serverless
lambda_handler = Mangum(
    app,
    lifespan="off",  # Désactive la gestion du lifespan
    api_gateway_base_path=None,  # Chemin de base pour API Gateway
    text_mime_types=[
        "application/json",
        "application/javascript",
        "application/xml",
        "application/vnd.api+json",
    ],
)

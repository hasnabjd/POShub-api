import os
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

logger.info(f"Démarrage de OrderApiFunction - Stage: {STAGE}")

# Application FastAPI spécifique pour les orders
app = FastAPI(
    title="POSHub Orders API",
    version="1.0.0",
    description=f"API Orders pour POSHub - Stage: {STAGE}",
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

@app.on_event("startup")
async def startup():
    logger.info("Starting Orders API")
    
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

# Include only auth and orders routers
app.include_router(auth_router)
app.include_router(orders_router)

@app.get("/health")
async def health_check():
    """Health check endpoint for Orders API."""
    logger.info("Orders API health check requested")
    return {
        "status": "healthy",
        "service": "poshub-orders-api",
        "stage": STAGE,
    }

# AWS Lambda Handler pour OrderApiFunction
lambda_handler = Mangum(
    app,
    lifespan="off",
    api_gateway_base_path=None,
) 
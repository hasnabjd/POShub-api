import os
import json
from datetime import datetime
from mangum import Mangum
from fastapi import FastAPI

from poshub_api.logging_config import configure_logging, get_logger
from poshub_api.middleware import CorrelationIDMiddleware

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

STAGE = os.getenv("STAGE", "dev")

logger.info(f"Démarrage de HealthApiFunction - Stage: {STAGE}")

# Application FastAPI spécifique pour health check
app = FastAPI(
    title="POSHub Health API",
    version="1.0.0",
    description=f"API Health Check pour POSHub - Stage: {STAGE}",
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

@app.get("/health")
async def health_check():
    """Health check endpoint avec throttling."""
    logger.info("Health check requested")
    
    health_data = {
        "status": "healthy",
        "service": "poshub-health-api",
        "stage": STAGE,
        "timestamp": datetime.utcnow().isoformat(),
        "throttling": "50 req/s, burst 10"
    }
    
    return health_data

# AWS Lambda Handler pour HealthApiFunction
lambda_handler = Mangum(
    app,
    lifespan="off",
    api_gateway_base_path=None,
) 
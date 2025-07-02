from fastapi import FastAPI
import httpx
from poshub_api.orders.router import router as orders_router
from poshub_api.demo.router import router as demo_router
from poshub_api.auth_router import router as auth_router
from poshub_api.logging_config import configure_logging, get_logger
from poshub_api.middleware import CorrelationIDMiddleware

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="POSHub API", 
    version="1.0.0",
    description="API sécurisée pour système POS avec authentification JWT et gestion des scopes"
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

@app.on_event("startup")
async def startup():
    logger.info("Starting POSHub API")
    app.state.http = httpx.AsyncClient(timeout=10.0)
    logger.info("HTTP client initialized")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down POSHub API")
    await app.state.http.aclose()
    logger.info("HTTP client closed")

# Include routers
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(demo_router)

@app.get("/health")
async def health_check():
    """Health check endpoint with correlation ID logging."""
    logger.info("Health check requested")
    return {"status": "healthy", "service": "poshub-api"} 
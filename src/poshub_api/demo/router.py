from fastapi import APIRouter, Depends, HTTPException
from poshub_api.http_client import get_http
from poshub_api.logging_config import get_logger
from poshub_api.auth import require_demo_read, User
from .service import fetch_mockbin

router = APIRouter(prefix="/demo", tags=["demo"])
logger = get_logger(__name__)

@router.get("/mockbin")
async def call_mockbin(
    http_client = Depends(get_http),
    current_user: User = Depends(require_demo_read)
):
    """
    Route de démonstration qui appelle l'API externe Mockbin via safe_get.
    Requiert le scope: demo:read
    """
    logger.info("Mockbin request started", username=current_user.username)
    try:
        result = await fetch_mockbin(http_client)
        logger.info("Mockbin request completed successfully", username=current_user.username)
        return result
    except Exception as e:
        logger.error("Mockbin request failed", username=current_user.username, error=str(e))
        raise HTTPException(status_code=502, detail="External API error") 
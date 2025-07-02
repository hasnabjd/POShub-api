from fastapi import APIRouter, Depends, HTTPException
from poshub_api.http_client import get_http
from .service import fetch_mockbin

router = APIRouter()

@router.get("/mockbin")
async def call_mockbin(http_client = Depends(get_http)):
    """
    Route de démonstration qui appelle l'API externe Mockbin via safe_get.
    """
    try:
        return await fetch_mockbin(http_client)
    except Exception:
        raise HTTPException(status_code=502, detail="External API error") 
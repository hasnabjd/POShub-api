import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .logging_config import get_logger

logger = get_logger(__name__)


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
async def safe_get(client: httpx.AsyncClient, url: str):
    """
    Effectue un GET HTTP robuste avec retry, timeout et logs.
    """
    try:
        logger.info("HTTP request", url=url)
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        logger.info("HTTP success", url=url, status=response.status_code)
        return response.json()
    except httpx.HTTPError as e:
        logger.error("HTTP error", url=url, error=str(e))
        raise

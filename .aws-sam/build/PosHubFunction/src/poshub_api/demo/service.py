from poshub_api.http_utils import safe_get

MOCKBIN_URL = "https://mockbin.org/request"


async def fetch_mockbin(client):
    """
    Appelle l'API externe Mockbin et retourne le JSON.
    """
    return await safe_get(client, MOCKBIN_URL)

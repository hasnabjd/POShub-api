import httpx
from fastapi import Request

def get_http(request: Request) -> httpx.AsyncClient:
    """
    Fournit le client HTTP unique stocké dans app.state.http
    Utilisé avec Depends dans les routes/services
    """
    return request.app.state.http 
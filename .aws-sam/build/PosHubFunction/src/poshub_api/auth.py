from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .logging_config import get_logger

logger = get_logger(__name__)

# Configuration JWT
SECRET_KEY = "your-secret-key-change-in-production"  # À changer en production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Scopes disponibles
SCOPES = {
    "orders:read": "Lecture des commandes",
    "orders:write": "Création et modification des commandes",
    "demo:read": "Accès aux routes de démonstration",
}


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    scopes: List[str] = []


# Security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token JWT d'accès."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Vérifie et décode un token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        scopes: List[str] = payload.get("scopes", [])

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(username=username, scopes=scopes)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Dépendance pour obtenir l'utilisateur courant."""
    token = credentials.credentials
    token_data = verify_token(token)

    logger.info(
        "User authenticated",
        username=token_data.username,
        scopes=token_data.scopes,
    )

    return User(username=token_data.username, scopes=token_data.scopes)


def require_scope(required_scope: str):
    """Décorateur pour vérifier qu'un scope est requis."""

    def scope_checker(current_user: User = Depends(get_current_user)) -> User:
        if required_scope not in current_user.scopes:
            logger.warning(
                "Access denied - missing scope",
                username=current_user.username,
                required_scope=required_scope,
                user_scopes=current_user.scopes,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required scope: "
                f"{required_scope}",
            )

        logger.info(
            "Access granted",
            username=current_user.username,
            scope=required_scope,
        )
        return current_user

    return scope_checker


# Dépendances pré-définies pour les scopes courants
require_orders_read = require_scope("orders:read")
require_orders_write = require_scope("orders:write")
require_demo_read = require_scope("demo:read")

# Utilisateurs de test (en production, utiliser une base de données)
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "scopes": ["orders:read", "orders:write", "demo:read"],
    },
    "user": {
        "username": "user",
        "password": "user123",
        "scopes": ["orders:read"],
    },
    "demo": {
        "username": "demo",
        "password": "demo123",
        "scopes": ["demo:read"],
    },
}


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authentifie un utilisateur avec username/password."""
    user_data = TEST_USERS.get(username)
    if not user_data or user_data["password"] != password:
        return None

    return User(username=user_data["username"], scopes=user_data["scopes"])

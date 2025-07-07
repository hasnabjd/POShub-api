from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from .logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


class Token(BaseModel):
    access_token: str
    token_type: str
    scopes: list[str]


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Endpoint de connexion pour obtenir un token JWT."""
    logger.info("Login attempt", username=form_data.username)

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(
            "Login failed - invalid credentials", username=form_data.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=access_token_expires,
    )

    logger.info("Login successful", username=user.username, scopes=user.scopes)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "scopes": user.scopes,
    }


@router.post("/login-json", response_model=Token)
async def login_with_json(login_data: LoginRequest):
    """Endpoint de connexion alternatif avec JSON."""
    logger.info("JSON login attempt", username=login_data.username)

    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        logger.warning(
            "JSON login failed - invalid credentials",
            username=login_data.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes},
        expires_delta=access_token_expires,
    )

    logger.info(
        "JSON login successful", username=user.username, scopes=user.scopes
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "scopes": user.scopes,
    }


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Endpoint pour obtenir les informations de l'utilisateur courant."""
    logger.info("User profile requested", username=current_user.username)
    return current_user


@router.get("/scopes")
async def get_available_scopes():
    """Endpoint pour obtenir la liste des scopes disponibles."""
    from .auth import SCOPES

    return {"scopes": SCOPES}

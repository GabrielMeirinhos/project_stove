"""Utilitários de autenticação JWT.

Expõe:
- ``hash_password`` / ``verify_password`` — bcrypt
- ``create_access_token`` — gera JWT assinado com SECRET_KEY
- ``get_current_user`` — dependency FastAPI que valida o Bearer token
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app import config

ALGORITHM = "HS256"

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_PREFIX}/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": username, "exp": expire},
        config.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def get_current_user(token: Annotated[str, Depends(_oauth2_scheme)]) -> dict:
    """Dependency que extrai e valida o JWT. Levanta 401 se inválido."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise exc
    except JWTError:
        raise exc
    return {"username": username}

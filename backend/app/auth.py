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


def create_access_token(username: str, role: str, user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": username, "role": role, "user_id": user_id, "exp": expire},
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
    return {
        "username": username,
        "role": payload.get("role", "user"),
        "user_id": payload.get("user_id"),
    }


def require_superadmin(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    """Dependency que garante acesso apenas para superadmin."""
    if current_user["role"] != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a superadmin",
        )
    return current_user


def get_user_device_ids(user_id: str) -> set[str]:
    """Retorna os IDs de devices acessíveis a um usuário comum (via suas plantas)."""
    from app.database import device_repo, plant_repo
    plant_ids = {
        str(p["id"]) for p in plant_repo.list(
            where=lambda r: str(r.get("user_id", "")) == user_id
        )
    }
    return {
        str(d["id"]) for d in device_repo.list(
            where=lambda r: str(r["plant_id"]) in plant_ids
        )
    }


def get_user_image_ids(user_id: str) -> set[str]:
    """Retorna os IDs de imagens acessíveis a um usuário (via seus devices)."""
    from app.database import plant_image_repo
    device_ids = get_user_device_ids(user_id)
    return {
        str(img["id"]) for img in plant_image_repo.list(
            where=lambda r: str(r["device_id"]) in device_ids
        )
    }

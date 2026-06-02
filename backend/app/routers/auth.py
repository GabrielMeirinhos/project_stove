"""Endpoints de autenticação."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.auth import create_access_token, verify_password
from app.db.connection import get_pool

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _get_user(username: str) -> dict | None:
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, hashed_password, is_active, role FROM users WHERE username = %s",
            (username,),
        )
        return cur.fetchone()


@router.post("/login", response_model=TokenResponse, summary="Obtém token JWT")
def login(form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    user = _get_user(form.username)
    if not user or not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )
    return TokenResponse(
        access_token=create_access_token(
            username=form.username,
            role=user["role"],
            user_id=str(user["id"]),
        )
    )

"""Endpoints de gerenciamento de usuários (acesso restrito a superadmin)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import hash_password, require_superadmin
from app.database import user_repo
from app.schemas.user import User, UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Cria novo usuário (superadmin only)",
)
def create(
    data: UserCreate,
    _: Annotated[dict, Depends(require_superadmin)],
) -> User:
    existing = user_repo.find_one(lambda r: r["username"] == data.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username já em uso")
    record = {
        "id": uuid4(),
        "username": data.username,
        "hashed_password": hash_password(data.password),
        "is_active": True,
        "role": data.role,
        "created_at": datetime.now(timezone.utc),
    }
    user_repo.add(record)
    return User(**record)


@router.get(
    "",
    response_model=List[User],
    summary="Lista usuários (superadmin only)",
)
def list_all(
    _: Annotated[dict, Depends(require_superadmin)],
) -> List[User]:
    return [User(**r) for r in user_repo.list(order_by="created_at")]

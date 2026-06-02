"""Schemas da entidade ``users``."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field("user", pattern="^(user|superadmin)$")


class User(BaseModel):
    id: UUID
    username: str
    is_active: bool
    role: str
    created_at: datetime

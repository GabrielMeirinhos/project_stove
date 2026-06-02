from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserPublic


class InviteCreateRequest(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.user


class InviteCreateResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    invite_url: str
    expires_at: datetime


class InviteAcceptRequest(BaseModel):
    token: str
    password: str = Field(min_length=6)


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetRequestResponse(BaseModel):
    reset_url: str
    expires_at: datetime


class PasswordResetConfirmRequest(BaseModel):
    token: str
    password: str = Field(min_length=6)


class AdminOverview(BaseModel):
    users_total: int
    admins_total: int
    active_users_total: int
    pending_invites_total: int
    pending_reset_tokens_total: int


class MessageResponse(BaseModel):
    message: str

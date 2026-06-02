from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .db import connection
from .db import init_db
from .schemas import (
    AdminOverview,
    AuthResponse,
    InviteAcceptRequest,
    InviteCreateRequest,
    InviteCreateResponse,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    UserPublic,
    UserRole,
)
from .security import create_signed_token, decode_signed_token, now_utc, verify_password
from .seed import seed_default_users
from .settings import (
    API_PREFIX,
    APP_BASE_URL,
    APP_NAME,
    FRONTEND_ORIGINS,
    INVITE_TTL_HOURS,
    RESET_TTL_HOURS,
    TOKEN_TTL_MINUTES,
)
from . import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_default_users()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_public_user(user: dict) -> UserPublic:
    return UserPublic.model_validate(user)


def _auth_payload(user: dict) -> dict:
    return {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "full_name": user["full_name"],
    }


def current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_signed_token(token)
    user = store.get_user_by_id(payload.get("sub", ""))
    if user is None or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido")
    return user


def admin_user(user: Annotated[dict, Depends(current_user)]) -> dict:
    if user["role"] != UserRole.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao admin")
    return user


@app.get("/")
def health() -> dict:
    return {"service": APP_NAME, "status": "ok"}


@app.post(f"{API_PREFIX}/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user = store.get_user_by_email(payload.email)
    if user is None or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    store.update_last_login(user["id"])
    refreshed_user = store.get_user_by_id(user["id"])
    access_token = create_signed_token(
        _auth_payload(refreshed_user),
        expires_delta=timedelta(minutes=TOKEN_TTL_MINUTES),
    )
    return AuthResponse(
        access_token=access_token,
        expires_in_minutes=TOKEN_TTL_MINUTES,
        user=_to_public_user(refreshed_user),
    )


@app.get(f"{API_PREFIX}/auth/me", response_model=UserPublic)
def me(user: Annotated[dict, Depends(current_user)]) -> UserPublic:
    return _to_public_user(user)


@app.post(f"{API_PREFIX}/auth/logout", response_model=MessageResponse)
def logout() -> MessageResponse:
    return MessageResponse(message="Logout realizado com sucesso")


@app.post(f"{API_PREFIX}/auth/invites", response_model=InviteCreateResponse)
def create_invite(payload: InviteCreateRequest, user: Annotated[dict, Depends(admin_user)]) -> InviteCreateResponse:
    expires_at = now_utc() + timedelta(hours=INVITE_TTL_HOURS)
    invite = store.create_invite(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        created_by=user["id"],
        expires_at=expires_at,
    )
    invite_url = f"{APP_BASE_URL}/accept-invite?token={invite['token']}"
    return InviteCreateResponse(
        id=invite["id"],
        email=invite["email"],
        full_name=invite["full_name"],
        role=invite["role"],
        invite_url=invite_url,
        expires_at=invite["expires_at"],
    )


@app.post(f"{API_PREFIX}/auth/invites/accept", response_model=AuthResponse)
def accept_invite(payload: InviteAcceptRequest) -> AuthResponse:
    try:
        user = store.accept_invite(payload.token, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    access_token = create_signed_token(
        _auth_payload(user),
        expires_delta=timedelta(minutes=TOKEN_TTL_MINUTES),
    )
    return AuthResponse(
        access_token=access_token,
        expires_in_minutes=TOKEN_TTL_MINUTES,
        user=_to_public_user(user),
    )


@app.post(f"{API_PREFIX}/auth/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(payload: PasswordResetRequest) -> PasswordResetRequestResponse:
    user = store.get_user_by_email(payload.email)
    expires_at = now_utc() + timedelta(hours=RESET_TTL_HOURS)
    if user is not None:
        reset = store.create_password_reset_token(user["id"], expires_at)
        reset_url = f"{APP_BASE_URL}/reset-password?token={reset['token']}"
        return PasswordResetRequestResponse(reset_url=reset_url, expires_at=reset["expires_at"])

    return PasswordResetRequestResponse(
        reset_url=f"{APP_BASE_URL}/reset-password?notice=sent",
        expires_at=expires_at,
    )


@app.post(f"{API_PREFIX}/auth/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(payload: PasswordResetConfirmRequest) -> MessageResponse:
    reset = store.get_reset_token(payload.token)
    if reset is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")
    if reset.get("used_at") is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token já utilizado")
    if reset.get("expires_at") <= now_utc().isoformat():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado")

    store.update_user_password(reset["user_id"], payload.password)
    store.mark_reset_token_used(reset["id"])
    return MessageResponse(message="Senha atualizada com sucesso")


@app.get(f"{API_PREFIX}/admin/users", response_model=list[UserPublic])
def admin_users(_: Annotated[dict, Depends(admin_user)]) -> list[UserPublic]:
    return [UserPublic.model_validate(user) for user in store.list_users()]


@app.get(f"{API_PREFIX}/admin/overview", response_model=AdminOverview)
def admin_overview(_: Annotated[dict, Depends(admin_user)]) -> AdminOverview:
    with connection() as conn:
        invites = conn.execute(
            "SELECT COUNT(*) AS total FROM auth_invites WHERE accepted_at IS NULL"
        ).fetchone()
        resets = conn.execute(
            "SELECT COUNT(*) AS total FROM password_reset_tokens WHERE used_at IS NULL"
        ).fetchone()

    return AdminOverview(
        users_total=store.count_users(),
        admins_total=store.count_admins(),
        active_users_total=store.count_active_users(),
        pending_invites_total=int(invites["total"]),
        pending_reset_tokens_total=int(resets["total"]),
    )

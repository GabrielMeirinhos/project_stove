from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .db import connection
from .security import hash_password, now_utc, sha256_hex
from .schemas import UserRole


def _row_to_dict(row) -> Dict[str, Any]:
    return dict(row) if row is not None else {}


def _user_row_to_public(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "full_name": row["full_name"],
        "email": row["email"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_login_at": row["last_login_at"],
    }


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(email) = lower(?)",
            (email,),
        ).fetchone()
        return _row_to_dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    with connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_dict(row) if row else None


def list_users() -> List[Dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at ASC").fetchall()
        return [_user_row_to_public(row) for row in rows]


def count_users() -> int:
    with connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(row["total"])


def count_admins() -> int:
    with connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM users WHERE role = ?",
            (UserRole.admin.value,),
        ).fetchone()
        return int(row["total"])


def count_active_users() -> int:
    with connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM users WHERE is_active = 1").fetchone()
        return int(row["total"])


def create_user(full_name: str, email: str, password: str, role: UserRole) -> Dict[str, Any]:
    user_id = str(uuid.uuid4())
    timestamp = now_utc().isoformat()
    password_hash = hash_password(password)

    with connection() as conn:
        conn.execute(
            """
            INSERT INTO users (id, full_name, email, password_hash, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (user_id, full_name, email.lower(), password_hash, role.value, timestamp, timestamp),
        )

    return get_user_by_id(user_id)  # type: ignore[return-value]


def update_last_login(user_id: str) -> None:
    timestamp = now_utc().isoformat()
    with connection() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
            (timestamp, timestamp, user_id),
        )


def update_user_email(user_id: str, email: str) -> None:
    timestamp = now_utc().isoformat()
    with connection() as conn:
        conn.execute(
            "UPDATE users SET email = ?, updated_at = ? WHERE id = ?",
            (email.lower(), timestamp, user_id),
        )


def update_user_password(user_id: str, password: str) -> None:
    timestamp = now_utc().isoformat()
    password_hash = hash_password(password)
    with connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (password_hash, timestamp, user_id),
        )


def create_invite(
    email: str,
    full_name: str,
    role: UserRole,
    created_by: Optional[str],
    expires_at: datetime,
) -> Dict[str, Any]:
    invite_id = str(uuid.uuid4())
    token = uuid.uuid4().hex + uuid.uuid4().hex
    token_hash = sha256_hex(token)
    timestamp = now_utc().isoformat()

    with connection() as conn:
        conn.execute(
            """
            INSERT INTO auth_invites
            (id, email, full_name, role, token_hash, created_by, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invite_id,
                email.lower(),
                full_name,
                role.value,
                token_hash,
                created_by,
                expires_at.isoformat(),
                timestamp,
            ),
        )

    return {
        "id": invite_id,
        "email": email.lower(),
        "full_name": full_name,
        "role": role.value,
        "token": token,
        "expires_at": expires_at,
    }


def get_invite_by_token(token: str) -> Optional[Dict[str, Any]]:
    token_hash = sha256_hex(token)
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM auth_invites WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        return _row_to_dict(row) if row else None


def accept_invite(token: str, password: str) -> Dict[str, Any]:
    invite = get_invite_by_token(token)
    if invite is None:
        raise ValueError("Convite inválido")
    if invite["accepted_at"] is not None:
        raise ValueError("Convite já utilizado")
    expires_at = datetime.fromisoformat(invite["expires_at"])
    if expires_at <= now_utc():
        raise ValueError("Convite expirado")
    if get_user_by_email(invite["email"]) is not None:
        raise ValueError("Usuário já existe")

    user = create_user(
        full_name=invite["full_name"] or invite["email"],
        email=invite["email"],
        password=password,
        role=UserRole(invite["role"]),
    )

    timestamp = now_utc().isoformat()
    with connection() as conn:
        conn.execute(
            "UPDATE auth_invites SET accepted_at = ? WHERE id = ?",
            (timestamp, invite["id"]),
        )
    return user


def create_password_reset_token(user_id: str, expires_at: datetime) -> Dict[str, Any]:
    reset_id = str(uuid.uuid4())
    token = uuid.uuid4().hex + uuid.uuid4().hex
    token_hash = sha256_hex(token)
    timestamp = now_utc().isoformat()
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO password_reset_tokens
            (id, user_id, token_hash, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (reset_id, user_id, token_hash, expires_at.isoformat(), timestamp),
        )
    return {
        "id": reset_id,
        "user_id": user_id,
        "token": token,
        "expires_at": expires_at,
    }


def get_reset_token(token: str) -> Optional[Dict[str, Any]]:
    token_hash = sha256_hex(token)
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM password_reset_tokens WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        return _row_to_dict(row) if row else None


def mark_reset_token_used(reset_id: str) -> None:
    timestamp = now_utc().isoformat()
    with connection() as conn:
        conn.execute(
            "UPDATE password_reset_tokens SET used_at = ? WHERE id = ?",
            (timestamp, reset_id),
        )

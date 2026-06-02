from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Dict

from fastapi import HTTPException, status

from .settings import SECRET_KEY

PBKDF2_ITERATIONS = 210_000
PBKDF2_ALGORITHM = "sha256"
PASSWORD_SALT_BYTES = 16
SIGNING_ALGORITHM = "HS256"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def iso_now() -> str:
    return now_utc().isoformat()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return "pbkdf2_sha256${iterations}${salt}${hash}".format(
        iterations=PBKDF2_ITERATIONS,
        salt=_b64url_encode(salt),
        hash=_b64url_encode(derived),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        prefix, iterations_str, salt_b64, hash_b64 = stored_hash.split("$")
    except ValueError:
        return False
    if prefix != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_str)
        salt = _b64url_decode(salt_b64)
        expected = _b64url_decode(hash_b64)
    except Exception:
        return False

    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(derived, expected)


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_signed_token(payload: Dict[str, Any], expires_delta: timedelta) -> str:
    header = {"alg": SIGNING_ALGORITHM, "typ": "JWT"}
    issued_at = now_utc()
    data = dict(payload)
    data["iat"] = int(issued_at.timestamp())
    data["exp"] = int((issued_at + expires_delta).timestamp())

    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _b64url_encode(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def decode_signed_token(token: str) -> Dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    try:
        provided_signature = _b64url_decode(signature_segment)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura inválida")

    try:
        payload = json.loads(_b64url_decode(payload_segment).decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Payload inválido") from exc

    exp = payload.get("exp")
    if not isinstance(exp, int) or datetime.fromtimestamp(exp, tz=UTC) <= now_utc():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")

    return payload

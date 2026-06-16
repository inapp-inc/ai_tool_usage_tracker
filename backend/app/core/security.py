"""Password hashing and JWT helpers."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import Settings, get_settings

_password_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _password_hasher.hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, plain)
    except VerifyMismatchError:
        return False


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(
    *,
    user_id: UUID,
    organization_id: UUID,
    role: str,
    email: str,
    settings: Settings | None = None,
) -> tuple[str, int]:
    cfg = settings or get_settings()
    expires_in = cfg.jwt_access_token_expire_minutes * 60
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "type": "access",
    }
    token = jwt.encode(payload, cfg.jwt_secret_key, algorithm="HS256")
    return token, expires_in


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    payload = jwt.decode(token, cfg.jwt_secret_key, algorithms=["HS256"])
    if payload.get("type") != "access":
        msg = "Invalid token type"
        raise jwt.InvalidTokenError(msg)
    return payload

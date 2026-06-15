"""Password hashing and JWT utilities."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import Settings, get_settings

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def normalize_email(email: str) -> str:
    """Normalize email for lookup and storage."""
    return email.strip().lower()


def hash_password(password: str) -> str:
    """Hash password with Argon2id."""
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def generate_opaque_refresh_token() -> str:
    """Generate cryptographically random opaque refresh token."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hash for refresh token storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    role: str,
    settings: Settings | None = None,
) -> tuple[str, int]:
    """Create JWT access token; returns (token, expires_in_seconds)."""
    settings = settings or get_settings()
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "org": str(organization_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm="HS256",
    )
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Decode and validate JWT access token."""
    settings = settings or get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=["HS256"],
    )

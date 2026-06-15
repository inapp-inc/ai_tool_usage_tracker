"""Unit tests for security helpers."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    normalize_email,
    verify_password,
)


def test_normalize_email_lowercase() -> None:
    assert normalize_email(" Admin@Acme.EXAMPLE ") == "admin@acme.example"


def test_password_hash_and_verify() -> None:
    hashed = hash_password("SecurePass123!")
    assert verify_password(hashed, "SecurePass123!")
    assert not verify_password(hashed, "wrong")


def test_jwt_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "unit_test_secret")
    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    token, expires_in = create_access_token(
        user_id=user_id,
        organization_id=org_id,
        role="super_admin",
        settings=settings,
    )
    assert expires_in == 30 * 60
    payload = decode_access_token(token, settings=settings)
    assert payload["sub"] == str(user_id)
    assert payload["org"] == str(org_id)
    assert payload["role"] == "super_admin"


def test_expired_jwt_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "unit_test_secret")
    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    expired = datetime.now(UTC) - timedelta(minutes=1)
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "org": str(uuid.uuid4()),
            "role": "team_member",
            "exp": expired,
            "iat": expired,
            "jti": str(uuid.uuid4()),
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token, settings=settings)

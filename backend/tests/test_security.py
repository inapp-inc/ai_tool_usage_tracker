"""Security helper tests."""

from uuid import uuid4

import jwt
import pytest

from app.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        JWT_SECRET_KEY="test-secret-key",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
        COLLECTOR_ENCRYPTION_KEY="test-collector-key",
    )


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("SecurePass123!")
    assert verify_password("SecurePass123!", hashed)
    assert not verify_password("wrong", hashed)


def test_refresh_token_hash_is_deterministic() -> None:
    assert hash_refresh_token("abc") == hash_refresh_token("abc")
    assert hash_refresh_token("abc") != hash_refresh_token("xyz")


def test_access_token_encode_decode(settings: Settings) -> None:
    user_id = uuid4()
    org_id = uuid4()
    token, expires_in = create_access_token(
        user_id=user_id,
        organization_id=org_id,
        role="super_admin",
        email="admin@example.com",
        settings=settings,
    )
    assert expires_in == 30 * 60
    payload = decode_access_token(token, settings=settings)
    assert payload["sub"] == str(user_id)
    assert payload["org"] == str(org_id)
    assert payload["role"] == "super_admin"


def test_access_token_rejects_wrong_type(settings: Settings) -> None:
    token = jwt.encode(
        {"sub": str(uuid4()), "type": "refresh"},
        settings.jwt_secret_key,
        algorithm="HS256",
    )
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token, settings=settings)

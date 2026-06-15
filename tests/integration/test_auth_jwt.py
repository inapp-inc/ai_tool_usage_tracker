"""Integration tests for expired JWT."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_expired_token(auth_env: None) -> None:
    settings = get_settings()
    expired = datetime.now(UTC) - timedelta(minutes=5)
    token = jwt.encode(
        {
            "sub": "550e8400-e29b-41d4-a716-446655440001",
            "org": "660e8400-e29b-41d4-a716-446655440000",
            "role": "team_member",
            "exp": expired,
            "iat": expired,
            "jti": "test-jti",
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 401

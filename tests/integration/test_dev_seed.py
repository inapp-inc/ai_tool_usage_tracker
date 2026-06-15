"""Integration tests for dev seed script."""

import os
import subprocess
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.models.auth import User

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_dev_seed_creates_super_admin(auth_env: None, database_url: str) -> None:
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env={**os.environ, "DATABASE_URL": database_url},
        check=True,
    )
    subprocess.run(
        ["python", "-m", "app.scripts.seed_dev_admin"],
        cwd=BACKEND_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": database_url,
            "PYTHONPATH": str(BACKEND_ROOT),
        },
        check=True,
    )

    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(User))
        assert count == 1

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@acme.example", "password": "SecurePass123!"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "Bearer"
    assert "access_token" in body
    await engine.dispose()

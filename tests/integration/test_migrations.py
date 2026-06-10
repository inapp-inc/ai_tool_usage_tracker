"""Integration tests for Alembic migrations (TASK-INF-004)."""

import os
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

pytestmark = pytest.mark.integration

SCHEMAS = (
    "auth",
    "admin",
    "ingestion",
    "usage",
    "notifications",
    "reporting",
    "audit",
)


@pytest.fixture
def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — run with Docker Postgres for integration test")
    return url


@pytest.mark.asyncio
async def test_initial_schemas(database_url: str) -> None:
    """Verify migration revision creates application schemas."""
    import subprocess

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            for schema in SCHEMAS:
                row = await connection.execute(
                    text(
                        "SELECT schema_name FROM information_schema.schemata "
                        "WHERE schema_name = :name"
                    ),
                    {"name": schema},
                )
                assert row.scalar_one_or_none() == schema
    finally:
        await engine.dispose()

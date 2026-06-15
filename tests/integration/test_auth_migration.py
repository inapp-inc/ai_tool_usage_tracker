"""Integration tests for auth schema migration."""

import os
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

pytestmark = pytest.mark.integration


@pytest.fixture
async def migrated_db(auth_env: None, database_url: str):
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    yield database_url


@pytest.mark.asyncio
async def test_auth_tables_exist(migrated_db: str) -> None:
    engine = create_async_engine(migrated_db)
    try:
        async with engine.connect() as conn:
            for table in ("organizations", "users", "refresh_tokens"):
                row = await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'auth' AND table_name = :name"
                    ),
                    {"name": table},
                )
                assert row.scalar_one_or_none() == table
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_retention_constraints(migrated_db: str) -> None:
    engine = create_async_engine(migrated_db)
    org_id = str(uuid.uuid4())
    try:
        async with engine.begin() as conn:
            with pytest.raises(Exception):
                await conn.execute(
                    text(
                        "INSERT INTO auth.organizations "
                        "(id, name, slug, timezone, retention_months, retention_audit_months, settings) "
                        "VALUES (:id, 'Bad', 'bad', 'UTC', 12, 12, '{}')"
                    ),
                    {"id": org_id},
                )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_valid_role_insert(migrated_db: str) -> None:
    engine = create_async_engine(migrated_db)
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO auth.organizations "
                    "(id, name, slug, timezone, retention_months, retention_audit_months, settings) "
                    "VALUES (:id, 'Test Org', 'test-org', 'UTC', 24, 24, '{}')"
                ),
                {"id": org_id},
            )
            await conn.execute(
                text(
                    "INSERT INTO auth.users "
                    "(id, organization_id, email, password_hash, role, active) "
                    "VALUES (:uid, :oid, 'user@test.com', 'hash', 'super_admin', true)"
                ),
                {"uid": user_id, "oid": org_id},
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_invalid_role_rejected(migrated_db: str) -> None:
    engine = create_async_engine(migrated_db)
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO auth.organizations "
                    "(id, name, slug, timezone, retention_months, retention_audit_months, settings) "
                    "VALUES (:id, 'Test Org 2', 'test-org-2', 'UTC', 24, 24, '{}')"
                ),
                {"id": org_id},
            )
            with pytest.raises(Exception):
                await conn.execute(
                    text(
                        "INSERT INTO auth.users "
                        "(id, organization_id, email, password_hash, role, active) "
                        "VALUES (:uid, :oid, 'bad@test.com', 'hash', 'invalid_role', true)"
                    ),
                    {"uid": user_id, "oid": org_id},
                )
    finally:
        await engine.dispose()

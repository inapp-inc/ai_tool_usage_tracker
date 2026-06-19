"""Unit tests for PermissionCache and permission evaluation."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.permissions import PermissionCache
from app.models.roles import RolePermission


@pytest.fixture(autouse=True)
def clear_permission_cache() -> None:
    PermissionCache.clear()
    yield
    PermissionCache.clear()


def _make_perm(resource: str, *, can_read: bool, can_write: bool, team_scoped: bool = False):
    row = MagicMock(spec=RolePermission)
    row.resource = resource
    row.can_read = can_read
    row.can_write = can_write
    row.team_scoped = team_scoped
    return row


@pytest.mark.asyncio
async def test_write_implies_read() -> None:
    role_id = uuid.uuid4()
    session = AsyncMock()
    session.execute.return_value.scalars.return_value.all.return_value = [
        _make_perm("uploads", can_read=False, can_write=True),
    ]

    allowed = await PermissionCache.check(role_id, "uploads", "read", session)
    assert allowed is True


@pytest.mark.asyncio
async def test_missing_row_denied() -> None:
    role_id = uuid.uuid4()
    session = AsyncMock()
    session.execute.return_value.scalars.return_value.all.return_value = []

    allowed = await PermissionCache.check(role_id, "credentials", "read", session)
    assert allowed is False


@pytest.mark.asyncio
async def test_cache_hit_on_second_call() -> None:
    role_id = uuid.uuid4()
    session = AsyncMock()
    session.execute.return_value.scalars.return_value.all.return_value = [
        _make_perm("alerts", can_read=True, can_write=False),
    ]

    first = await PermissionCache.check(role_id, "alerts", "read", session)
    second = await PermissionCache.check(role_id, "alerts", "read", session)

    assert first is True
    assert second is True
    assert session.execute.await_count == 1


@pytest.mark.asyncio
async def test_invalidation_triggers_reload() -> None:
    role_id = uuid.uuid4()
    session = AsyncMock()
    session.execute.return_value.scalars.return_value.all.return_value = [
        _make_perm("alerts", can_read=True, can_write=False),
    ]

    await PermissionCache.check(role_id, "alerts", "read", session)
    PermissionCache.invalidate(role_id)
    await PermissionCache.check(role_id, "alerts", "read", session)

    assert session.execute.await_count == 2

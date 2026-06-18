"""Tests for built-in org catalogue tool seeding."""

import pytest

from app.settings.builtin_catalog import BUILTIN_CATALOGUE_SLUGS
from app.tools.builtin_seed import sync_org_builtin_catalogue_tools


@pytest.mark.asyncio
async def test_sync_org_builtin_catalogue_tools_creates_all_products() -> None:
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4

    org_id = uuid4()
    session = AsyncMock()

    async def fake_execute(stmt):  # noqa: ANN001
        result = MagicMock()
        result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        return result

    session.execute = fake_execute

    await sync_org_builtin_catalogue_tools(session, org_id)

    assert session.add.call_count == len(BUILTIN_CATALOGUE_SLUGS)


@pytest.mark.asyncio
async def test_sync_org_builtin_catalogue_tools_handles_duplicate_rows() -> None:
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4

    from app.tools.builtin_seed import _pick_canonical_catalogue_row, _retire_duplicate_catalogue_rows

    org_id = uuid4()
    now = datetime.now(UTC)

    older = MagicMock()
    older.id = uuid4()
    older.built_in = False
    older.catalogue_only = True
    older.active = True
    older.created_at = now

    newer = MagicMock()
    newer.id = uuid4()
    newer.built_in = False
    newer.catalogue_only = True
    newer.active = True
    newer.created_at = now.replace(year=now.year + 1)

    canonical = _pick_canonical_catalogue_row([newer, older])
    assert canonical.id == older.id

    _retire_duplicate_catalogue_rows(canonical, [older, newer])
    assert older.active is True
    assert newer.active is False
    assert newer.built_in is False

    session = AsyncMock()

    async def fake_execute(stmt):  # noqa: ANN001
        result = MagicMock()
        result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[older, newer]))
        )
        return result

    session.execute = fake_execute

    await sync_org_builtin_catalogue_tools(session, org_id)

    assert older.built_in is True
    assert session.add.call_count == 0


@pytest.mark.asyncio
async def test_delete_builtin_catalogue_tool_returns_409() -> None:
    from unittest.mock import AsyncMock, MagicMock
    from uuid import uuid4

    from fastapi import HTTPException

    from app.tools.service import ToolService

    org_id = uuid4()
    tool_id = uuid4()
    session = AsyncMock()
    service = ToolService(session)

    tool = MagicMock()
    tool.catalogue_only = True
    tool.built_in = True
    service._require_tool = AsyncMock(return_value=tool)

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_tool(org_id, tool_id)

    assert exc_info.value.status_code == 409

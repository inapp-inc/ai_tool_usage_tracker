"""Tests for collector pull window resolution."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.collector.service import CollectorService
from app.models.admin import Tool
from app.models.collector import CollectorConfig


@pytest.mark.asyncio
async def test_resolve_pull_since_uses_full_sync_window_not_pull_interval() -> None:
    """Incremental sync must not be capped to the last pull interval (e.g. 60 minutes)."""
    tool_id = uuid4()
    config = CollectorConfig(
        id=uuid4(),
        name="Cursor",
        provider="cursor",
        api_token_ciphertext="cipher",
        pull_interval_minutes=60,
        active=True,
        tool_id=tool_id,
    )
    tool = MagicMock(spec=Tool)
    tool.id = tool_id
    tool.vendor = "cursor"
    tool.organization_id = uuid4()
    tool.pricing_config = {"team_id": str(uuid4())}

    session = AsyncMock()
    session.get = AsyncMock(return_value=tool)

    latest = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=uuid4())),  # collector ingest
            MagicMock(scalar_one_or_none=MagicMock(return_value=latest)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=datetime(2026, 3, 31, tzinfo=UTC))),
        ]
    )

    until = datetime(2026, 6, 29, 15, 0, tzinfo=UTC)
    service = CollectorService(session)
    since = await service._resolve_pull_since(config, until)

    interval_cap = until - timedelta(minutes=config.pull_interval_minutes)
    assert since < interval_cap
    assert since == latest - timedelta(hours=1)

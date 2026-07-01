"""Tests for usage sync window resolution."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.collector.sync_since import (
    billing_period_start,
    resolve_initial_sync_since,
    resolve_usage_sync_since,
)
from app.models.admin import Tool


@pytest.mark.asyncio
async def test_resolve_initial_sync_since_uses_month_start() -> None:
    tool = MagicMock(spec=Tool)
    tool.created_at = datetime(2026, 6, 15, tzinfo=UTC)
    tool.id = uuid4()

    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    until = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
    since = await resolve_initial_sync_since(session, tool, until)

    assert since == until - timedelta(days=90)


@pytest.mark.asyncio
async def test_resolve_initial_sync_since_uses_earlier_subscription_start() -> None:
    tool = MagicMock(spec=Tool)
    tool.created_at = datetime(2026, 6, 15, tzinfo=UTC)
    tool.id = uuid4()

    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=date(2026, 3, 1))
        )
    )

    until = datetime(2026, 6, 25, tzinfo=UTC)
    since = await resolve_initial_sync_since(session, tool, until)

    assert since == datetime(2026, 3, 1, tzinfo=UTC)


@pytest.mark.asyncio
async def test_resolve_usage_sync_since_first_connect_delegates_to_initial() -> None:
    tool = MagicMock(spec=Tool)
    tool.created_at = datetime(2026, 6, 10, tzinfo=UTC)
    tool.id = uuid4()
    tool.vendor = "cursor"
    tool.organization_id = uuid4()

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # no collector ingest
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # subscription
        ]
    )

    until = datetime(2026, 6, 25, tzinfo=UTC)
    since = await resolve_usage_sync_since(session, tool, until)

    assert since == until - timedelta(days=90)


@pytest.mark.asyncio
async def test_resolve_usage_sync_since_new_credential_ignores_other_team_events() -> None:
    """First ingest for a credential must not be capped by another team's usage history."""
    tool = MagicMock(spec=Tool)
    tool.id = uuid4()
    tool.vendor = "cursor"
    tool.organization_id = uuid4()
    tool.created_at = datetime(2026, 6, 1, tzinfo=UTC)
    tool.pricing_config = {"team_id": str(uuid4())}

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # no collector ingest
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # subscription
        ]
    )

    until = datetime(2026, 6, 25, tzinfo=UTC)
    since = await resolve_usage_sync_since(session, tool, until)

    assert since == until - timedelta(days=90)


@pytest.mark.asyncio
async def test_resolve_usage_sync_since_incremental_from_latest_event() -> None:
    tool = MagicMock(spec=Tool)
    tool.id = uuid4()
    tool.vendor = "cursor"
    tool.organization_id = uuid4()
    tool.pricing_config = {}

    latest = datetime(2026, 6, 20, 15, 0, tzinfo=UTC)
    earliest = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=uuid4())),  # collector ingest
            MagicMock(scalar_one_or_none=MagicMock(return_value=latest)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # subscription
            MagicMock(scalar_one_or_none=MagicMock(return_value=earliest)),
        ]
    )

    until = datetime(2026, 6, 25, tzinfo=UTC)
    since = await resolve_usage_sync_since(session, tool, until)

    assert since == latest.replace(hour=14)


@pytest.mark.asyncio
async def test_resolve_usage_sync_since_backfills_billing_gap() -> None:
    tool = MagicMock(spec=Tool)
    tool.created_at = datetime(2026, 6, 15, tzinfo=UTC)
    tool.id = uuid4()
    tool.vendor = "cursor"
    tool.organization_id = uuid4()
    tool.pricing_config = {}

    latest = datetime(2026, 6, 20, 15, 0, tzinfo=UTC)
    earliest = datetime(2026, 6, 10, tzinfo=UTC)
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=uuid4())),  # collector ingest
            MagicMock(scalar_one_or_none=MagicMock(return_value=latest)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # subscription
            MagicMock(scalar_one_or_none=MagicMock(return_value=earliest)),
        ]
    )

    until = datetime(2026, 6, 25, tzinfo=UTC)
    since = await resolve_usage_sync_since(session, tool, until)

    assert since == billing_period_start(until)

"""Tests for provider-agnostic usage routing via integration_config."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.collector.adapters.registry import fetch_provider_usage


@pytest.mark.asyncio
@patch("app.collector.adapters.registry.fetch_usage_from_config", new_callable=AsyncMock)
async def test_fetch_provider_usage_uses_engine_for_any_vendor(
    mock_engine: AsyncMock,
) -> None:
    from app.collector.adapters.base import UsageRecord
    from decimal import Decimal

    mock_engine.return_value = [
        UsageRecord(
            vendor_event_id="evt-1",
            model="default",
            occurred_at=datetime(2026, 6, 1, tzinfo=UTC),
            input_tokens=10,
            output_tokens=0,
            estimated_cost=Decimal("0"),
        )
    ]
    config = {
        "usage": {
            "url": "{api_endpoint}",
            "response": {
                "fields": {
                    "vendor_event_id": "id",
                    "occurred_at": "timestamp",
                    "input_tokens": "tokens_used",
                }
            },
        }
    }
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 2, tzinfo=UTC)

    records = await fetch_provider_usage(
        "openai",
        "secret",
        since=since,
        until=until,
        api_endpoint="https://api.example.com/usage",
        integration_config=config,
    )

    assert len(records) == 1
    mock_engine.assert_awaited_once()
    assert mock_engine.await_args.kwargs["integration_config"] == config


@pytest.mark.asyncio
async def test_fetch_provider_usage_cursor_adapter_ignores_extra_kwargs() -> None:
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 2, tzinfo=UTC)

    with patch(
        "app.collector.adapters.cursor.CursorUsageAdapter.fetch_usage",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_fetch:
        await fetch_provider_usage(
            "cursor",
            "secret",
            since=since,
            until=until,
            pricing_config={"team_id": "abc"},
            api_endpoint="https://api.cursor.com/v1/me",
        )

    mock_fetch.assert_awaited_once()
    call_kwargs = mock_fetch.await_args.kwargs
    assert call_kwargs["since"] == since
    assert call_kwargs["until"] == until

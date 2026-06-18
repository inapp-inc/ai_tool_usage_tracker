"""Tests for config-driven usage polling engine."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.collector.adapters.http_utils import HttpResult
from app.integration.engine import IntegrationConfigError, fetch_usage_from_config, validate_integration_config
from app.integration.mapping import map_record, resolve_field_value


def test_validate_integration_config_requires_usage_fields() -> None:
    with pytest.raises(IntegrationConfigError, match="url is required"):
        validate_integration_config({"usage": {"response": {"fields": {}}}})


def test_map_record_dot_paths() -> None:
    record = {"id": "evt-1", "date": "2026-06-01", "metrics": {"in": 42}}
    mapped = map_record(
        record,
        {
            "vendor_event_id": "id",
            "occurred_at": "date",
            "input_tokens": "metrics.in",
            "output_tokens": "0",
            "estimated_cost": "0",
            "model": "copilot",
        },
    )
    assert mapped["vendor_event_id"] == "evt-1"
    assert mapped["input_tokens"] == 42
    assert mapped["model"] == "copilot"


def test_resolve_field_value_template() -> None:
    record = {"date": "2026-06-01", "org": "inapp"}
    assert resolve_field_value(record, "{org}-{date}") == "inapp-2026-06-01"


def test_map_record_user_fields() -> None:
    record = {"id": "1", "date": "2026-06-01", "email": "dev@example.com", "display_name": "Dev User"}
    mapped = map_record(
        record,
        {
            "vendor_event_id": "id",
            "occurred_at": "date",
            "input_tokens": "10",
            "user_email": "email",
            "user_name": "display_name",
        },
    )
    assert mapped["user_email"] == "dev@example.com"
    assert mapped["user_name"] == "Dev User"


@pytest.mark.asyncio
@patch("app.integration.engine.get_with_detail", new_callable=AsyncMock)
async def test_fetch_usage_from_config_get(mock_get_detail: AsyncMock) -> None:
    mock_get_detail.return_value = HttpResult(
        status_code=200,
        text="[]",
        json=[
            {
                "id": "row-1",
                "date": "2026-06-01T00:00:00Z",
                "total_tokens": 100,
            }
        ],
    )
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 2, tzinfo=UTC)
    config = {
        "version": 1,
        "auth": {"type": "bearer", "header": "Authorization", "prefix": "Bearer "},
        "usage": {
            "method": "GET",
            "url": "{api_endpoint}",
            "query": {"since": "{since_iso}", "until": "{until_iso}"},
            "response": {
                "type": "json_array",
                "fields": {
                    "vendor_event_id": "id",
                    "occurred_at": "date",
                    "input_tokens": "total_tokens",
                    "output_tokens": "0",
                    "estimated_cost": "0",
                    "model": "default",
                },
            },
        },
    }

    records = await fetch_usage_from_config(
        "secret-token",
        integration_config=config,
        since=since,
        until=until,
        api_endpoint="https://api.example.com/usage",
    )

    assert len(records) == 1
    assert records[0].vendor_event_id == "row-1"
    assert records[0].input_tokens == 100
    assert records[0].estimated_cost == Decimal("0")
    mock_get_detail.assert_awaited_once()
    call_kwargs = mock_get_detail.await_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer secret-token"
    assert "since" in call_kwargs["params"]


@pytest.mark.asyncio
@patch("app.integration.engine.get_with_detail", new_callable=AsyncMock)
async def test_fetch_usage_http_error(mock_get_detail: AsyncMock) -> None:
    mock_get_detail.return_value = HttpResult(
        status_code=404,
        text='{"message":"Not Found"}',
        json={"message": "Not Found"},
    )
    config = {
        "usage": {
            "method": "GET",
            "url": "https://api.example.com/usage",
            "response": {
                "type": "json_array",
                "fields": {
                    "vendor_event_id": "id",
                    "occurred_at": "date",
                    "input_tokens": "total_tokens",
                },
            },
        },
    }
    with pytest.raises(IntegrationConfigError, match="HTTP 404"):
        await fetch_usage_from_config(
            "token",
            integration_config=config,
            since=datetime(2026, 6, 1, tzinfo=UTC),
            until=datetime(2026, 6, 2, tzinfo=UTC),
            api_endpoint=None,
        )

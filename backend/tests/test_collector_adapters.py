"""Tests for provider adapters."""

from datetime import UTC, datetime, timedelta

import pytest

from app.collector.adapters.base import ProviderValidationError, resolve_provider_api_url
from app.collector.adapters.cursor import CursorUsageAdapter
from app.collector.adapters.figma import FigmaUsageAdapter
from app.collector.adapters.generic import GenericUsageAdapter
from app.collector.adapters.openai import OpenAIUsageAdapter
from app.collector.adapters.registry import SUPPORTED_PROVIDERS, get_adapter


def test_resolve_provider_api_url_prefers_tool_endpoint() -> None:
    assert (
        resolve_provider_api_url(
            "https://custom.example.com/v1/models",
            default_url="https://api.openai.com/v1/models",
        )
        == "https://custom.example.com/v1/models"
    )
    assert (
        resolve_provider_api_url(None, default_url="https://api.openai.com/v1/models")
        == "https://api.openai.com/v1/models"
    )


@pytest.mark.asyncio
async def test_openai_adapter_stub_records() -> None:
    adapter = OpenAIUsageAdapter()
    until = datetime.now(UTC)
    since = until - timedelta(hours=1)
    records = await adapter.fetch_usage("invalid-token", since=since, until=until)
    assert len(records) >= 1
    assert records[0].total_tokens > 0
    assert records[0].vendor_event_id.startswith("openai-stub-")


@pytest.mark.asyncio
async def test_openai_snapshot_aggregates_tokens() -> None:
    adapter = OpenAIUsageAdapter()
    snapshot = await adapter.fetch_snapshot("invalid-token")
    assert snapshot.tokens_used > 0
    assert snapshot.total_cost >= 0
    assert snapshot.sync_status == "active"


@pytest.mark.asyncio
async def test_generic_adapter_rejects_short_key() -> None:
    adapter = GenericUsageAdapter("custom")
    with pytest.raises(ProviderValidationError):
        await adapter.validate_api_key("short")


@pytest.mark.parametrize("provider", sorted(SUPPORTED_PROVIDERS))
def test_registry_has_all_providers(provider: str) -> None:
    adapter = get_adapter(provider)
    assert adapter.provider == provider or hasattr(adapter, "provider")


def test_cursor_adapter_is_registered() -> None:
    adapter = get_adapter("cursor")
    assert isinstance(adapter, CursorUsageAdapter)


def test_copilot_adapter_is_registered() -> None:
    from app.collector.adapters.copilot import CopilotUsageAdapter

    adapter = get_adapter("copilot")
    assert isinstance(adapter, CopilotUsageAdapter)


def test_figma_adapter_is_registered() -> None:
    adapter = get_adapter("figma")
    assert isinstance(adapter, FigmaUsageAdapter)


@pytest.mark.asyncio
async def test_figma_adapter_rejects_short_token() -> None:
    adapter = FigmaUsageAdapter()
    with pytest.raises(ProviderValidationError):
        await adapter.validate_api_key("short")


@pytest.mark.asyncio
async def test_figma_fetch_usage_creates_seat_records() -> None:
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock, patch

    adapter = FigmaUsageAdapter()
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 2, tzinfo=UTC)
    members = [
        __import__("app.collector.adapters.base", fromlist=["ProviderMember"]).ProviderMember(
            email="designer@example.com",
            name="Designer",
        )
    ]
    with patch.object(adapter, "fetch_members", new=AsyncMock(return_value=members)):
        records = await adapter.fetch_usage("token", since=since, until=until)
    assert len(records) == 1
    assert records[0].user_email == "designer@example.com"
    assert records[0].total_tokens == 1

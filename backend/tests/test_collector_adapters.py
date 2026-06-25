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
async def test_openai_validate_api_key_rejects_short_key() -> None:
    adapter = OpenAIUsageAdapter()
    with pytest.raises(ProviderValidationError, match="at least 8 characters"):
        await adapter.validate_api_key("short")


@pytest.mark.asyncio
async def test_openai_validate_api_key_rejects_project_key_prefix() -> None:
    adapter = OpenAIUsageAdapter()
    with pytest.raises(ProviderValidationError, match="project API key"):
        await adapter.validate_api_key("sk-proj-valid-key-123456789012345678901234567890")


@pytest.mark.asyncio
async def test_openai_validate_api_key_accepts_admin_key() -> None:
    from unittest.mock import AsyncMock, patch

    from app.collector.adapters.http_utils import HttpResult

    adapter = OpenAIUsageAdapter()
    forbidden = HttpResult(status_code=403, text='{"error":"Forbidden"}', json={"error": "Forbidden"})
    ok = HttpResult(status_code=200, text='{"data":[]}', json={"data": []})

    async def fake_get_with_detail(url, *, headers=None, params=None, timeout=20.0):
        del headers, params, timeout
        if "usage/completions" in url:
            return ok
        return forbidden

    with patch(
        "app.collector.adapters.openai.get_with_detail",
        new=AsyncMock(side_effect=fake_get_with_detail),
    ):
        await adapter.validate_api_key("sk-admin-valid-key-123456789012345678901234567890")


@pytest.mark.asyncio
async def test_openai_validate_api_key_rejects_project_key_via_models_probe() -> None:
    from unittest.mock import AsyncMock, patch

    from app.collector.adapters.http_utils import HttpResult

    adapter = OpenAIUsageAdapter()
    forbidden = HttpResult(status_code=403, text='{"error":"Forbidden"}', json={"error": "Forbidden"})
    models_ok = HttpResult(status_code=200, text='{"data":[]}', json={"data": []})

    with patch(
        "app.collector.adapters.openai.get_with_detail",
        new=AsyncMock(side_effect=[forbidden, forbidden, forbidden, forbidden, models_ok]),
    ):
        with pytest.raises(ProviderValidationError, match="not an Organization Admin API key"):
            await adapter.validate_api_key("sk-legacy-valid-key-123456789012345678901234567890")


@pytest.mark.asyncio
async def test_openai_validate_api_key_rejects_invalid_key() -> None:
    from unittest.mock import AsyncMock, patch

    from app.collector.adapters.http_utils import HttpResult

    adapter = OpenAIUsageAdapter()
    unauthorized = HttpResult(status_code=401, text='{"error":"Unauthorized"}', json={"error": "Unauthorized"})

    with patch(
        "app.collector.adapters.openai.get_with_detail",
        new=AsyncMock(return_value=unauthorized),
    ):
        with pytest.raises(ProviderValidationError, match="Invalid or expired OpenAI Admin API key"):
            await adapter.validate_api_key("sk-admin-invalid-key-123456789012345678901234567890")


def test_normalize_openai_admin_token_strips_wrappers() -> None:
    from app.collector.adapters.openai import normalize_openai_admin_token

    assert normalize_openai_admin_token('  "sk-admin-abc"\n') == "sk-admin-abc"


@pytest.mark.asyncio
async def test_openai_validate_api_key_rejects_users_only_access() -> None:
    from unittest.mock import AsyncMock, patch

    from app.collector.adapters.http_utils import HttpResult

    adapter = OpenAIUsageAdapter()
    forbidden = HttpResult(status_code=403, text='{"error":"Forbidden"}', json={"error": "Forbidden"})
    users_ok = HttpResult(status_code=200, text='{"data":[]}', json={"data": []})

    async def fake_get_with_detail(url, *, headers=None, params=None, timeout=20.0):
        del headers, params, timeout
        if "organization/users" in url:
            return users_ok
        return forbidden

    with patch(
        "app.collector.adapters.openai.get_with_detail",
        new=AsyncMock(side_effect=fake_get_with_detail),
    ):
        with patch(
            "app.collector.adapters.openai.OPENAI_MODELS_URL",
            "https://api.openai.com/v1/models",
        ):
            with pytest.raises(ProviderValidationError, match="usage or costs"):
                await adapter.validate_api_key("sk-admin-valid-key-123456789012345678901234567890")


@pytest.mark.asyncio
async def test_openai_fetch_usage_paginates_and_parses() -> None:
    from unittest.mock import AsyncMock, patch

    from app.collector.adapters.http_utils import HttpResult

    adapter = OpenAIUsageAdapter()
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 8, tzinfo=UTC)
    usage_page_1 = HttpResult(
        status_code=200,
        text="{}",
        json={
            "data": [
                {
                    "start_time": int(since.timestamp()),
                    "results": [
                        {
                            "input_tokens": 100,
                            "output_tokens": 50,
                            "model": "gpt-4o",
                            "user_id": "user-1",
                        }
                    ],
                }
            ],
            "next_page": "cursor-2",
        },
    )
    usage_page_2 = HttpResult(
        status_code=200,
        text="{}",
        json={
            "data": [
                {
                    "start_time": int((since + timedelta(days=1)).timestamp()),
                    "results": [
                        {
                            "input_tokens": 20,
                            "output_tokens": 10,
                            "model": "gpt-4o-mini",
                            "user_id": "user-2",
                        }
                    ],
                }
            ],
        },
    )
    empty_users = HttpResult(status_code=200, text='{"data":[]}', json={"data": []})
    empty_costs = HttpResult(status_code=200, text='{"data":[]}', json={"data": []})

    responses = {
        "users": [empty_users],
        "usage": [usage_page_1, usage_page_2, empty_costs, empty_costs],
    }

    async def fake_get_with_detail(url, *, headers=None, params=None, timeout=20.0):
        del headers, timeout
        if "organization/users" in url:
            return responses["users"][0]
        if "usage/" in url:
            if responses["usage"]:
                return responses["usage"].pop(0)
            return empty_costs
        if "organization/costs" in url:
            return empty_costs
        return HttpResult(status_code=404, text="", json=None)

    with patch(
        "app.collector.adapters.openai.get_with_detail",
        new=AsyncMock(side_effect=fake_get_with_detail),
    ):
        records = await adapter.fetch_usage("sk-admin-valid-key-12345678", since=since, until=until)

    assert len(records) == 2
    assert records[0].input_tokens == 100
    assert records[1].input_tokens == 20


@pytest.mark.asyncio
async def test_openai_fetch_members_falls_back_when_org_users_forbidden() -> None:
    from unittest.mock import AsyncMock, patch

    from app.collector.adapters.base import ProviderMember
    from app.collector.adapters.http_utils import HttpResult

    adapter = OpenAIUsageAdapter()
    forbidden = HttpResult(status_code=403, text='{"error":"Forbidden"}', json={"error": "Forbidden"})

    with patch(
        "app.collector.adapters.openai.get_with_detail",
        new=AsyncMock(return_value=forbidden),
    ):
        with patch.object(
            adapter,
            "fetch_usage",
            new=AsyncMock(
                return_value=[
                    __import__(
                        "app.collector.adapters.base", fromlist=["UsageRecord"]
                    ).UsageRecord(
                        vendor_event_id="u1",
                        model="gpt-4o",
                        occurred_at=datetime.now(UTC),
                        input_tokens=10,
                        output_tokens=5,
                        estimated_cost=__import__("decimal").Decimal("0"),
                        user_email="dev@example.com",
                    )
                ]
            ),
        ):
            members = await adapter.fetch_members("test-key")

    assert len(members) == 1
    assert members[0].email == "dev@example.com"


@pytest.mark.asyncio
async def test_openai_adapter_returns_empty_on_auth_failure() -> None:
    adapter = OpenAIUsageAdapter()
    until = datetime.now(UTC)
    since = until - timedelta(hours=1)
    records = await adapter.fetch_usage("invalid-token", since=since, until=until)
    assert records == []


@pytest.mark.asyncio
async def test_openai_snapshot_with_no_usage() -> None:
    adapter = OpenAIUsageAdapter()
    snapshot = await adapter.fetch_snapshot("invalid-token")
    assert snapshot.tokens_used == 0
    assert snapshot.total_cost == 0
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

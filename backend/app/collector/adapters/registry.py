"""Register provider adapters by name."""

from datetime import datetime
from typing import Protocol

from app.collector.adapters.anthropic import AnthropicUsageAdapter
from app.collector.adapters.azure_openai import AzureOpenAIUsageAdapter
from app.collector.adapters.base import (
    SUPPORTED_PROVIDERS,
    ProviderMember,
    ProviderSnapshot,
    ProviderValidationError,
    UsageRecord,
)
from app.collector.adapters.cursor import CursorUsageAdapter
from app.collector.adapters.figma import FigmaUsageAdapter
from app.collector.adapters.generic import GenericUsageAdapter
from app.collector.adapters.google import GoogleUsageAdapter
from app.collector.adapters.openai import OpenAIUsageAdapter
from app.integration.engine import IntegrationConfigError, fetch_usage_from_config
from app.settings.builtin_catalog import ADAPTER_ALIASES


class ProviderAdapter(Protocol):
    provider: str

    async def validate_api_key(self, api_token: str, **kwargs: object) -> None: ...

    async def fetch_snapshot(self, api_token: str, **kwargs: object) -> ProviderSnapshot: ...

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since,
        until,
    ) -> list[UsageRecord]: ...

    async def fetch_members(
        self,
        api_token: str,
        **kwargs: object,
    ) -> list[ProviderMember]: ...


_ADAPTERS: dict[str, ProviderAdapter] = {
    "openai": OpenAIUsageAdapter(),
    "anthropic": AnthropicUsageAdapter(),
    "google": GoogleUsageAdapter(),
    "azure_openai": AzureOpenAIUsageAdapter(),
    "copilot": GenericUsageAdapter("copilot"),
    "bedrock": GenericUsageAdapter("bedrock"),
    "custom": GenericUsageAdapter("custom"),
    "cursor": CursorUsageAdapter(),
    "figma": FigmaUsageAdapter(),
}


def resolve_adapter_key(provider: str, *, adapter_key: str | None = None) -> str:
    normalized = provider.strip().lower().replace("-", "_")
    if adapter_key:
        return adapter_key.strip().lower()
    return ADAPTER_ALIASES.get(normalized, normalized)


def get_adapter(provider: str, *, adapter_key: str | None = None) -> ProviderAdapter:
    key = resolve_adapter_key(provider, adapter_key=adapter_key)
    adapter = _ADAPTERS.get(key)
    if adapter is not None:
        return adapter
    return GenericUsageAdapter(key)


def _merge_adapter_config(
    pricing_config: dict | None,
    *,
    api_endpoint: str | None = None,
    integration_config: dict | None = None,
) -> dict:
    config = dict(pricing_config or {})
    if api_endpoint:
        config["api_endpoint"] = api_endpoint
    if integration_config:
        config["integration_config"] = integration_config
    return config


def _integration_config_from_pricing(pricing_config: dict | None) -> dict:
    raw = (pricing_config or {}).get("integration_config")
    return dict(raw) if isinstance(raw, dict) else {}


async def fetch_provider_usage(
    provider: str,
    api_token: str,
    *,
    since: datetime,
    until: datetime,
    pricing_config: dict | None = None,
    api_endpoint: str | None = None,
    integration_config: dict | None = None,
) -> list[UsageRecord]:
    """Poll usage — config engine first when integration_config.usage is set (any provider)."""
    merged_config = _merge_adapter_config(
        pricing_config,
        api_endpoint=api_endpoint,
        integration_config=integration_config,
    )
    config = integration_config or _integration_config_from_pricing(merged_config)
    endpoint = api_endpoint or merged_config.get("api_endpoint")

    if isinstance(config, dict) and config.get("usage"):
        try:
            return await fetch_usage_from_config(
                api_token,
                integration_config=config,
                since=since,
                until=until,
                api_endpoint=endpoint if isinstance(endpoint, str) else None,
                tool_vendor=provider,
                pricing_config=merged_config,
            )
        except IntegrationConfigError as exc:
            raise ProviderValidationError(str(exc)) from exc

    adapter = get_adapter(provider)
    try:
        return await adapter.fetch_usage(
            api_token,
            since=since,
            until=until,
            pricing_config=merged_config,
            api_endpoint=endpoint if isinstance(endpoint, str) else None,
        )
    except TypeError:
        return await adapter.fetch_usage(
            api_token,
            since=since,
            until=until,
            pricing_config=merged_config,
        )


async def validate_provider_api_key(
    provider: str,
    api_token: str,
    *,
    pricing_config: dict | None = None,
    api_endpoint: str | None = None,
) -> None:
    await get_adapter(provider).validate_api_key(
        api_token,
        pricing_config=_merge_adapter_config(pricing_config, api_endpoint=api_endpoint),
        api_endpoint=api_endpoint,
    )


async def fetch_provider_snapshot(
    provider: str,
    api_token: str,
    *,
    package_allowance: int | None = None,
    pricing_config: dict | None = None,
    api_endpoint: str | None = None,
    integration_config: dict | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> ProviderSnapshot:
    merged_config = _merge_adapter_config(
        pricing_config,
        api_endpoint=api_endpoint,
        integration_config=integration_config,
    )
    config = integration_config or _integration_config_from_pricing(merged_config)
    if isinstance(config, dict) and config.get("usage"):
        from datetime import UTC, timedelta

        end = until or datetime.now(UTC)
        start = since or (end - timedelta(days=30))
        records = await fetch_provider_usage(
            provider,
            api_token,
            since=start,
            until=end,
            pricing_config=merged_config,
            api_endpoint=api_endpoint,
            integration_config=config,
        )
        from decimal import Decimal

        tokens_used = sum(record.total_tokens for record in records)
        total_cost = sum((record.estimated_cost for record in records), Decimal("0"))
        balance = None
        if package_allowance is not None:
            balance = max(package_allowance - tokens_used, 0)
        return ProviderSnapshot(
            sync_status="active",
            tokens_used=tokens_used,
            balance_tokens=balance,
            total_cost=total_cost,
            member_count=0,
        )

    return await get_adapter(provider).fetch_snapshot(
        api_token,
        package_allowance=package_allowance,
        pricing_config=merged_config,
        api_endpoint=api_endpoint,
    )


async def fetch_provider_members(
    provider: str,
    api_token: str,
    *,
    pricing_config: dict | None = None,
    api_endpoint: str | None = None,
) -> list[ProviderMember]:
    adapter = get_adapter(provider)
    fetch_members = getattr(adapter, "fetch_members", None)
    if fetch_members is None:
        return []
    return await fetch_members(
        api_token,
        pricing_config=_merge_adapter_config(pricing_config, api_endpoint=api_endpoint),
        api_endpoint=api_endpoint,
    )


__all__ = [
    "SUPPORTED_PROVIDERS",
    "ProviderAdapter",
    "ProviderMember",
    "ProviderValidationError",
    "ProviderSnapshot",
    "UsageRecord",
    "fetch_provider_members",
    "fetch_provider_snapshot",
    "fetch_provider_usage",
    "get_adapter",
    "validate_provider_api_key",
]

"""Register provider adapters by name."""

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
from app.collector.adapters.cohere import CohereUsageAdapter
from app.collector.adapters.cursor import CursorUsageAdapter
from app.collector.adapters.generic import GenericUsageAdapter
from app.collector.adapters.google import GoogleUsageAdapter
from app.collector.adapters.mistral import MistralUsageAdapter
from app.collector.adapters.openai import OpenAIUsageAdapter


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
    "cohere": CohereUsageAdapter(),
    "mistral": MistralUsageAdapter(),
    "custom": GenericUsageAdapter("custom"),
    "mabl": GenericUsageAdapter("mabl"),
    "windsurf": GenericUsageAdapter("windsurf"),
    "cursor": CursorUsageAdapter(),
}


def get_adapter(provider: str) -> ProviderAdapter:
    normalized = provider.strip().lower()
    adapter = _ADAPTERS.get(normalized)
    if adapter is None:
        msg = f"Unsupported provider: {provider}"
        raise ValueError(msg)
    return adapter


async def validate_provider_api_key(
    provider: str,
    api_token: str,
    *,
    pricing_config: dict | None = None,
) -> None:
    await get_adapter(provider).validate_api_key(
        api_token,
        pricing_config=pricing_config,
    )


async def fetch_provider_snapshot(
    provider: str,
    api_token: str,
    *,
    package_allowance: int | None = None,
    pricing_config: dict | None = None,
) -> ProviderSnapshot:
    return await get_adapter(provider).fetch_snapshot(
        api_token,
        package_allowance=package_allowance,
        pricing_config=pricing_config,
    )


async def fetch_provider_members(
    provider: str,
    api_token: str,
    *,
    pricing_config: dict | None = None,
) -> list[ProviderMember]:
    adapter = get_adapter(provider)
    fetch_members = getattr(adapter, "fetch_members", None)
    if fetch_members is None:
        return []
    return await fetch_members(api_token, pricing_config=pricing_config)


__all__ = [
    "SUPPORTED_PROVIDERS",
    "ProviderAdapter",
    "ProviderMember",
    "ProviderValidationError",
    "ProviderSnapshot",
    "UsageRecord",
    "fetch_provider_members",
    "fetch_provider_snapshot",
    "get_adapter",
    "validate_provider_api_key",
]

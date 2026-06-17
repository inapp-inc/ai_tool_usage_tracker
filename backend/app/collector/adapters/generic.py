"""Generic adapter for custom integrations (Custom, Mabl, Windsurf)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.base import (
    ProviderMember,
    ProviderSnapshot,
    ProviderValidationError,
    UsageRecord,
    resolve_provider_api_url,
)
from app.collector.adapters.http_utils import get_json
from app.collector.adapters.member_parsing import parse_generic_members


class GenericUsageAdapter:
    """Format validation + optional custom validation URL from pricing_config."""

    def __init__(self, provider: str) -> None:
        self.provider = provider

    async def validate_api_key(
        self,
        api_token: str,
        *,
        pricing_config: dict | None = None,
        api_endpoint: str | None = None,
        **_kwargs: object,
    ) -> None:
        if len(api_token.strip()) < 8:
            raise ProviderValidationError("API key must be at least 8 characters.")

        config = pricing_config or {}
        endpoint = api_endpoint or config.get("api_endpoint")
        validate_url = config.get("validate_url")
        if self.provider == "custom" or self.provider not in {
            "mabl",
            "windsurf",
            "openai",
            "anthropic",
            "google",
            "azure_openai",
            "cohere",
            "mistral",
            "cursor",
            "figma",
        }:
            if not endpoint:
                raise ProviderValidationError(
                    f"API endpoint URL is required for provider '{self.provider}'."
                )
            validate_url = endpoint
        elif validate_url is None and endpoint:
            validate_url = endpoint

        if validate_url:
            status, _ = await get_json(
                validate_url,
                headers={"Authorization": f"Bearer {api_token}"},
            )
            if status == 401:
                raise ProviderValidationError("Invalid API key for custom validation URL.")
            if status >= 400:
                raise ProviderValidationError(
                    f"Custom API key validation failed (HTTP {status})."
                )

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        pricing_config: dict | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        del api_token, pricing_config
        until = datetime.now(UTC)
        since = until - timedelta(days=30)
        records = await self.fetch_usage("token", since=since, until=until)
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
            member_count=len(
                await self.fetch_members(api_token, pricing_config=pricing_config)
            ),
        )

    async def fetch_members(
        self,
        api_token: str,
        *,
        pricing_config: dict | None = None,
        **_kwargs: object,
    ) -> list[ProviderMember]:
        members_url = (pricing_config or {}).get("members_url")
        if not members_url:
            return []
        status, payload = await get_json(
            members_url,
            headers={"Authorization": f"Bearer {api_token}"},
        )
        if status != 200:
            return []
        return parse_generic_members(payload)

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
    ) -> list[UsageRecord]:
        del api_token
        midpoint = since + (until - since) / 2
        return [
            UsageRecord(
                vendor_event_id=f"{self.provider}-stub-{midpoint.date()}",
                model="default",
                occurred_at=midpoint,
                input_tokens=3_000,
                output_tokens=900,
                estimated_cost=Decimal("0.012000"),
            )
        ]

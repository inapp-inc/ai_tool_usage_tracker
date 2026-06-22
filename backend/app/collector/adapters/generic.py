"""Generic adapter for config-driven and legacy custom integrations."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.base import (
    ProviderMember,
    ProviderSnapshot,
    ProviderValidationError,
    UsageRecord,
)
from app.collector.adapters.http_utils import get_with_detail
from app.collector.adapters.member_parsing import parse_generic_members
from app.integration.engine import (
    IntegrationConfigError,
    fetch_usage_from_config,
    validate_connection_from_config,
)
from app.integration.http_log import log_provider_http


class GenericUsageAdapter:
    """Validation and usage via integration_config when present; legacy URL probe otherwise."""

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
        integration_config = config.get("integration_config")

        if isinstance(integration_config, dict) and integration_config.get("usage"):
            try:
                await validate_connection_from_config(
                    api_token,
                    integration_config=integration_config,
                    api_endpoint=endpoint,
                    tool_vendor=self.provider,
                    pricing_config=config,
                )
            except IntegrationConfigError as exc:
                raise ProviderValidationError(str(exc)) from exc
            return

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
            result = await get_with_detail(
                validate_url,
                headers={"Authorization": f"Bearer {api_token}"},
            )
            log_provider_http(
                operation="validate",
                method="GET",
                url=validate_url,
                status_code=result.status_code,
                response_body=result.text,
                tool_vendor=self.provider,
            )
            if result.status_code == 401:
                raise ProviderValidationError("Invalid API key for custom validation URL.")
            if result.status_code >= 400:
                raise ProviderValidationError(
                    f"Custom API key validation failed (HTTP {result.status_code}). "
                    "See Docker api logs for the provider response body."
                )

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        pricing_config: dict | None = None,
        api_endpoint: str | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        until = datetime.now(UTC)
        since = until - timedelta(days=30)
        records = await self.fetch_usage(
            api_token,
            since=since,
            until=until,
            pricing_config=pricing_config,
            api_endpoint=api_endpoint,
        )
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
        result = await get_with_detail(
            members_url,
            headers={"Authorization": f"Bearer {api_token}"},
        )
        log_provider_http(
            operation="members",
            method="GET",
            url=members_url,
            status_code=result.status_code,
            response_body=result.text,
            tool_vendor=self.provider,
        )
        if result.status_code != 200:
            return []
        return parse_generic_members(result.json)

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        pricing_config: dict | None = None,
        api_endpoint: str | None = None,
    ) -> list[UsageRecord]:
        config = pricing_config or {}
        integration_config = config.get("integration_config")
        if isinstance(integration_config, dict) and integration_config.get("usage"):
            endpoint = api_endpoint or config.get("api_endpoint")
            try:
                return await fetch_usage_from_config(
                    api_token,
                    integration_config=integration_config,
                    since=since,
                    until=until,
                    api_endpoint=endpoint,
                    tool_vendor=self.provider,
                    pricing_config=config,
                )
            except IntegrationConfigError as exc:
                raise ProviderValidationError(str(exc)) from exc

        del api_token
        logger.info(
            "%s fetch_usage | no config-driven usage; returning empty",
            self.provider,
        )
        return []

    @staticmethod
    def parse_token_rows(
        provider: str,
        rows: list[dict],
        *,
        fallback_at: datetime,
    ) -> list[UsageRecord]:
        from app.normalization.converters import token_to_usage_record
        from app.normalization.token import (
            map_bedrock_usage,
            map_generic_token_usage,
        )

        records: list[UsageRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            if provider == "bedrock":
                normalized = map_bedrock_usage(row, fallback_at=fallback_at)
            else:
                normalized = map_generic_token_usage(
                    row, source=provider.replace("_", " ").title(), fallback_at=fallback_at
                )
            if normalized is not None:
                records.append(token_to_usage_record(normalized))
        return records

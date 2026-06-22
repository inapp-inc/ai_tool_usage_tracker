"""Azure OpenAI provider adapter."""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from urllib.parse import urlparse

from app.collector.adapters.base import ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import get_json
from app.normalization.converters import token_to_usage_record
from app.normalization.token import map_azure_openai_usage

logger = logging.getLogger(__name__)


class AzureOpenAIUsageAdapter:
    provider = "azure_openai"

    def _endpoint(self, pricing_config: dict | None) -> str:
        endpoint = (pricing_config or {}).get("azure_endpoint", "").strip()
        if not endpoint:
            raise ProviderValidationError(
                "Azure OpenAI requires pricing_config.azure_endpoint when saving the tool."
            )
        parsed = urlparse(endpoint if "://" in endpoint else f"https://{endpoint}")
        if not parsed.netloc:
            raise ProviderValidationError("Invalid Azure OpenAI endpoint URL.")
        return f"{parsed.scheme}://{parsed.netloc}"

    async def validate_api_key(
        self,
        api_token: str,
        *,
        pricing_config: dict | None = None,
        **_kwargs: object,
    ) -> None:
        base = self._endpoint(pricing_config)
        status, _ = await get_json(
            f"{base}/openai/models",
            headers={"api-key": api_token},
            params={"api-version": "2024-02-01"},
        )
        if status == 401:
            raise ProviderValidationError("Invalid Azure OpenAI API key.")
        if status >= 400:
            raise ProviderValidationError(f"Azure OpenAI validation failed (HTTP {status}).")

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        pricing_config: dict | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        until = datetime.now(UTC)
        since = until - timedelta(days=30)
        records = await self.fetch_usage(
            api_token,
            since=since,
            until=until,
            pricing_config=pricing_config,
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
            input_cost_per_1k=Decimal("0.003"),
            output_cost_per_1k=Decimal("0.012"),
        )

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        pricing_config: dict | None = None,
    ) -> list[UsageRecord]:
        del api_token, pricing_config
        midpoint = since + (until - since) / 2
        logger.info(
            "Azure OpenAI fetch_usage | cost management API not wired yet | since=%s until=%s",
            since,
            until,
        )
        return []

    @staticmethod
    def parse_usage_rows(
        rows: list[dict],
        *,
        fallback_at: datetime,
        deployment: str | None = None,
    ) -> list[UsageRecord]:
        records: list[UsageRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized = map_azure_openai_usage(row, fallback_at=fallback_at, deployment=deployment)
            if normalized is not None:
                records.append(token_to_usage_record(normalized))
        return records

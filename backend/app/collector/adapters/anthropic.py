"""Anthropic provider adapter."""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.base import ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import get_json
from app.normalization.converters import token_to_usage_record
from app.normalization.token import map_anthropic_usage

logger = logging.getLogger(__name__)


class AnthropicUsageAdapter:
    provider = "anthropic"

    def _headers(self, api_token: str) -> dict[str, str]:
        return {
            "x-api-key": api_token,
            "anthropic-version": "2023-06-01",
        }

    async def validate_api_key(self, api_token: str, **_kwargs: object) -> None:
        status, _ = await get_json(
            "https://api.anthropic.com/v1/models",
            headers=self._headers(api_token),
        )
        if status == 401:
            raise ProviderValidationError("Invalid Anthropic API key.")
        if status >= 400:
            raise ProviderValidationError(f"Anthropic API key validation failed (HTTP {status}).")

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        until = datetime.now(UTC)
        since = until - timedelta(days=30)
        records = await self.fetch_usage(api_token, since=since, until=until)
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
            output_cost_per_1k=Decimal("0.015"),
        )

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
    ) -> list[UsageRecord]:
        del api_token
        # Anthropic admin usage API is org-specific; parse normalized rows when payload is supplied.
        logger.info(
            "Anthropic fetch_usage | no org usage API wired yet | since=%s until=%s",
            since,
            until,
        )
        return []

    @staticmethod
    def parse_usage_rows(rows: list[dict], *, fallback_at: datetime) -> list[UsageRecord]:
        records: list[UsageRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized = map_anthropic_usage(row, fallback_at=fallback_at)
            if normalized is not None:
                records.append(token_to_usage_record(normalized))
        return records

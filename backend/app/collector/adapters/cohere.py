"""Cohere provider adapter."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.base import ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import post_json


class CohereUsageAdapter:
    provider = "cohere"

    async def validate_api_key(self, api_token: str, **_kwargs: object) -> None:
        status, _ = await post_json(
            "https://api.cohere.com/v1/check-api-key",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
        )
        if status == 401:
            raise ProviderValidationError("Invalid Cohere API key.")
        if status >= 400:
            raise ProviderValidationError(f"Cohere API key validation failed (HTTP {status}).")

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
            input_cost_per_1k=Decimal("0.001"),
            output_cost_per_1k=Decimal("0.002"),
        )

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
                vendor_event_id=f"cohere-stub-{midpoint.date()}",
                model="command-r",
                occurred_at=midpoint,
                input_tokens=5_500,
                output_tokens=1_200,
                estimated_cost=Decimal("0.019500"),
            )
        ]

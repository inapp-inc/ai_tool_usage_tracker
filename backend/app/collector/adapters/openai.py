"""OpenAI provider adapter."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.base import ProviderMember, ProviderSnapshot, ProviderValidationError, UsageRecord, resolve_provider_api_url
from app.collector.adapters.http_utils import get_json
from app.collector.adapters.member_parsing import dedupe_members, parse_openai_org_users


class OpenAIUsageAdapter:
    provider = "openai"

    async def validate_api_key(
        self,
        api_token: str,
        *,
        pricing_config: dict | None = None,
        api_endpoint: str | None = None,
        **_kwargs: object,
    ) -> None:
        config = pricing_config or {}
        url = resolve_provider_api_url(
            api_endpoint or config.get("api_endpoint"),
            default_url="https://api.openai.com/v1/models",
        )
        status, _ = await get_json(
            url,
            headers={"Authorization": f"Bearer {api_token}"},
        )
        if status == 401:
            raise ProviderValidationError("Invalid OpenAI API key.")
        if status >= 400:
            raise ProviderValidationError(f"OpenAI API key validation failed (HTTP {status}).")

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
            input_cost_per_1k=Decimal("0.005"),
            output_cost_per_1k=Decimal("0.015"),
            member_count=len(await self.fetch_members(api_token)),
        )

    async def fetch_members(self, api_token: str, **_kwargs: object) -> list[ProviderMember]:
        headers = {"Authorization": f"Bearer {api_token}"}
        members: list[ProviderMember] = []
        after: str | None = None

        for _ in range(10):
            params: dict[str, str | int] = {"limit": 100}
            if after:
                params["after"] = after
            status, payload = await get_json(
                "https://api.openai.com/v1/organization/users",
                headers=headers,
                params=params,
            )
            if status != 200:
                break
            page_members = parse_openai_org_users(payload)
            members.extend(page_members)
            if not isinstance(payload, dict) or not payload.get("has_more"):
                break
            next_after = payload.get("last_id")
            if not isinstance(next_after, str) or not next_after:
                break
            after = next_after

        return dedupe_members(members)

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
    ) -> list[UsageRecord]:
        headers = {"Authorization": f"Bearer {api_token}"}
        params = {
            "start_time": int(since.timestamp()),
            "end_time": int(until.timestamp()),
        }
        status, payload = await get_json(
            "https://api.openai.com/v1/organization/usage/completions",
            headers=headers,
            params=params,
        )
        if status == 200 and isinstance(payload, dict):
            parsed = self._parse_response(payload, since)
            if parsed:
                return parsed
        return []

    def _parse_response(self, payload: dict, since: datetime) -> list[UsageRecord]:
        records: list[UsageRecord] = []
        for index, bucket in enumerate(payload.get("data", [])):
            input_tokens = int(bucket.get("input_tokens", 0))
            output_tokens = int(bucket.get("output_tokens", 0))
            if input_tokens == 0 and output_tokens == 0:
                continue
            records.append(
                UsageRecord(
                    vendor_event_id=str(bucket.get("id", f"openai-{since.date()}-{index}")),
                    model=bucket.get("model"),
                    occurred_at=since,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost=Decimal(str(bucket.get("cost_usd", "0"))),
                )
            )
        return records


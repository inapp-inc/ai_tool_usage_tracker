"""Cursor provider adapter."""

import base64
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.collector.adapters.base import ProviderMember, ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import get_json, post_json
from app.collector.adapters.member_parsing import parse_cursor_members
from app.collector.adapters.usage_parsing import parse_cursor_usage_page

MAX_USAGE_PAGES = 50
DEFAULT_USAGE_PAGE_SIZE = 100


def _basic_auth_headers(api_token: str) -> dict[str, str]:
    encoded = base64.b64encode(f"{api_token}:".encode()).decode("ascii")
    return {"Authorization": f"Basic {encoded}"}


class CursorUsageAdapter:
    provider = "cursor"

    async def validate_api_key(self, api_token: str, **_kwargs: object) -> None:
        bearer_headers = {"Authorization": f"Bearer {api_token}"}
        status, _ = await get_json(
            "https://api.cursor.com/v1/me",
            headers=bearer_headers,
        )
        if status == 200:
            return

        admin_status, _ = await get_json(
            "https://api.cursor.com/teams/members",
            headers=_basic_auth_headers(api_token),
        )
        if admin_status == 401:
            raise ProviderValidationError("Invalid Cursor API key.")
        if admin_status in {200, 403}:
            return

        if status == 401:
            raise ProviderValidationError("Invalid Cursor API key.")
        if status >= 400 and status not in {403, 404}:
            raise ProviderValidationError(f"Cursor API key validation failed (HTTP {status}).")

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
            input_cost_per_1k=Decimal("0.004"),
            output_cost_per_1k=Decimal("0.012"),
            member_count=len(await self.fetch_members(api_token)),
        )

    async def fetch_members(self, api_token: str, **_kwargs: object) -> list[ProviderMember]:
        status, payload = await get_json(
            "https://api.cursor.com/teams/members",
            headers=_basic_auth_headers(api_token),
        )
        if status == 200:
            return parse_cursor_members(payload)

        bearer_status, bearer_payload = await get_json(
            "https://api.cursor.com/v1/me",
            headers={"Authorization": f"Bearer {api_token}"},
        )
        if bearer_status == 200 and isinstance(bearer_payload, dict):
            email = bearer_payload.get("email")
            if isinstance(email, str) and email.strip():
                return [ProviderMember(email=email.strip())]
        return []

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
    ) -> list[UsageRecord]:
        start_ms = int(since.timestamp() * 1000)
        end_ms = int(until.timestamp() * 1000)
        records: list[UsageRecord] = []
        page = 1

        while page <= MAX_USAGE_PAGES:
            status, payload = await post_json(
                "https://api.cursor.com/teams/filtered-usage-events",
                headers={
                    **_basic_auth_headers(api_token),
                    "Content-Type": "application/json",
                },
                json_body={
                    "startDate": start_ms,
                    "endDate": end_ms,
                    "page": page,
                    "pageSize": DEFAULT_USAGE_PAGE_SIZE,
                },
            )
            if status == 401:
                raise ProviderValidationError(
                    "Cursor team admin API key required to pull live usage."
                )
            if status != 200:
                break

            batch, has_next = parse_cursor_usage_page(payload)
            records.extend(batch)
            if not has_next or not batch:
                break
            page += 1

        return records

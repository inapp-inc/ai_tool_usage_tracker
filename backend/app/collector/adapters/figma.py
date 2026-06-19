"""Figma provider adapter — personal access token + team membership sync."""

import logging
from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.base import ProviderMember, ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import get_with_detail
from app.collector.adapters.member_parsing import dedupe_members, parse_figma_members
from app.integration.http_log import log_provider_http

logger = logging.getLogger(__name__)

FIGMA_API_BASE = "https://api.figma.com/v1"


def _figma_headers(api_token: str) -> dict[str, str]:
    return {"X-Figma-Token": api_token.strip()}


class FigmaUsageAdapter:
    provider = "figma"

    async def validate_api_key(self, api_token: str, **_kwargs: object) -> None:
        token = api_token.strip()
        if len(token) < 8:
            raise ProviderValidationError("Figma personal access token must be at least 8 characters.")

        result = await get_with_detail(f"{FIGMA_API_BASE}/me", headers=_figma_headers(token))
        log_provider_http(
            operation="validate",
            method="GET",
            url=f"{FIGMA_API_BASE}/me",
            status_code=result.status_code,
            response_body=result.text,
            tool_vendor="figma",
        )
        if result.status_code in {401, 403}:
            raise ProviderValidationError("Invalid Figma personal access token.")
        if result.status_code >= 400:
            raise ProviderValidationError(f"Figma token validation failed (HTTP {result.status_code}).")

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        members = await self.fetch_members(api_token)
        records = await self.fetch_usage(
            api_token,
            since=datetime.now(UTC),
            until=datetime.now(UTC),
        )
        tokens_used = sum(record.total_tokens for record in records)
        balance = package_allowance
        if package_allowance is not None:
            balance = max(package_allowance - tokens_used, 0)
        return ProviderSnapshot(
            sync_status="active",
            tokens_used=tokens_used,
            balance_tokens=balance,
            total_cost=Decimal("0"),
            member_count=len(members),
        )

    async def fetch_members(self, api_token: str, **_kwargs: object) -> list[ProviderMember]:
        headers = _figma_headers(api_token)
        members: list[ProviderMember] = []

        teams_result = await get_with_detail(f"{FIGMA_API_BASE}/teams", headers=headers)
        log_provider_http(
            operation="teams",
            method="GET",
            url=f"{FIGMA_API_BASE}/teams",
            status_code=teams_result.status_code,
            response_body=teams_result.text,
            tool_vendor="figma",
        )
        if teams_result.status_code == 200 and isinstance(teams_result.json, dict):
            teams = teams_result.json.get("teams", [])
            if isinstance(teams, list):
                for team in teams:
                    if not isinstance(team, dict):
                        continue
                    team_id = team.get("id")
                    if not isinstance(team_id, str) or not team_id.strip():
                        continue
                    members_url = f"{FIGMA_API_BASE}/teams/{team_id.strip()}/members"
                    member_result = await get_with_detail(members_url, headers=headers)
                    log_provider_http(
                        operation="members",
                        method="GET",
                        url=members_url,
                        status_code=member_result.status_code,
                        response_body=member_result.text,
                        tool_vendor="figma",
                    )
                    if member_result.status_code == 200:
                        members.extend(parse_figma_members(member_result.json))

        if members:
            return dedupe_members(members)

        me_result = await get_with_detail(f"{FIGMA_API_BASE}/me", headers=headers)
        log_provider_http(
            operation="me",
            method="GET",
            url=f"{FIGMA_API_BASE}/me",
            status_code=me_result.status_code,
            response_body=me_result.text,
            tool_vendor="figma",
        )
        if me_result.status_code == 200 and isinstance(me_result.json, dict):
            email = me_result.json.get("email")
            if isinstance(email, str) and email.strip():
                return [
                    ProviderMember(
                        email=email.strip(),
                        name=me_result.json.get("handle")
                        if isinstance(me_result.json.get("handle"), str)
                        else None,
                    )
                ]
        return []

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
        **_kwargs: object,
    ) -> list[UsageRecord]:
        """Figma has no token-usage API — record one seat per team member for billing visibility."""
        members = await self.fetch_members(api_token)
        if not members:
            logger.info("Figma fetch_usage | no members returned from Figma API")
            return []

        occurred_at = until if until.tzinfo else until.replace(tzinfo=UTC)
        day_key = occurred_at.astimezone(UTC).strftime("%Y-%m-%d")
        records: list[UsageRecord] = []
        for index, member in enumerate(members):
            records.append(
                UsageRecord(
                    vendor_event_id=f"figma-seat-{day_key}-{member.email}-{index}",
                    model="figma-seat",
                    occurred_at=occurred_at,
                    input_tokens=1,
                    output_tokens=0,
                    estimated_cost=Decimal("0"),
                    user_email=member.email,
                    user_name=member.name,
                )
            )
        logger.info("Figma fetch_usage | ingested %s seat records for %s members", len(records), len(members))
        return records

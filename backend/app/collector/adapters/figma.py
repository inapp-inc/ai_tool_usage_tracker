"""Figma provider adapter — personal access token + team membership sync."""

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.base import ProviderMember, ProviderSnapshot, ProviderValidationError, UsageRecord
from app.collector.adapters.http_utils import get_json
from app.collector.adapters.member_parsing import dedupe_members, parse_figma_members

FIGMA_API_BASE = "https://api.figma.com/v1"


def _figma_headers(api_token: str) -> dict[str, str]:
    return {"X-Figma-Token": api_token.strip()}


class FigmaUsageAdapter:
    provider = "figma"

    async def validate_api_key(self, api_token: str, **_kwargs: object) -> None:
        token = api_token.strip()
        if len(token) < 8:
            raise ProviderValidationError("Figma personal access token must be at least 8 characters.")

        status, _ = await get_json(f"{FIGMA_API_BASE}/me", headers=_figma_headers(token))
        if status in {401, 403}:
            raise ProviderValidationError("Invalid Figma personal access token.")
        if status >= 400:
            raise ProviderValidationError(f"Figma token validation failed (HTTP {status}).")

    async def fetch_snapshot(
        self,
        api_token: str,
        *,
        package_allowance: int | None = None,
        **_kwargs: object,
    ) -> ProviderSnapshot:
        members = await self.fetch_members(api_token)
        balance = package_allowance
        return ProviderSnapshot(
            sync_status="active",
            tokens_used=0,
            balance_tokens=balance,
            total_cost=Decimal("0"),
            member_count=len(members),
        )

    async def fetch_members(self, api_token: str, **_kwargs: object) -> list[ProviderMember]:
        headers = _figma_headers(api_token)
        members: list[ProviderMember] = []

        teams_status, teams_payload = await get_json(f"{FIGMA_API_BASE}/teams", headers=headers)
        if teams_status == 200 and isinstance(teams_payload, dict):
            teams = teams_payload.get("teams", [])
            if isinstance(teams, list):
                for team in teams:
                    if not isinstance(team, dict):
                        continue
                    team_id = team.get("id")
                    if not isinstance(team_id, str) or not team_id.strip():
                        continue
                    member_status, member_payload = await get_json(
                        f"{FIGMA_API_BASE}/teams/{team_id.strip()}/members",
                        headers=headers,
                    )
                    if member_status == 200:
                        members.extend(parse_figma_members(member_payload))

        if members:
            return dedupe_members(members)

        me_status, me_payload = await get_json(f"{FIGMA_API_BASE}/me", headers=headers)
        if me_status == 200 and isinstance(me_payload, dict):
            email = me_payload.get("email")
            handle = me_payload.get("handle")
            if isinstance(email, str) and email.strip():
                return [
                    ProviderMember(
                        email=email.strip(),
                        name=handle.strip() if isinstance(handle, str) and handle.strip() else None,
                    )
                ]
        return []

    async def fetch_usage(
        self,
        api_token: str,
        *,
        since: datetime,
        until: datetime,
    ) -> list[UsageRecord]:
        del api_token, since, until
        # Figma has no token-usage API; seat-based billing is tracked via member sync.
        return []

"""Fetch provider token members for tools assigned to a team."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.collector.adapters.registry import fetch_provider_members
from app.core.token_crypto import decrypt_token
from app.models.admin import Team, Tool
from app.teams.repository import TeamRepository
from app.tools.repository import ToolRepository


@dataclass(frozen=True)
class ToolMemberEntry:
    email: str
    name: str | None
    tool_id: UUID
    tool_name: str


async def fetch_tool_members_for_team(
    session: AsyncSession,
    team: Team,
) -> list[ToolMemberEntry]:
    tool_ids_raw = team.tool_ids if isinstance(team.tool_ids, list) else []
    if not tool_ids_raw:
        return []

    tools_repo = ToolRepository(session)
    entries: list[ToolMemberEntry] = []
    seen_emails: set[str] = set()

    for raw_tool_id in tool_ids_raw:
        try:
            tool_uuid = UUID(str(raw_tool_id))
        except ValueError:
            continue

        tool = await tools_repo.get_by_id(tool_uuid, team.organization_id)
        if tool is None or not tool.active:
            continue

        pricing_config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
        try:
            api_key = decrypt_token(tool.api_token_ciphertext)
            provider_members = await fetch_provider_members(
                tool.vendor,
                api_key,
                pricing_config=pricing_config,
            )
        except Exception:  # noqa: BLE001 — skip tools that fail provider pull
            continue

        for member in provider_members:
            email = member.email.strip().lower()
            if not email or email in seen_emails:
                continue
            seen_emails.add(email)
            entries.append(
                ToolMemberEntry(
                    email=member.email.strip(),
                    name=member.name,
                    tool_id=tool.id,
                    tool_name=tool.name,
                )
            )

    entries.sort(key=lambda row: row.email.lower())
    return entries

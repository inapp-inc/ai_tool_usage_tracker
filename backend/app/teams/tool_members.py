"""Fetch provider token members for tools assigned to a team."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.collector.adapters.registry import fetch_provider_members
from app.core.token_crypto import decrypt_token
from app.models.admin import Team
from app.teams.team_tool_repository import TeamToolRepository
from app.tools.catalogue import (
    catalogue_tool_id_from_connected,
    connected_to_catalogue_map,
)
from app.tools.repository import ToolRepository
from app.tools.synced_members import read_synced_members


@dataclass(frozen=True)
class ToolMemberEntry:
    email: str
    name: str | None
    tool_id: UUID
    tool_name: str


async def _team_catalogue_tool_ids(session: AsyncSession, team: Team) -> set[UUID]:
    ids: set[UUID] = set()
    raw_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
    for raw in raw_ids:
        try:
            ids.add(UUID(str(raw)))
        except ValueError:
            continue

    team_tools = TeamToolRepository(session)
    for assignment in await team_tools.list_by_team(team.id):
        ids.add(assignment.tool_id)

    if not ids:
        return set()

    tools_repo = ToolRepository(session)
    org_tools = await tools_repo.list_by_organization(team.organization_id, active=None)
    id_to_catalogue = connected_to_catalogue_map(org_tools)
    return {id_to_catalogue.get(tool_id, tool_id) for tool_id in ids}


async def _members_for_connected_tool(
    connected,
    *,
    catalogue_tool,
) -> list:
    cached = read_synced_members(connected)
    if cached:
        return cached

    pricing_config = (
        dict(connected.pricing_config) if isinstance(connected.pricing_config, dict) else {}
    )
    api_key = decrypt_token(connected.api_token_ciphertext)
    if not api_key:
        return []

    try:
        return await fetch_provider_members(
            connected.vendor,
            api_key,
            pricing_config=pricing_config,
            api_endpoint=connected.api_endpoint,
        )
    except Exception:  # noqa: BLE001 — fall back to empty when live pull fails
        return []


async def fetch_tool_members_for_team(
    session: AsyncSession,
    team: Team,
) -> list[ToolMemberEntry]:
    tools_repo = ToolRepository(session)
    catalogue_tool_ids = await _team_catalogue_tool_ids(session, team)
    connected_tools = await tools_repo.list_connected_for_team(
        team.organization_id,
        team_id=team.id,
        catalogue_tool_ids=catalogue_tool_ids,
    )
    if not connected_tools and catalogue_tool_ids:
        org_tools = await tools_repo.list_by_organization(team.organization_id, active=None)
        id_to_catalogue = connected_to_catalogue_map(org_tools)
        for tool in org_tools:
            if tool.catalogue_only or not tool.active:
                continue
            catalogue_id = catalogue_tool_id_from_connected(tool)
            if catalogue_id is None or catalogue_id not in catalogue_tool_ids:
                continue
            connected_tools.append(tool)
        connected_tools = sorted(
            {tool.id: tool for tool in connected_tools}.values(),
            key=lambda row: (row.name or "").lower(),
        )

    entries: list[ToolMemberEntry] = []
    seen_emails: set[str] = set()

    for connected in connected_tools:
        catalogue_id = catalogue_tool_id_from_connected(connected)
        catalogue_tool = (
            await tools_repo.get_by_id(catalogue_id, team.organization_id)
            if catalogue_id is not None
            else None
        )
        display_tool_id = catalogue_id or connected.id
        display_tool_name = (
            catalogue_tool.name if catalogue_tool is not None else connected.name
        )

        provider_members = await _members_for_connected_tool(
            connected,
            catalogue_tool=catalogue_tool,
        )
        for member in provider_members:
            email = member.email.strip().lower()
            if not email or email in seen_emails:
                continue
            seen_emails.add(email)
            entries.append(
                ToolMemberEntry(
                    email=member.email.strip(),
                    name=member.name,
                    tool_id=display_tool_id,
                    tool_name=display_tool_name,
                )
            )

    entries.sort(key=lambda row: row.email.lower())
    return entries

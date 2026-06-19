"""Delete data associated with a team before removing the team row."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.admin import Team
from app.models.reporting import ReportJob
from app.tools.repository import ToolRepository

logger = logging.getLogger(__name__)


def _catalogue_tool_ids(team: Team) -> set[UUID]:
    ids: set[UUID] = set()
    raw_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
    for item in raw_ids:
        try:
            ids.add(UUID(str(item)))
        except ValueError:
            continue
    return ids


async def delete_connected_credentials_for_team(
    session: AsyncSession,
    *,
    organization_id: UUID,
    team: Team,
) -> int:
    """Remove connected credential tools (and their collectors) linked to the team."""
    tools = ToolRepository(session)
    connected = await tools.list_connected_for_team(
        organization_id,
        team_id=team.id,
        catalogue_tool_ids=_catalogue_tool_ids(team),
    )
    for tool in connected:
        await tools.delete(tool)
    if connected:
        logger.info(
            "Deleted %s connected credential(s) for team %s",
            len(connected),
            team.id,
        )
    return len(connected)


async def remove_team_from_report_jobs(
    session: AsyncSession,
    *,
    organization_id: UUID,
    team_id: UUID,
) -> int:
    """Drop deleted team id from report job filters (JSON team_ids array)."""
    team_id_str = str(team_id)
    result = await session.execute(
        select(ReportJob).where(ReportJob.organization_id == organization_id)
    )
    updated = 0
    for job in result.scalars().all():
        team_ids = job.team_ids if isinstance(job.team_ids, list) else []
        filtered = [value for value in team_ids if str(value) != team_id_str]
        if len(filtered) != len(team_ids):
            job.team_ids = filtered
            flag_modified(job, "team_ids")
            updated += 1
    return updated

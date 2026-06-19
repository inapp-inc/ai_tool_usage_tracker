"""Helpers when removing a team row (usage/uploads cascade via DB FKs)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.reporting import ReportJob


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

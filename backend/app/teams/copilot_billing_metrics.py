"""Sum Copilot billing CSV import costs for team list metrics."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.billing_totals import (
    compute_copilot_billed_split_from_parsed,
    totals_from_upload_ids,
)
from app.models.admin import TeamTool, Tool
from app.models.copilot import CopilotBillingImport
from app.models.ingestion import Upload
from app.teams.team_tool_repository import TeamToolRepository


def copilot_import_overlaps_period(
    from_date: date,
    to_date: date,
):
    """SQLAlchemy filter: billing import counts toward a date window."""
    return or_(
        and_(
            CopilotBillingImport.billing_period_start.isnot(None),
            CopilotBillingImport.billing_period_start <= to_date,
            or_(
                CopilotBillingImport.billing_period_end.is_(None),
                CopilotBillingImport.billing_period_end >= from_date,
            ),
        ),
        and_(
            CopilotBillingImport.billing_period_start.is_(None),
            Upload.billing_period_start.isnot(None),
            Upload.billing_period_start <= to_date,
            or_(
                Upload.billing_period_end.is_(None),
                Upload.billing_period_end >= from_date,
            ),
        ),
        and_(
            CopilotBillingImport.billing_period_start.is_(None),
            Upload.billing_period_start.is_(None),
            func.date(CopilotBillingImport.imported_at) >= from_date,
            func.date(CopilotBillingImport.imported_at) <= to_date,
        ),
    )


def active_upload_filter():
    return or_(Upload.deleted_at.is_(None), Upload.id.is_(None))


async def sum_copilot_import_cost_by_team(
    session: AsyncSession,
    organization_id: UUID,
    team_ids: list[UUID],
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> dict[UUID, Decimal]:
    split = await copilot_import_split_by_team(
        session,
        organization_id,
        team_ids,
        from_dt=from_dt,
        to_dt=to_dt,
    )
    return {
        team_id: subscription + additional
        for team_id, (subscription, additional) in split.items()
    }


async def copilot_import_split_by_team(
    session: AsyncSession,
    organization_id: UUID,
    team_ids: list[UUID],
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> dict[UUID, tuple[Decimal, Decimal]]:
    """Return configured subscription and additional billable Copilot spend per team."""
    if not team_ids:
        return {}

    stmt = (
        select(CopilotBillingImport.team_id, CopilotBillingImport.upload_id)
        .outerjoin(Upload, CopilotBillingImport.upload_id == Upload.id)
        .where(
            CopilotBillingImport.organization_id == organization_id,
            CopilotBillingImport.team_id.in_(team_ids),
            active_upload_filter(),
            CopilotBillingImport.upload_id.isnot(None),
        )
    )

    if from_dt is not None and to_dt is not None:
        from_date = from_dt.date() if isinstance(from_dt, datetime) else from_dt
        to_date = to_dt.date() if isinstance(to_dt, datetime) else to_dt
        stmt = stmt.where(copilot_import_overlaps_period(from_date, to_date))

    result = await session.execute(stmt)

    uploads_by_team: dict[UUID, set[UUID]] = {}
    for team_id, upload_id in result.all():
        if team_id is None or upload_id is None:
            continue
        uploads_by_team.setdefault(team_id, set()).add(upload_id)

    split_by_team: dict[UUID, tuple[Decimal, Decimal]] = {}
    team_tools = TeamToolRepository(session)
    for team_id, upload_ids in uploads_by_team.items():
        parsed = await totals_from_upload_ids(session, list(upload_ids))
        assignment = await _copilot_assignment_for_team(session, team_tools, team_id)
        from app.copilot.service import CopilotAnalyticsService

        _, _, configured_subscription, _ = CopilotAnalyticsService._configured_copilot_pricing(
            assignment
        )
        subscription, additional, _total = compute_copilot_billed_split_from_parsed(
            parsed,
            configured_subscription,
        )
        split_by_team[team_id] = (subscription, additional)
    return split_by_team


async def _copilot_assignment_for_team(
    session: AsyncSession,
    team_tools: TeamToolRepository,
    team_id: UUID,
):
    result = await session.execute(
        select(TeamTool)
        .join(Tool, TeamTool.tool_id == Tool.id)
        .where(TeamTool.team_id == team_id, Tool.vendor == "copilot")
        .limit(1)
    )
    return result.scalar_one_or_none()


def month_bounds(value: date) -> tuple[date, date]:
    last_day = calendar.monthrange(value.year, value.month)[1]
    return value.replace(day=1), value.replace(day=last_day)

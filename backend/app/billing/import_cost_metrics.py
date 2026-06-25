"""Sum billing CSV import costs for threshold evaluation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.copilot import CopilotBillingImport
from app.models.figma import FigmaBillingImport
from app.models.ingestion import Upload
from app.teams.copilot_billing_metrics import (
    active_upload_filter,
    copilot_import_overlaps_period,
)
from app.teams.figma_billing_metrics import figma_import_overlaps_period


async def sum_import_billing_cost(
    session: AsyncSession,
    *,
    organization_id: UUID,
    team_id: UUID,
    tool_id: UUID,
    from_date: date,
    to_date: date,
) -> Decimal:
    """Total imported billing cost (Copilot + Figma) for a team/tool in a date window."""
    copilot_total = await _sum_copilot_import_cost(
        session,
        organization_id=organization_id,
        team_id=team_id,
        tool_id=tool_id,
        from_date=from_date,
        to_date=to_date,
    )
    figma_total = await _sum_figma_import_cost(
        session,
        organization_id=organization_id,
        team_id=team_id,
        tool_id=tool_id,
        from_date=from_date,
        to_date=to_date,
    )
    return copilot_total + figma_total


async def _sum_copilot_import_cost(
    session: AsyncSession,
    *,
    organization_id: UUID,
    team_id: UUID,
    tool_id: UUID,
    from_date: date,
    to_date: date,
) -> Decimal:
    stmt = (
        select(func.coalesce(func.sum(CopilotBillingImport.total_cost), 0))
        .outerjoin(Upload, CopilotBillingImport.upload_id == Upload.id)
        .where(
            CopilotBillingImport.organization_id == organization_id,
            CopilotBillingImport.team_id == team_id,
            CopilotBillingImport.tool_id == tool_id,
            active_upload_filter(),
        )
    )
    stmt = stmt.where(copilot_import_overlaps_period(from_date, to_date))
    result = await session.execute(stmt)
    return Decimal(str(result.scalar_one() or 0))


async def _sum_figma_import_cost(
    session: AsyncSession,
    *,
    organization_id: UUID,
    team_id: UUID,
    tool_id: UUID,
    from_date: date,
    to_date: date,
) -> Decimal:
    stmt = (
        select(func.coalesce(func.sum(FigmaBillingImport.total_cost), 0))
        .outerjoin(Upload, FigmaBillingImport.upload_id == Upload.id)
        .where(
            FigmaBillingImport.organization_id == organization_id,
            FigmaBillingImport.team_id == team_id,
            FigmaBillingImport.tool_id == tool_id,
            active_upload_filter(),
        )
    )
    stmt = stmt.where(figma_import_overlaps_period(from_date, to_date))
    result = await session.execute(stmt)
    return Decimal(str(result.scalar_one() or 0))

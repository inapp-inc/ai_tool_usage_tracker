"""Sum Figma billing CSV import costs for team list metrics."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.figma import FigmaBillingImport
from app.models.ingestion import Upload


def figma_import_overlaps_period(from_date: date, to_date: date):
    """SQLAlchemy filter: Figma billing import counts toward a date window."""
    return or_(
        and_(
            FigmaBillingImport.usage_period_start.isnot(None),
            FigmaBillingImport.usage_period_start <= to_date,
            or_(
                FigmaBillingImport.usage_period_end.is_(None),
                FigmaBillingImport.usage_period_end >= from_date,
            ),
        ),
        and_(
            FigmaBillingImport.usage_period_start.is_(None),
            func.date(FigmaBillingImport.imported_at) >= from_date,
            func.date(FigmaBillingImport.imported_at) <= to_date,
        ),
    )


def active_upload_filter():
    return or_(Upload.deleted_at.is_(None), Upload.id.is_(None))


async def sum_figma_import_cost_by_team(
    session: AsyncSession,
    organization_id: UUID,
    team_ids: list[UUID],
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> dict[UUID, Decimal]:
    if not team_ids:
        return {}

    stmt = (
        select(
            FigmaBillingImport.team_id,
            func.coalesce(func.sum(FigmaBillingImport.total_cost), 0),
        )
        .outerjoin(Upload, FigmaBillingImport.upload_id == Upload.id)
        .where(
            FigmaBillingImport.organization_id == organization_id,
            FigmaBillingImport.team_id.in_(team_ids),
            active_upload_filter(),
        )
        .group_by(FigmaBillingImport.team_id)
    )

    if from_dt is not None and to_dt is not None:
        from_date = from_dt.date() if isinstance(from_dt, datetime) else from_dt
        to_date = to_dt.date() if isinstance(to_dt, datetime) else to_dt
        stmt = stmt.where(figma_import_overlaps_period(from_date, to_date))

    result = await session.execute(stmt)
    return {team_id: Decimal(str(total or 0)) for team_id, total in result.all()}

"""Shared usage aggregation queries."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collector import UsageEvent
from app.usage.cost import usage_event_effective_cost_sql


async def sum_tokens_and_cost_by_team(
    session: AsyncSession,
    organization_id: UUID,
    team_ids: list[UUID],
    from_dt: datetime,
    to_dt: datetime,
) -> dict[UUID, tuple[int, Decimal]]:
    """Sum tokens and recorded cost per team for the period."""
    if not team_ids:
        return {}

    result = await session.execute(
        select(
            UsageEvent.team_id,
            func.coalesce(func.sum(UsageEvent.total_tokens), 0),
            func.coalesce(func.sum(usage_event_effective_cost_sql()), 0),
        )
        .where(
            UsageEvent.organization_id == organization_id,
            UsageEvent.team_id.in_(team_ids),
            UsageEvent.occurred_at >= from_dt,
            UsageEvent.occurred_at <= to_dt,
        )
        .group_by(UsageEvent.team_id)
    )
    return {
        team_id: (int(tokens), Decimal(str(cost)))
        for team_id, tokens, cost in result.all()
        if team_id is not None
    }


async def sum_org_cost(
    session: AsyncSession,
    organization_id: UUID,
    from_dt: datetime,
    to_dt: datetime,
    *,
    team_id: UUID | None = None,
    tool_ids: list[UUID] | None = None,
) -> Decimal:
    """Sum recorded estimated_cost for the org in the period."""
    conditions = [
        UsageEvent.organization_id == organization_id,
        UsageEvent.occurred_at >= from_dt,
        UsageEvent.occurred_at <= to_dt,
    ]
    if team_id is not None:
        conditions.append(UsageEvent.team_id == team_id)
    if tool_ids:
        conditions.append(UsageEvent.tool_id.in_(tool_ids))

    result = await session.execute(
        select(func.coalesce(func.sum(usage_event_effective_cost_sql()), 0)).where(*conditions)
    )
    return Decimal(str(result.scalar_one()))

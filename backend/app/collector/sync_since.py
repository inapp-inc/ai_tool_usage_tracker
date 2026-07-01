"""Resolve usage pull windows for first connect and incremental sync."""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import TeamTool, Tool
from app.models.collector import CollectorConfig, CollectorRun, UsageEvent
from app.tools.catalogue import catalogue_tool_id_from_connected, team_id_from_connected

SYNC_LOOKBACK_DAYS = 30
INITIAL_SYNC_MAX_DAYS = 365
CURSOR_HISTORY_DAYS = 90


def billing_period_start(until: datetime) -> datetime:
    """Start of the calendar month containing ``until`` (UTC)."""
    if until.tzinfo is None:
        until = until.replace(tzinfo=UTC)
    return until.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def earliest_subscription_start(session: AsyncSession, tool: Tool) -> date | None:
    catalogue_id = catalogue_tool_id_from_connected(tool) or tool.id
    result = await session.execute(
        select(func.min(TeamTool.subscription_start)).where(
            TeamTool.tool_id == catalogue_id,
            TeamTool.subscription_start.isnot(None),
        )
    )
    value = result.scalar_one_or_none()
    return value if isinstance(value, date) else None


async def resolve_initial_sync_since(
    session: AsyncSession,
    tool: Tool,
    until: datetime,
) -> datetime:
    """First pull: from billing month start, subscription start, or credential created."""
    if until.tzinfo is None:
        until = until.replace(tzinfo=UTC)

    candidates: list[datetime] = [
        billing_period_start(until),
        until - timedelta(days=CURSOR_HISTORY_DAYS),
    ]

    if tool.created_at is not None:
        created = tool.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        candidates.append(created)

    subscription_start = await earliest_subscription_start(session, tool)
    if subscription_start is not None:
        candidates.append(datetime.combine(subscription_start, time.min, tzinfo=UTC))

    since = min(candidates)
    floor = until - timedelta(days=INITIAL_SYNC_MAX_DAYS)
    return max(since, floor)


def _usage_scope_tool_ids(tool: Tool) -> set[UUID]:
    tool_ids: set[UUID] = {tool.id}
    catalogue_id = catalogue_tool_id_from_connected(tool)
    if catalogue_id is not None:
        tool_ids.add(catalogue_id)
    return tool_ids


def _usage_scope_conditions(tool: Tool) -> list:
    """Scope usage history to this credential's team when assigned."""
    conditions = [
        UsageEvent.provider == tool.vendor,
        UsageEvent.organization_id == tool.organization_id,
        UsageEvent.tool_id.in_(_usage_scope_tool_ids(tool)),
    ]
    team_id = team_id_from_connected(tool)
    if team_id is not None:
        conditions.append(UsageEvent.team_id == team_id)
    return conditions


async def _collector_has_successful_ingest(session: AsyncSession, tool: Tool) -> bool:
    """True once this connected credential's collector has ingested usage rows."""
    result = await session.execute(
        select(CollectorRun.id)
        .join(CollectorConfig, CollectorConfig.id == CollectorRun.collector_id)
        .where(
            CollectorConfig.tool_id == tool.id,
            CollectorRun.status == "success",
            CollectorRun.records_ingested > 0,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def resolve_usage_sync_since(
    session: AsyncSession,
    tool: Tool,
    until: datetime,
    *,
    lookback_days: int = SYNC_LOOKBACK_DAYS,
) -> datetime:
    """Incremental overlap from last event, or full initial window on first connect."""
    if until.tzinfo is None:
        until = until.replace(tzinfo=UTC)

    if not await _collector_has_successful_ingest(session, tool):
        return await resolve_initial_sync_since(session, tool, until)

    scope = _usage_scope_conditions(tool)

    result = await session.execute(
        select(func.max(UsageEvent.occurred_at)).where(*scope)
    )
    latest = result.scalar_one_or_none()
    if latest is None:
        return await resolve_initial_sync_since(session, tool, until)

    initial_since = await resolve_initial_sync_since(session, tool, until)
    earliest_result = await session.execute(
        select(func.min(UsageEvent.occurred_at)).where(*scope)
    )
    earliest = earliest_result.scalar_one_or_none()
    if earliest is not None:
        if earliest.tzinfo is None:
            earliest = earliest.replace(tzinfo=UTC)
        if earliest > initial_since + timedelta(hours=1):
            return initial_since

    overlap = timedelta(hours=1)
    incremental_since = latest - overlap
    if incremental_since.tzinfo is None:
        incremental_since = incremental_since.replace(tzinfo=UTC)
    lookback_start = until - timedelta(days=lookback_days)
    return max(incremental_since, lookback_start)

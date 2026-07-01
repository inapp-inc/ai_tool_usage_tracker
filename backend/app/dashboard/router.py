"""Dashboard REST API — usage insights and widgets."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.org_scope import get_operating_org_scope, OperatingOrgScope
from app.core.permissions import require_permission, require_super_admin
from app.dashboard.schemas import (
    ActiveAlertsResponse,
    ActiveCountsWidget,
    CostOverviewWidget,
    DailyBreakdownResponse,
    MyUsageResponse,
    OrganizationCostBreakdownResponse,
    OrganizationCostSummary,
    TokenUsageWidget,
    TopConsumersResponse,
    TrendGranularityApi,
    TrendsResponse,
    UsageByTeamResponse,
    UsageByToolResponse,
)
from app.dashboard.scope import resolve_dashboard_scope
from app.dashboard.service import DashboardService
from app.db.session import get_session
from app.models.auth import User
from app.teams.metrics import ALL_TIME_FROM, ALL_TIME_TO

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(session: AsyncSession = Depends(get_session)) -> DashboardService:
    return DashboardService(session)


def _parse_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


@router.get("/tokens", response_model=TokenUsageWidget)
async def get_dashboard_tokens(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    team_id: UUID | None = None,
    tool_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> TokenUsageWidget:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_tokens(
        scope,
        _parse_datetime(from_dt),
        _parse_datetime(to_dt),
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get("/cost", response_model=CostOverviewWidget)
async def get_dashboard_cost(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    team_id: UUID | None = None,
    tool_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> CostOverviewWidget:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_cost(
        scope,
        _parse_datetime(from_dt),
        _parse_datetime(to_dt),
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get("/organization-costs", response_model=OrganizationCostSummary)
async def get_dashboard_organization_costs(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    team_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> OrganizationCostSummary:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_organization_cost_summary(
        scope,
        _parse_datetime(from_dt),
        _parse_datetime(to_dt),
    )


@router.get("/organization-costs/breakdown", response_model=OrganizationCostBreakdownResponse)
async def get_dashboard_organization_cost_breakdown(
    all_time: bool = Query(False),
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    _current_user: User = Depends(require_super_admin()),
    service: DashboardService = Depends(get_dashboard_service),
) -> OrganizationCostBreakdownResponse:
    if all_time:
        window_from, window_to = ALL_TIME_FROM, ALL_TIME_TO
    else:
        window_from = _parse_datetime(from_dt)  # type: ignore[arg-type]
        window_to = _parse_datetime(to_dt)  # type: ignore[arg-type]
    return await service.get_organization_cost_breakdown(window_from, window_to)


@router.get("/active-counts", response_model=ActiveCountsWidget)
async def get_dashboard_active_counts(
    team_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> ActiveCountsWidget:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_active_counts(scope, team_id=team_id)


@router.get("/usage-by-tool", response_model=UsageByToolResponse)
async def get_dashboard_usage_by_tool(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    team_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> UsageByToolResponse:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_usage_by_tool(
        scope,
        _parse_datetime(from_dt),
        _parse_datetime(to_dt),
        team_id=team_id,
    )


@router.get("/usage-by-team", response_model=UsageByTeamResponse)
async def get_dashboard_usage_by_team(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    team_id: UUID | None = None,
    tool_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> UsageByTeamResponse:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_usage_by_team(
        scope,
        _parse_datetime(from_dt),
        _parse_datetime(to_dt),
        tool_id=tool_id,
    )


@router.get("/top-consumers", response_model=TopConsumersResponse)
async def get_dashboard_top_consumers(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    limit: int = Query(default=10, ge=1, le=50),
    entity: str = Query(default="users"),
    team_id: UUID | None = None,
    tool_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> TopConsumersResponse:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_top_consumers(
        scope,
        _parse_datetime(from_dt),
        _parse_datetime(to_dt),
        limit=limit,
        entity=entity,
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get("/alerts", response_model=ActiveAlertsResponse)
async def get_dashboard_alerts(
    team_id: UUID | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> ActiveAlertsResponse:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_alerts(scope, team_id=team_id, limit=limit)


@router.get("/trends", response_model=TrendsResponse)
async def get_dashboard_trends(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    granularity: TrendGranularityApi = Query(),
    team_id: UUID | None = None,
    tool_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> TrendsResponse:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_trends(
        scope,
        _parse_datetime(from_dt),
        _parse_datetime(to_dt),
        granularity,
        team_id=team_id,
        tool_id=tool_id,
    )


# my-usage stays open to all authenticated users — it only returns the caller's own data
@router.get("/my-usage", response_model=MyUsageResponse)
async def get_dashboard_my_usage(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    user_id: UUID | None = None,
    current_user: User = Depends(require_permission("my_usage", "read")),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> MyUsageResponse:
    scope = await resolve_dashboard_scope(session, current_user)
    return await service.get_my_usage(
        scope,
        _parse_datetime(from_dt),
        _parse_datetime(to_dt),
        user_id=user_id,
    )


@router.get("/daily-breakdown", response_model=DailyBreakdownResponse)
async def get_dashboard_daily_breakdown(
    date: datetime = Query(description="Calendar day (ISO 8601)"),
    team_id: UUID | None = None,
    tool_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    org_scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: DashboardService = Depends(get_dashboard_service),
) -> DailyBreakdownResponse:
    scope = await resolve_dashboard_scope(
        session,
        current_user,
        team_id=team_id,
        org_scope=org_scope,
    )
    return await service.get_daily_breakdown(
        scope,
        _parse_datetime(date),
        team_id=team_id,
        tool_id=tool_id,
    )

"""Dashboard API routes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.service import AuthenticatedUser
from app.dashboard.service import DashboardService
from app.db.session import get_session

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _parse_period(
    from_value: datetime,
    to_value: datetime,
) -> tuple[datetime, datetime]:
    start = from_value if from_value.tzinfo else from_value.replace(tzinfo=UTC)
    end = to_value if to_value.tzinfo else to_value.replace(tzinfo=UTC)
    return start, end


@router.get("/summary", summary="Insights summary stats")
async def get_dashboard_summary(
    from_value: Annotated[datetime, Query(alias="from")],
    to_value: Annotated[datetime, Query(alias="to")],
    team_id: uuid.UUID | None = None,
    tool_id: uuid.UUID | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = DashboardService(session)
    start, end = _parse_period(from_value, to_value)
    return await service.get_summary(
        current_user,
        from_dt=start,
        to_dt=end,
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get("/tokens", summary="Total token usage widget", operation_id="getDashboardTokens")
async def get_dashboard_tokens(
    from_value: Annotated[datetime, Query(alias="from")],
    to_value: Annotated[datetime, Query(alias="to")],
    team_id: uuid.UUID | None = None,
    tool_id: uuid.UUID | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = DashboardService(session)
    start, end = _parse_period(from_value, to_value)
    return await service.get_tokens_widget(
        current_user,
        from_dt=start,
        to_dt=end,
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get("/cost", summary="Cost overview widget", operation_id="getDashboardCost")
async def get_dashboard_cost(
    from_value: Annotated[datetime, Query(alias="from")],
    to_value: Annotated[datetime, Query(alias="to")],
    team_id: uuid.UUID | None = None,
    tool_id: uuid.UUID | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = DashboardService(session)
    start, end = _parse_period(from_value, to_value)
    return await service.get_cost_widget(
        current_user,
        from_dt=start,
        to_dt=end,
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get(
    "/usage-by-tool",
    summary="Usage by tool widget",
    operation_id="getDashboardUsageByTool",
)
async def get_usage_by_tool(
    from_value: Annotated[datetime, Query(alias="from")],
    to_value: Annotated[datetime, Query(alias="to")],
    team_id: uuid.UUID | None = None,
    tool_id: uuid.UUID | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = DashboardService(session)
    start, end = _parse_period(from_value, to_value)
    return await service.get_usage_by_tool(
        current_user,
        from_dt=start,
        to_dt=end,
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get(
    "/usage-by-team",
    summary="Usage by team widget",
    operation_id="getDashboardUsageByTeam",
)
async def get_usage_by_team(
    from_value: Annotated[datetime, Query(alias="from")],
    to_value: Annotated[datetime, Query(alias="to")],
    team_id: uuid.UUID | None = None,
    tool_id: uuid.UUID | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = DashboardService(session)
    start, end = _parse_period(from_value, to_value)
    return await service.get_usage_by_team(
        current_user,
        from_dt=start,
        to_dt=end,
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get(
    "/top-consumers",
    summary="Top consumers widget",
    operation_id="getDashboardTopConsumers",
)
async def get_top_consumers(
    from_value: Annotated[datetime, Query(alias="from")],
    to_value: Annotated[datetime, Query(alias="to")],
    limit: int = Query(default=10, ge=1, le=50),
    team_id: uuid.UUID | None = None,
    tool_id: uuid.UUID | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = DashboardService(session)
    start, end = _parse_period(from_value, to_value)
    return await service.get_top_consumers(
        current_user,
        from_dt=start,
        to_dt=end,
        limit=limit,
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get("/trends", summary="Usage trends", operation_id="getDashboardTrends")
async def get_dashboard_trends(
    from_value: Annotated[datetime, Query(alias="from")],
    to_value: Annotated[datetime, Query(alias="to")],
    granularity: str = Query(default="daily"),
    team_id: uuid.UUID | None = None,
    tool_id: uuid.UUID | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = DashboardService(session)
    start, end = _parse_period(from_value, to_value)
    return await service.get_trends(
        current_user,
        from_dt=start,
        to_dt=end,
        granularity=granularity,
        team_id=team_id,
        tool_id=tool_id,
    )


@router.get("/alerts", summary="Active alerts widget", operation_id="getDashboardAlerts")
async def get_dashboard_alerts(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = DashboardService(session)
    return await service.get_alerts(current_user)

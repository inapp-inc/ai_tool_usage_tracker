"""Copilot productivity analytics REST API."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.copilot.schemas import (
    CopilotCostReportRow,
    CopilotInsightsResponse,
    CopilotOverviewResponse,
    CopilotProductivityReportRow,
    CopilotSeatReportRow,
    CopilotUserDetailResponse,
    CopilotUserListResponse,
)
from app.copilot.service import CopilotAnalyticsService
from app.core.permissions import require_permission
from app.dashboard.scope import resolve_dashboard_scope
from app.db.session import get_session
from app.models.auth import User

router = APIRouter(prefix="/copilot", tags=["Copilot"])


def get_copilot_service(session: AsyncSession = Depends(get_session)) -> CopilotAnalyticsService:
    return CopilotAnalyticsService(session)


def _parse_date(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.date()


async def _assert_team_access(
    session: AsyncSession,
    user: User,
    team_id: UUID,
) -> None:
    scope = await resolve_dashboard_scope(session, user, team_id=team_id)
    if scope.allowed_team_ids is not None and team_id not in scope.allowed_team_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team access denied.")


@router.get("/overview", response_model=CopilotOverviewResponse)
async def copilot_overview(
    team_id: UUID,
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: CopilotAnalyticsService = Depends(get_copilot_service),
) -> CopilotOverviewResponse:
    await _assert_team_access(session, current_user, team_id)
    return await service.get_overview(
        team_id=team_id,
        from_date=_parse_date(from_dt),
        to_date=_parse_date(to_dt),
    )


@router.get("/users", response_model=CopilotUserListResponse)
async def copilot_users(
    team_id: UUID,
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: CopilotAnalyticsService = Depends(get_copilot_service),
) -> CopilotUserListResponse:
    await _assert_team_access(session, current_user, team_id)
    return await service.list_users(
        team_id=team_id,
        from_date=_parse_date(from_dt),
        to_date=_parse_date(to_dt),
    )


@router.get("/users/{user_login}", response_model=CopilotUserDetailResponse)
async def copilot_user_detail(
    user_login: str,
    team_id: UUID,
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: CopilotAnalyticsService = Depends(get_copilot_service),
) -> CopilotUserDetailResponse:
    await _assert_team_access(session, current_user, team_id)
    detail = await service.get_user_detail(
        team_id=team_id,
        user_login=user_login,
        from_date=_parse_date(from_dt),
        to_date=_parse_date(to_dt),
    )
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return detail


@router.get("/insights", response_model=CopilotInsightsResponse)
async def copilot_insights(
    team_id: UUID,
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: CopilotAnalyticsService = Depends(get_copilot_service),
) -> CopilotInsightsResponse:
    await _assert_team_access(session, current_user, team_id)
    return await service.get_insights(
        team_id=team_id,
        from_date=_parse_date(from_dt),
        to_date=_parse_date(to_dt),
    )


@router.get("/reports/seats", response_model=list[CopilotSeatReportRow])
async def copilot_seat_report(
    team_id: UUID,
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: CopilotAnalyticsService = Depends(get_copilot_service),
) -> list[CopilotSeatReportRow]:
    await _assert_team_access(session, current_user, team_id)
    return await service.seat_report(team_id=team_id)


@router.get("/reports/productivity", response_model=list[CopilotProductivityReportRow])
async def copilot_productivity_report(
    team_id: UUID,
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: CopilotAnalyticsService = Depends(get_copilot_service),
) -> list[CopilotProductivityReportRow]:
    await _assert_team_access(session, current_user, team_id)
    return await service.productivity_report(
        team_id=team_id,
        from_date=_parse_date(from_dt),
        to_date=_parse_date(to_dt),
    )


@router.get("/reports/cost", response_model=list[CopilotCostReportRow])
async def copilot_cost_report(
    team_id: UUID,
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: CopilotAnalyticsService = Depends(get_copilot_service),
) -> list[CopilotCostReportRow]:
    await _assert_team_access(session, current_user, team_id)
    return await service.cost_report(team_id=team_id)

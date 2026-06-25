"""Figma billing analytics REST API."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.permissions import require_permission
from app.dashboard.scope import resolve_dashboard_scope
from app.db.session import get_session
from app.figma.schemas import FigmaBillingInsightsResponse, FigmaBillingPeriodUsersResponse
from app.figma.service import FigmaAnalyticsService
from app.models.auth import User

router = APIRouter(prefix="/figma", tags=["Figma"])


def get_figma_service(session: AsyncSession = Depends(get_session)) -> FigmaAnalyticsService:
    return FigmaAnalyticsService(session)


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


@router.get("/billing-insights", response_model=FigmaBillingInsightsResponse)
async def figma_billing_insights(
    team_id: UUID,
    tool_id: UUID,
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    billing_period_start: date | None = None,
    billing_period_end: date | None = None,
    billing_import_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: FigmaAnalyticsService = Depends(get_figma_service),
) -> FigmaBillingInsightsResponse:
    await _assert_team_access(session, current_user, team_id)
    return await service.get_billing_insights(
        team_id=team_id,
        tool_id=tool_id,
        from_date=_parse_date(from_dt),
        to_date=_parse_date(to_dt),
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
        billing_import_id=billing_import_id,
    )


@router.get("/billing-period-users", response_model=FigmaBillingPeriodUsersResponse)
async def figma_billing_period_users(
    team_id: UUID,
    tool_id: UUID,
    period_start: date | None = None,
    period_end: date | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: FigmaAnalyticsService = Depends(get_figma_service),
) -> FigmaBillingPeriodUsersResponse:
    await _assert_team_access(session, current_user, team_id)
    return await service.get_billing_period_users(
        team_id=team_id,
        tool_id=tool_id,
        period_start=period_start,
        period_end=period_end,
    )


@router.get("/billing-day-users", response_model=FigmaBillingPeriodUsersResponse)
async def figma_billing_day_users(
    team_id: UUID,
    tool_id: UUID,
    on_date: date,
    current_user: User = Depends(require_permission("insights", "read")),
    session: AsyncSession = Depends(get_session),
    service: FigmaAnalyticsService = Depends(get_figma_service),
) -> FigmaBillingPeriodUsersResponse:
    await _assert_team_access(session, current_user, team_id)
    return await service.get_billing_day_users(
        team_id=team_id,
        tool_id=tool_id,
        on_date=on_date,
    )

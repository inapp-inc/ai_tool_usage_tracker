"""Reporting API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthenticatedUser
from app.core.rbac import require_super_admin
from app.db.session import get_session
from app.reporting.service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportCreateBody(BaseModel):
    name: str
    type: str
    format: str
    schedule: str
    period_from: str
    period_to: str
    team_ids: list[str] = Field(default_factory=list)


class SubscriptionCreateBody(BaseModel):
    channel: str
    cadence: str
    email_recipients: list[str] = Field(default_factory=list)


@router.get("", operation_id="listReports")
async def list_reports(
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = ReportService(session)
    return {"data": await service.list_reports(current_user)}


@router.post("", status_code=status.HTTP_201_CREATED, operation_id="createReport")
async def create_report(
    body: ReportCreateBody,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = ReportService(session)
    return {"data": await service.create_report(current_user, body.model_dump())}


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = ReportService(session)
    if not await service.delete_report(current_user, str(report_id)):
        raise HTTPException(status_code=404, detail="Report not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{report_id}/subscriptions", operation_id="listReportSubscriptions")
async def list_subscriptions(
    report_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = ReportService(session)
    return {"data": await service.list_subscriptions(current_user, str(report_id))}


@router.post(
    "/{report_id}/subscriptions",
    status_code=status.HTTP_201_CREATED,
    operation_id="createReportSubscription",
)
async def create_subscription(
    report_id: uuid.UUID,
    body: SubscriptionCreateBody,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = ReportService(session)
    return {
        "data": await service.create_subscription(
            current_user, str(report_id), body.model_dump()
        )
    }


@router.delete(
    "/{report_id}/subscriptions/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subscription(
    report_id: uuid.UUID,
    subscription_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = ReportService(session)
    if not await service.delete_subscription(
        current_user, str(report_id), str(subscription_id)
    ):
        raise HTTPException(status_code=404, detail="Subscription not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

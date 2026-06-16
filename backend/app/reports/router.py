"""Reports REST API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.models.auth import User
from app.reports.schemas import (
    ReportGenerateRequest,
    ReportJobResponse,
    ReportListResponse,
    SubscriptionCreateRequest,
    SubscriptionListResponse,
    SubscriptionResponse,
)
from app.reports.service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_report_service(session: AsyncSession = Depends(get_session)) -> ReportService:
    return ReportService(session)


@router.get("", response_model=ReportListResponse)
async def list_reports(
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> ReportListResponse:
    return await service.list_reports(current_user)


@router.post("/generate", response_model=ReportJobResponse, status_code=201)
async def generate_report(
    body: ReportGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> ReportJobResponse:
    created = await service.generate_report(current_user, body)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="report.generate",
        resource_type="report",
        request=request,
        resource_id=created.job_id,
        resource_name=created.name,
    )
    return created


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    reports = await service.list_reports(current_user)
    target = next((row for row in reports.data if row.job_id == report_id), None)
    await service.delete_report(current_user, report_id)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="report.delete",
        resource_type="report",
        request=request,
        resource_id=report_id,
        resource_name=target.name if target else None,
    )


@router.get("/jobs/{job_id}/download")
async def download_report_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> Response:
    return await service.download_report(current_user, job_id)


@router.get("/{report_id}/subscriptions", response_model=SubscriptionListResponse)
async def list_report_subscriptions(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> SubscriptionListResponse:
    return await service.list_subscriptions(current_user, report_id)


@router.post("/{report_id}/subscriptions", response_model=SubscriptionResponse, status_code=201)
async def create_report_subscription(
    report_id: UUID,
    body: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> SubscriptionResponse:
    return await service.create_subscription(current_user, report_id, body)


@router.delete("/{report_id}/subscriptions/{subscription_id}", status_code=204)
async def delete_report_subscription(
    report_id: UUID,
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> None:
    await service.delete_subscription(current_user, report_id, subscription_id)

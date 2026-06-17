"""Audit log REST API."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.context import get_client_ip, get_correlation_id
from app.audit.recorder import AuditRecorder
from app.audit.schemas import AuditLogExportRequest, AuditLogListResponse
from app.audit.service import AuditLogService
from app.core.rbac import require_auditor_access
from app.db.session import get_session
from app.models.auth import User

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


def get_audit_service(session: AsyncSession = Depends(get_session)) -> AuditLogService:
    return AuditLogService(session)


def get_audit_recorder(session: AsyncSession = Depends(get_session)) -> AuditRecorder:
    return AuditRecorder(session)


def _parse_optional_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    actor_id: UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    cursor: str | None = None,
    current_user: User = Depends(require_auditor_access),
    service: AuditLogService = Depends(get_audit_service),
) -> AuditLogListResponse:
    parsed_from = _parse_optional_datetime(from_dt)
    parsed_to = _parse_optional_datetime(to_dt)
    if parsed_from is None and parsed_to is None:
        parsed_from = datetime.now(UTC) - timedelta(days=90)
    return await service.list_logs(
        current_user,
        from_dt=parsed_from,
        to_dt=parsed_to,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        q=q,
        limit=limit,
        cursor=cursor,
    )


@router.post("/export")
async def export_audit_logs(
    body: AuditLogExportRequest,
    current_user: User = Depends(require_auditor_access),
    service: AuditLogService = Depends(get_audit_service),
) -> Response:
    return await service.export_csv(current_user, body)


async def record_audit_event(
    recorder: AuditRecorder,
    *,
    actor: User,
    action: str,
    resource_type: str,
    request: Request | None = None,
    resource_id: UUID | str | None = None,
    resource_name: str | None = None,
    description: str | None = None,
    outcome: str = "success",
) -> None:
    """Shared helper for routers to append audit rows."""
    await recorder.log(
        organization_id=actor.organization_id,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        description=description,
        outcome=outcome,
        source_ip=get_client_ip(request) if request else None,
        correlation_id=get_correlation_id(request) if request else None,
    )

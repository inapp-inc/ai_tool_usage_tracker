"""Uploads REST API."""

import uuid
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder
from app.auth.dependencies import get_current_user
from app.core.permissions import get_scoped_team_ids_for, require_permission
from app.db.session import get_session
from app.models.auth import User
from app.uploads.schemas import (
    UploadColumnMappingRequest,
    UploadCommitRequest,
    UploadCreateResponse,
    UploadListResponse,
    UploadMappingResponse,
    UploadPreviewResponse,
    UploadResponse,
)
from app.uploads.service import UploadService

router = APIRouter(prefix="/uploads", tags=["Uploads"])


def get_upload_service(session: AsyncSession = Depends(get_session)) -> UploadService:
    return UploadService(session)


@router.get("", response_model=UploadListResponse)
async def list_uploads(
    team_id: UUID | None = Query(default=None),
    tool_id: UUID | None = Query(default=None),
    period_from: date | None = Query(default=None),
    period_to: date | None = Query(default=None),
    current_user: User = Depends(require_permission("uploads", "read")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("uploads")),
    service: UploadService = Depends(get_upload_service),
) -> UploadListResponse:
    return await service.list_uploads(
        current_user.organization_id,
        team_ids=managed_team_ids if managed_team_ids else None,
        team_id=team_id,
        tool_id=tool_id,
        period_from=period_from,
        period_to=period_to,
    )


@router.post("", response_model=UploadCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_upload(
    file: UploadFile = File(...),
    team_id: UUID | None = Form(default=None),
    tool_id: UUID | None = Form(default=None),
    current_user: User = Depends(require_permission("uploads", "write")),
    service: UploadService = Depends(get_upload_service),
) -> UploadCreateResponse:
    return await service.create_upload(current_user, file=file, team_id=team_id, tool_id=tool_id)


@router.get("/{upload_id}/mapping", response_model=UploadMappingResponse)
async def get_upload_mapping(
    upload_id: UUID,
    current_user: User = Depends(require_permission("uploads", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("uploads")),
    service: UploadService = Depends(get_upload_service),
) -> UploadMappingResponse:
    if managed_team_ids:
        await service.assert_upload_scope(current_user.organization_id, upload_id, managed_team_ids)
    return await service.get_mapping(current_user.organization_id, upload_id)


@router.post("/{upload_id}/mapping", response_model=UploadResponse)
async def apply_upload_mapping(
    upload_id: UUID,
    body: UploadColumnMappingRequest,
    current_user: User = Depends(require_permission("uploads", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("uploads")),
    service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    if managed_team_ids:
        await service.assert_upload_scope(current_user.organization_id, upload_id, managed_team_ids)
    return await service.apply_mapping(current_user.organization_id, upload_id, body)


@router.get("/{upload_id}/preview", response_model=UploadPreviewResponse)
async def get_upload_preview(
    upload_id: UUID,
    current_user: User = Depends(require_permission("uploads", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("uploads")),
    service: UploadService = Depends(get_upload_service),
) -> UploadPreviewResponse:
    if managed_team_ids:
        await service.assert_upload_scope(current_user.organization_id, upload_id, managed_team_ids)
    return await service.get_preview(current_user.organization_id, upload_id)


@router.post("/{upload_id}/commit", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def commit_upload(
    upload_id: UUID,
    request: Request,
    body: UploadCommitRequest | None = None,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(require_permission("uploads", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("uploads")),
    service: UploadService = Depends(get_upload_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> UploadResponse:
    _ = idempotency_key
    if managed_team_ids:
        await service.assert_upload_scope(current_user.organization_id, upload_id, managed_team_ids)
    payload = body or UploadCommitRequest()
    result = await service.commit_upload(current_user.organization_id, upload_id, payload)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="upload.submit",
        resource_type="upload",
        request=request,
        resource_id=result.id,
        resource_name=result.filename,
    )
    return result


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    upload_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("uploads", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("uploads")),
    service: UploadService = Depends(get_upload_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    if managed_team_ids:
        await service.assert_upload_scope(current_user.organization_id, upload_id, managed_team_ids)
    uploads = await service.list_uploads(current_user.organization_id)
    target = next((row for row in uploads.data if row.id == upload_id), None)
    await service.delete_upload(current_user.organization_id, upload_id)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="upload.delete",
        resource_type="upload",
        request=request,
        resource_id=upload_id,
        resource_name=target.filename if target else None,
    )

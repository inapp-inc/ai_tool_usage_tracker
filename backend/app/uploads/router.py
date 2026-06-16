"""Uploads REST API."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
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
from app.uploads.service import ADMIN_ROLES, UploadService

router = APIRouter(prefix="/uploads", tags=["Uploads"])


def get_upload_service(session: AsyncSession = Depends(get_session)) -> UploadService:
    return UploadService(session)


def require_upload_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


@router.get("", response_model=UploadListResponse)
async def list_uploads(
    current_user: User = Depends(require_upload_admin),
    service: UploadService = Depends(get_upload_service),
) -> UploadListResponse:
    return await service.list_uploads(current_user.organization_id)


@router.post("", response_model=UploadCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_upload(
    file: UploadFile = File(...),
    team_id: UUID | None = Form(default=None),
    current_user: User = Depends(require_upload_admin),
    service: UploadService = Depends(get_upload_service),
) -> UploadCreateResponse:
    return await service.create_upload(current_user, file=file, team_id=team_id)


@router.get("/{upload_id}/mapping", response_model=UploadMappingResponse)
async def get_upload_mapping(
    upload_id: UUID,
    current_user: User = Depends(require_upload_admin),
    service: UploadService = Depends(get_upload_service),
) -> UploadMappingResponse:
    return await service.get_mapping(current_user.organization_id, upload_id)


@router.post("/{upload_id}/mapping", response_model=UploadResponse)
async def apply_upload_mapping(
    upload_id: UUID,
    body: UploadColumnMappingRequest,
    current_user: User = Depends(require_upload_admin),
    service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    return await service.apply_mapping(current_user.organization_id, upload_id, body)


@router.get("/{upload_id}/preview", response_model=UploadPreviewResponse)
async def get_upload_preview(
    upload_id: UUID,
    current_user: User = Depends(require_upload_admin),
    service: UploadService = Depends(get_upload_service),
) -> UploadPreviewResponse:
    return await service.get_preview(current_user.organization_id, upload_id)


@router.post("/{upload_id}/commit", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def commit_upload(
    upload_id: UUID,
    body: UploadCommitRequest | None = None,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(require_upload_admin),
    service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    _ = idempotency_key
    payload = body or UploadCommitRequest()
    return await service.commit_upload(current_user.organization_id, upload_id, payload)


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    upload_id: UUID,
    current_user: User = Depends(require_upload_admin),
    service: UploadService = Depends(get_upload_service),
) -> None:
    await service.delete_upload(current_user.organization_id, upload_id)

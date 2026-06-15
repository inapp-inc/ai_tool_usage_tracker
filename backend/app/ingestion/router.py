"""Usage file upload API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.tools.schemas import ToolCsvColumnMapping, ToolCsvInspectResponse
from app.auth.service import AuthenticatedUser
from app.core.rbac import require_super_admin
from app.db.session import get_session
from app.ingestion.upload_service import UploadCsvError, UploadNotFoundError, UploadService

router = APIRouter(prefix="/uploads", tags=["Uploads"])


def _mapping_from_form(
    token_column: str | None = Form(default=None),
    cost_column: str | None = Form(default=None),
    date_column: str | None = Form(default=None),
    date_from_column: str | None = Form(default=None),
    date_to_column: str | None = Form(default=None),
) -> ToolCsvColumnMapping | None:
    if not token_column:
        return None
    return ToolCsvColumnMapping(
        token_column=token_column or None,
        cost_column=cost_column or None,
        date_column=date_column or None,
        date_from_column=date_from_column or None,
        date_to_column=date_to_column or None,
    )


@router.get("", operation_id="listUploads")
async def list_uploads(
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = UploadService(session)
    return {"data": await service.list_uploads(current_user)}


@router.post("", status_code=status.HTTP_202_ACCEPTED, operation_id="createUpload")
async def create_upload(
    file: UploadFile = File(...),
    team_id: uuid.UUID | None = Form(default=None),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
):
    content = await file.read()
    service = UploadService(session)
    try:
        record = await service.create_upload(
            current_user,
            file_name=file.filename or "upload.csv",
            content=content,
            team_id=str(team_id) if team_id else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    return {"data": record}


@router.get("/{upload_id}", operation_id="getUpload")
async def get_upload(
    upload_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = UploadService(session)
    try:
        return {"data": await service.get_upload(current_user, str(upload_id))}
    except UploadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Upload not found.") from exc


@router.get(
    "/{upload_id}/inspect",
    response_model=ToolCsvInspectResponse,
    operation_id="inspectUpload",
)
async def inspect_upload(
    upload_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ToolCsvInspectResponse:
    service = UploadService(session)
    try:
        return await service.inspect_upload(current_user, str(upload_id))
    except UploadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Upload not found.") from exc
    except UploadCsvError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/{upload_id}/preview", operation_id="getUploadPreview")
async def get_upload_preview(
    upload_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = UploadService(session)
    try:
        return await service.get_preview(current_user, str(upload_id))
    except UploadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Upload not found.") from exc


@router.post("/{upload_id}/preview", operation_id="previewUploadWithMapping")
async def preview_upload_with_mapping(
    upload_id: uuid.UUID,
    token_column: str | None = Form(default=None),
    cost_column: str | None = Form(default=None),
    date_column: str | None = Form(default=None),
    date_from_column: str | None = Form(default=None),
    date_to_column: str | None = Form(default=None),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = UploadService(session)
    mapping = _mapping_from_form(
        token_column=token_column,
        cost_column=cost_column,
        date_column=date_column,
        date_from_column=date_from_column,
        date_to_column=date_to_column,
    )
    try:
        return await service.get_preview(
            current_user,
            str(upload_id),
            mapping=mapping,
        )
    except UploadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Upload not found.") from exc


@router.post("/{upload_id}/submit", operation_id="submitUpload")
async def submit_upload(
    upload_id: uuid.UUID,
    team_id: uuid.UUID | None = Form(default=None),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = UploadService(session)
    try:
        record = await service.submit_upload(
            current_user,
            str(upload_id),
            team_id=str(team_id) if team_id else None,
        )
    except UploadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Upload not found.") from exc
    return {"data": record}


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    upload_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = UploadService(session)
    try:
        await service.delete_upload(current_user, str(upload_id))
    except UploadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Upload not found.") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

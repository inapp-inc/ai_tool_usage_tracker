"""API credentials routes (FR-ADM-003)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.credentials.schemas import (
    CredentialCreateRequest,
    CredentialListResponse,
    CredentialResponse,
    CredentialRotateRequest,
    CredentialUpdateRequest,
)
from app.admin.credentials.service import (
    CredentialNotFoundError,
    CredentialService,
    CredentialValidationError,
)
from app.core.pagination import CursorError
from app.auth.service import AuthenticatedUser
from app.core.rbac import require_super_admin
from app.db.session import get_session

router = APIRouter(prefix="/credentials", tags=["Credentials"])


@router.get(
    "",
    response_model=CredentialListResponse,
    summary="List API credentials",
    operation_id="listCredentials",
)
async def list_credentials(
    tool_id: uuid.UUID | None = Query(default=None),
    team_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> CredentialListResponse:
    service = CredentialService(session)
    try:
        payload = await service.list_credentials(
            current_user,
            tool_id=tool_id,
            team_id=team_id,
            limit=limit,
            cursor=cursor,
        )
    except CursorError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return CredentialListResponse.model_validate(payload)


@router.post(
    "",
    response_model=CredentialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API credential",
    operation_id="createCredential",
)
async def create_credential(
    body: CredentialCreateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> CredentialResponse:
    service = CredentialService(session)
    try:
        return await service.create_credential(current_user, body)
    except CredentialValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{credential_id}/rotate",
    response_model=CredentialResponse,
    summary="Rotate API credential",
    operation_id="rotateCredential",
)
async def rotate_credential(
    credential_id: uuid.UUID,
    body: CredentialRotateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> CredentialResponse:
    service = CredentialService(session)
    try:
        return await service.rotate_credential(current_user, credential_id, body)
    except CredentialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found.",
        ) from exc


@router.patch(
    "/{credential_id}",
    response_model=CredentialResponse,
    summary="Update API credential",
    operation_id="updateCredential",
)
async def update_credential(
    credential_id: uuid.UUID,
    body: CredentialUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> CredentialResponse:
    service = CredentialService(session)
    try:
        return await service.update_credential(current_user, credential_id, body)
    except CredentialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found.",
        ) from exc


@router.post(
    "/{credential_id}/revoke",
    response_model=CredentialResponse,
    summary="Revoke API credential",
    operation_id="revokeCredential",
)
async def revoke_credential(
    credential_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> CredentialResponse:
    service = CredentialService(session)
    try:
        return await service.revoke_credential(current_user, credential_id)
    except CredentialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found.",
        ) from exc


@router.delete(
    "/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API credential",
    operation_id="deleteCredential",
)
async def delete_credential(
    credential_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = CredentialService(session)
    try:
        await service.delete_credential(current_user, credential_id)
    except CredentialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

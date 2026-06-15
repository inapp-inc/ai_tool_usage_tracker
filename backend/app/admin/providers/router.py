"""Provider registry API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.providers.schemas import (
    ProviderCreateRequest,
    ProviderListResponse,
    ProviderResponse,
    ProviderUpdateRequest,
    ValidateProviderRequest,
    ValidateProviderResponse,
)
from app.admin.providers.service import (
    ProviderConflictError,
    ProviderInUseError,
    ProviderNotFoundError,
    ProviderProtectedError,
    ProviderService,
    ProviderValidationError,
)
from app.auth.dependencies import get_current_user
from app.auth.service import AuthenticatedUser
from app.core.pagination import CursorError
from app.core.rbac import require_super_admin
from app.db.session import get_session

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get(
    "",
    response_model=ProviderListResponse,
    summary="List providers",
    operation_id="listProviders",
)
async def list_providers(
    active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProviderListResponse:
    service = ProviderService(session)
    try:
        return await service.list_providers(
            current_user, active=active, limit=limit, cursor=cursor
        )
    except CursorError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create provider",
    operation_id="createProvider",
)
async def create_provider(
    body: ProviderCreateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ProviderResponse:
    service = ProviderService(session)
    try:
        return await service.create_provider(current_user, body)
    except ProviderConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A provider with this slug already exists in your organization.",
        ) from exc


@router.post(
    "/validate",
    response_model=ValidateProviderResponse,
    summary="Validate provider API token",
    operation_id="validateProviderToken",
)
async def validate_provider_token(
    body: ValidateProviderRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ValidateProviderResponse:
    service = ProviderService(session)
    try:
        return await service.validate_token(current_user, body)
    except ProviderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found.",
        ) from exc
    except ProviderValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{provider_id}",
    response_model=ProviderResponse,
    summary="Get provider by ID",
    operation_id="getProvider",
)
async def get_provider(
    provider_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProviderResponse:
    service = ProviderService(session)
    try:
        return await service.get_provider(current_user, provider_id)
    except ProviderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found.",
        ) from exc


@router.patch(
    "/{provider_id}",
    response_model=ProviderResponse,
    summary="Update provider",
    operation_id="updateProvider",
)
async def update_provider(
    provider_id: uuid.UUID,
    body: ProviderUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> ProviderResponse:
    service = ProviderService(session)
    try:
        return await service.update_provider(current_user, provider_id, body)
    except ProviderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found.",
        ) from exc


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete provider",
    operation_id="deleteProvider",
)
async def delete_provider(
    provider_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = ProviderService(session)
    try:
        await service.delete_provider(current_user, provider_id)
    except ProviderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found.",
        ) from exc
    except ProviderProtectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Built-in providers cannot be deleted.",
        ) from exc
    except ProviderInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Provider is in use by one or more tools.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

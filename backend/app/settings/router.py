"""Settings REST API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.models.auth import User
from app.settings.schemas import (
    ProviderCreateRequest,
    ProviderListResponse,
    ProviderResponse,
    ProviderUpdateRequest,
)
from app.settings.service import ProviderService

router = APIRouter(prefix="/settings", tags=["Settings"])

ADMIN_ROLES = frozenset({"super_admin"})


def get_provider_service(session: AsyncSession = Depends(get_session)) -> ProviderService:
    return ProviderService(session)


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers(
    active: bool | None = Query(default=None),
    _current_user: User = Depends(get_current_user),
    service: ProviderService = Depends(get_provider_service),
) -> ProviderListResponse:
    return await service.list_providers(active=active)


@router.post(
    "/providers",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_provider(
    body: ProviderCreateRequest,
    _current_user: User = Depends(require_super_admin),
    service: ProviderService = Depends(get_provider_service),
) -> ProviderResponse:
    return await service.create_provider(body)


@router.patch("/providers/{slug}", response_model=ProviderResponse)
async def update_provider(
    slug: str,
    body: ProviderUpdateRequest,
    _current_user: User = Depends(require_super_admin),
    service: ProviderService = Depends(get_provider_service),
) -> ProviderResponse:
    return await service.update_provider(slug.strip().lower(), body)


@router.delete("/providers/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    slug: str,
    _current_user: User = Depends(require_super_admin),
    service: ProviderService = Depends(get_provider_service),
) -> None:
    await service.delete_provider(slug.strip().lower())

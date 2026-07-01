"""Tenant organization API — super admin only."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_super_admin
from app.db.session import get_session
from app.models.auth import User
from app.organizations.schemas import (
    OrganizationCreateRequest,
    OrganizationCreateResponse,
    OrganizationListResponse,
)
from app.organizations.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def get_organization_service(session: AsyncSession = Depends(get_session)) -> OrganizationService:
    return OrganizationService(session)


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    _current_user: User = Depends(require_super_admin()),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationListResponse:
    return await service.list_organizations()


@router.post(
    "",
    response_model=OrganizationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    body: OrganizationCreateRequest,
    _current_user: User = Depends(require_super_admin()),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationCreateResponse:
    return await service.create_organization(body)

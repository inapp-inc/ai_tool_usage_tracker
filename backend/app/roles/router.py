"""Roles REST API — /roles/*."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.permissions import require_super_admin
from app.db.session import get_session
from app.models.auth import User
from app.roles.schemas import (
    CreateRoleRequest,
    PermissionMatrixResponse,
    ReplacePermissionsRequest,
    RoleListResponse,
    RoleResponse,
    UpdateRoleRequest,
)
from app.roles.service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_role_service(session: AsyncSession = Depends(get_session)) -> RoleService:
    return RoleService(session)


@router.get("", response_model=RoleListResponse)
async def list_roles(
    current_user: User = Depends(require_super_admin()),
    service: RoleService = Depends(get_role_service),
) -> RoleListResponse:
    return await service.list_roles(current_user.organization_id)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: CreateRoleRequest,
    current_user: User = Depends(require_super_admin()),
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    return await service.create_role(current_user.organization_id, body)


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    body: UpdateRoleRequest,
    current_user: User = Depends(require_super_admin()),
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    return await service.update_role(current_user.organization_id, role_id, body)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(require_super_admin()),
    service: RoleService = Depends(get_role_service),
) -> None:
    await service.delete_role(current_user.organization_id, role_id)


@router.get("/{role_id}/permissions", response_model=PermissionMatrixResponse)
async def get_role_permissions(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    service: RoleService = Depends(get_role_service),
) -> PermissionMatrixResponse:
    if current_user.role_name != "super_admin" and current_user.role_id != role_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return await service.get_permissions(current_user.organization_id, role_id)


@router.put("/{role_id}/permissions", response_model=PermissionMatrixResponse)
async def replace_role_permissions(
    role_id: UUID,
    body: ReplacePermissionsRequest,
    current_user: User = Depends(require_super_admin()),
    service: RoleService = Depends(get_role_service),
) -> PermissionMatrixResponse:
    return await service.replace_permissions(
        current_user.organization_id,
        role_id,
        body.permissions,
    )

"""Roles REST API — /roles/*."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.org_scope import get_operating_org_scope, OperatingOrgScope, require_operating_organization_id
from app.core.permissions import require_permission
from app.db.session import get_session
from app.models.auth import User
from app.models.roles import Role
from app.organizations.service import assert_tenant_organization
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


def require_settings_read(current_user: User = Depends(require_permission("settings", "read"))) -> User:
    return current_user


def require_settings_write(current_user: User = Depends(require_permission("settings", "write"))) -> User:
    return current_user


async def _resolve_role_organization_id(
    session: AsyncSession,
    current_user: User,
    role_id: UUID,
) -> UUID:
    """Resolve the organization that owns a role for permission reads/writes."""
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found.",
        )

    if current_user.role_name == "super_admin":
        return role.organization_id

    if current_user.role_name == "org_admin":
        if role.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return role.organization_id

    if current_user.role_id != role_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return role.organization_id


@router.get("", response_model=RoleListResponse)
async def list_roles(
    organization_id: UUID | None = Query(default=None, alias="organization_id"),
    current_user: User = Depends(require_settings_read),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: RoleService = Depends(get_role_service),
) -> RoleListResponse:
    if scope.is_super_admin:
        org_id = scope.single_org_id or organization_id or current_user.organization_id
    else:
        org_id = scope.require_single_org()
    if scope.is_super_admin and org_id != current_user.organization_id:
        await assert_tenant_organization(session, org_id)
    return await service.list_roles(org_id)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: CreateRoleRequest,
    current_user: User = Depends(require_settings_write),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    org_id = require_operating_organization_id(scope)
    return await service.create_role(org_id, body)


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    body: UpdateRoleRequest,
    current_user: User = Depends(require_settings_write),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    org_id = require_operating_organization_id(scope)
    return await service.update_role(org_id, role_id, body)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(require_settings_write),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: RoleService = Depends(get_role_service),
) -> None:
    org_id = require_operating_organization_id(scope)
    await service.delete_role(org_id, role_id)


@router.get("/{role_id}/permissions", response_model=PermissionMatrixResponse)
async def get_role_permissions(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: RoleService = Depends(get_role_service),
) -> PermissionMatrixResponse:
    org_id = await _resolve_role_organization_id(session, current_user, role_id)
    return await service.get_permissions(org_id, role_id)


@router.put("/{role_id}/permissions", response_model=PermissionMatrixResponse)
async def replace_role_permissions(
    role_id: UUID,
    body: ReplacePermissionsRequest,
    current_user: User = Depends(require_settings_write),
    session: AsyncSession = Depends(get_session),
    service: RoleService = Depends(get_role_service),
) -> PermissionMatrixResponse:
    org_id = await _resolve_role_organization_id(session, current_user, role_id)
    return await service.replace_permissions(
        org_id,
        role_id,
        body.permissions,
    )

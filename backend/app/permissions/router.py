"""Permissions API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.service import AuthenticatedUser
from app.core.rbac import require_super_admin
from app.db.session import get_session
from app.permissions.schemas import (
    MyAccessResponse,
    PageAccess,
    PermissionsResponse,
    UpdatePermissionsRequest,
)
from app.permissions.service import ALL_PAGES, CONFIGURABLE_ROLES, PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("", response_model=PermissionsResponse, operation_id="getPermissions")
async def get_permissions(
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> PermissionsResponse:
    svc = PermissionService(session)
    matrix = await svc.get_matrix(current_user.organization_id)
    return PermissionsResponse(
        permissions=matrix,
        pages=sorted(ALL_PAGES),
        roles=CONFIGURABLE_ROLES,
    )


@router.put("", response_model=PermissionsResponse, operation_id="updatePermissions")
async def update_permissions(
    body: UpdatePermissionsRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> PermissionsResponse:
    svc = PermissionService(session)
    matrix = await svc.update_matrix(
        org_id=current_user.organization_id,
        updated_by=current_user.id,
        matrix=body.permissions,
    )
    return PermissionsResponse(
        permissions=matrix,
        pages=sorted(ALL_PAGES),
        roles=CONFIGURABLE_ROLES,
    )


@router.get("/my-access", response_model=MyAccessResponse, operation_id="getMyAccess")
async def my_access(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MyAccessResponse:
    """Returns the calling user's effective access per page. Used by the frontend on login."""
    role = current_user.role

    if role == "super_admin":
        return MyAccessResponse(
            role=role,
            access={page: PageAccess(read=True, write=True) for page in ALL_PAGES},
        )

    svc = PermissionService(session)
    perms = await svc.get_org_permissions(current_user.organization_id)
    role_perms = perms.get(role, {})

    return MyAccessResponse(
        role=role,
        access={
            page: PageAccess(
                read=role_perms.get(page, {}).get("read", False),
                write=role_perms.get(page, {}).get("write", False),
            )
            for page in ALL_PAGES
        },
    )

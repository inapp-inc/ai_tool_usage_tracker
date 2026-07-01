"""Users REST API — org member admin (/users)."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder
from app.auth.dependencies import get_current_user
from app.core.org_scope import (
    get_operating_org_scope,
    OperatingOrgScope,
    resolve_user_create_organization,
)
from app.core.permissions import get_scoped_team_ids_for, require_permission
from app.db.session import get_session
from app.models.auth import User
from app.teams.membership_repository import TeamMembershipRepository
from app.users.schemas import UserCreateRequest, UserCreateResponse, UserListResponse, UserResponse, UserUpdateRequest
from app.users.service import PROTECTED_ASSIGNABLE_ROLES, UserService

router = APIRouter(prefix="/users", tags=["Users"])


def _assert_can_assign_role(current_user: User, role_name: str) -> None:
    if role_name in PROTECTED_ASSIGNABLE_ROLES and current_user.role_name != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admin can assign the Super Admin role.",
        )
    if current_user.role_name == "team_admin" and role_name == "super_admin":
        raise HTTPException(status_code=403, detail="team_admin cannot assign super_admin role.")


async def _resolve_requested_role_name(
    service: UserService,
    organization_id: uuid.UUID,
    body: UserCreateRequest | UserUpdateRequest,
) -> str | None:
    if body.role_id is not None:
        return await service.resolve_role_name(organization_id, role_id=body.role_id)
    if isinstance(body, UserCreateRequest):
        return body.role
    return body.role


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


def require_user_admin(current_user: User = Depends(require_permission("members", "read"))) -> User:
    return current_user


def require_user_write(current_user: User = Depends(require_permission("members", "write"))) -> User:
    return current_user


async def _assert_in_managed_teams(
    session: AsyncSession,
    user_id: uuid.UUID,
    managed_team_ids: list[uuid.UUID],
) -> None:
    if not managed_team_ids:
        return
    repo = TeamMembershipRepository(session)
    active = await repo.list_active_teams_for_user(user_id)
    team_ids_for_user = {team.id for _, team in active}
    if not team_ids_for_user.intersection(set(managed_team_ids)):
        raise HTTPException(status_code=403, detail="User is not in your managed teams.")


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(require_user_admin),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("members")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    return await service.list_users_for_scope(
        scope,
        team_ids=managed_team_ids if managed_team_ids else None,
    )


@router.post("", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest,
    request: Request,
    current_user: User = Depends(require_user_write),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(get_user_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> UserCreateResponse:
    role_hint = body.role if body.role_id is None else None
    target_org_id, org_was_created = await resolve_user_create_organization(
        scope,
        session,
        body_organization_id=body.organization_id,
        organization_name=body.organization_name,
        role_name=role_hint,
    )
    requested_role = await _resolve_requested_role_name(
        service, target_org_id, body
    )
    if requested_role is not None:
        _assert_can_assign_role(current_user, requested_role)

    created = await service.create_user(target_org_id, body, actor=current_user)
    if org_was_created:
        await record_audit_event(
            recorder,
            actor=current_user,
            action="organization.create",
            resource_type="organization",
            request=request,
            resource_id=target_org_id,
            resource_name=(body.organization_name or "").strip(),
            description=f"Created organization {(body.organization_name or '').strip()}",
        )
    await record_audit_event(
        recorder,
        actor=current_user,
        action="user.invite",
        resource_type="user",
        request=request,
        resource_id=created.id,
        resource_name=created.email,
        description=f"Invited {created.email} as {created.role.replace('_', ' ')}",
    )
    return created


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_user_admin),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("members")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    if managed_team_ids:
        await _assert_in_managed_teams(session, user_id, managed_team_ids)
    return await service.get_user(current_user.organization_id, user_id, scope=scope)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(require_user_write),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("members")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(get_user_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> UserResponse:
    if body.role is not None or body.role_id is not None:
        user = await service.get_user(current_user.organization_id, user_id, scope=scope)
        requested_role = await _resolve_requested_role_name(
            service, user.organization_id, body
        )
        if requested_role is not None:
            _assert_can_assign_role(current_user, requested_role)
    if managed_team_ids:
        await _assert_in_managed_teams(session, user_id, managed_team_ids)
    updated = await service.update_user(
        current_user.organization_id,
        user_id,
        body,
        scope=scope,
    )
    action = "user.role_change" if body.role is not None or body.role_id is not None else "user.update"
    await record_audit_event(
        recorder,
        actor=current_user,
        action=action,
        resource_type="user",
        request=request,
        resource_id=updated.id,
        resource_name=updated.email,
    )
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_user_write),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("members")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(get_user_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    if managed_team_ids:
        await _assert_in_managed_teams(session, user_id, managed_team_ids)
    user = await service.get_user(current_user.organization_id, user_id, scope=scope)
    await service.deactivate_user(current_user.organization_id, user_id, scope=scope)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="user.remove",
        resource_type="user",
        request=request,
        resource_id=user.id,
        resource_name=user.email,
    )

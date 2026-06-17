"""Users REST API — org member admin (/users)."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder
from app.auth.dependencies import get_current_user
from app.core.rbac import get_managed_team_ids, require_team_admin_or_above
from app.db.session import get_session
from app.models.auth import User
from app.teams.membership_repository import TeamMembershipRepository
from app.users.schemas import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


def require_user_admin(current_user: User = Depends(require_team_admin_or_above)) -> User:
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
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    return await service.list_users(
        current_user.organization_id,
        team_ids=managed_team_ids if current_user.role == "team_admin" else None,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest,
    request: Request,
    current_user: User = Depends(require_user_admin),
    service: UserService = Depends(get_user_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> UserResponse:
    if current_user.role == "team_admin" and body.role == "super_admin":
        raise HTTPException(status_code=403, detail="team_admin cannot assign super_admin role.")
    created = await service.create_user(current_user.organization_id, body)
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
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    if current_user.role == "team_admin":
        await _assert_in_managed_teams(session, user_id, managed_team_ids)
    return await service.get_user(current_user.organization_id, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(require_user_admin),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(get_user_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> UserResponse:
    if current_user.role == "team_admin" and body.role == "super_admin":
        raise HTTPException(status_code=403, detail="team_admin cannot assign super_admin role.")
    if current_user.role == "team_admin":
        await _assert_in_managed_teams(session, user_id, managed_team_ids)
    updated = await service.update_user(current_user.organization_id, user_id, body)
    action = "user.role_change" if body.role is not None else "user.update"
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
    current_user: User = Depends(require_user_admin),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(get_user_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    if current_user.role == "team_admin":
        await _assert_in_managed_teams(session, user_id, managed_team_ids)
    user = await service.get_user(current_user.organization_id, user_id)
    await service.deactivate_user(current_user.organization_id, user_id)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="user.remove",
        resource_type="user",
        request=request,
        resource_id=user.id,
        resource_name=user.email,
    )

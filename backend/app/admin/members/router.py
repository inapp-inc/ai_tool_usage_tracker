"""Member management API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.members.schemas import (
    MemberInviteRequest,
    MemberListResponse,
    MemberResponse,
    MemberUpdateRequest,
)
from app.admin.members.service import (
    MemberConflictError,
    MemberNotFoundError,
    MemberService,
)
from app.auth.service import AuthenticatedUser
from app.core.rbac import get_managed_team_ids, require_team_admin_or_above
from app.db.session import get_session
from app.models.admin import TeamMembership

router = APIRouter(prefix="/members", tags=["Members"])


async def _is_member_in_teams(
    session: AsyncSession,
    member_id: uuid.UUID,
    team_ids: list[uuid.UUID],
) -> bool:
    """Returns True if the given user is an active member of any of the given teams."""
    if not team_ids:
        return True  # super_admin: no restriction
    stmt = select(TeamMembership.id).where(
        TeamMembership.user_id == member_id,
        TeamMembership.team_id.in_(team_ids),
        TeamMembership.removed_at.is_(None),
    )
    result = await session.execute(stmt)
    return result.first() is not None


@router.get("", response_model=MemberListResponse, operation_id="listMembers")
async def list_members(
    team_id: uuid.UUID | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> MemberListResponse:
    if current_user.role == "team_admin":
        if not managed_team_ids:
            raise HTTPException(status_code=403, detail="You are not a member of any team.")
        if team_id is None:
            team_id = managed_team_ids[0]
        elif team_id not in managed_team_ids:
            raise HTTPException(status_code=403, detail="You do not have access to this team.")

    service = MemberService(session)
    return await service.list_members(
        current_user.organization_id, team_id=team_id
    )


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="inviteMember",
)
async def invite_member(
    body: MemberInviteRequest,
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> MemberResponse:
    if current_user.role == "team_admin":
        if body.platform_role == "super_admin":
            raise HTTPException(status_code=403, detail="You cannot assign the Super Admin role.")
        if not managed_team_ids:
            raise HTTPException(status_code=403, detail="You are not a member of any team.")
        for tid in body.team_ids:
            if tid not in managed_team_ids:
                raise HTTPException(status_code=403, detail="You can only add members to your own team.")
        if not body.team_ids:
            body = body.model_copy(update={"team_ids": managed_team_ids})

    service = MemberService(session)
    try:
        return await service.invite_member(current_user.organization_id, body)
    except MemberConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    operation_id="updateMember",
)
async def update_member(
    member_id: uuid.UUID,
    body: MemberUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> MemberResponse:
    if current_user.role == "team_admin":
        if body.platform_role == "super_admin":
            raise HTTPException(status_code=403, detail="You cannot assign the Super Admin role.")
        member_in_team = await _is_member_in_teams(session, member_id, managed_team_ids)
        if not member_in_team:
            raise HTTPException(status_code=403, detail="Member is not in your team.")

    service = MemberService(session)
    try:
        return await service.update_member(
            current_user.organization_id, member_id, body
        )
    except MemberNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        ) from exc


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="removeMember",
)
async def remove_member(
    member_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> Response:
    if current_user.role == "team_admin":
        member_in_team = await _is_member_in_teams(session, member_id, managed_team_ids)
        if not member_in_team:
            raise HTTPException(status_code=403, detail="Member is not in your team.")

    service = MemberService(session)
    try:
        await service.remove_member(current_user.organization_id, member_id)
    except MemberNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

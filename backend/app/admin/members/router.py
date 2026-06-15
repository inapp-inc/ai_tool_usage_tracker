"""Member management API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
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
from app.core.rbac import require_super_admin
from app.db.session import get_session

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("", response_model=MemberListResponse, operation_id="listMembers")
async def list_members(
    team_id: uuid.UUID | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> MemberListResponse:
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
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> MemberResponse:
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
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> MemberResponse:
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
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = MemberService(session)
    try:
        await service.remove_member(current_user.organization_id, member_id)
    except MemberNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

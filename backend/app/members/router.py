"""Members REST API — unified org member list."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.members.schemas import MemberListResponse, MembersView
from app.members.service import MembersService
from app.models.auth import User
from app.users.service import ADMIN_ROLES

router = APIRouter(prefix="/members", tags=["Members"])


def get_members_service(session: AsyncSession = Depends(get_session)) -> MembersService:
    return MembersService(session)


def require_user_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


@router.get("", response_model=MemberListResponse)
async def list_members(
    view: Literal["all", "invited"] = Query(default="all"),
    current_user: User = Depends(require_user_admin),
    service: MembersService = Depends(get_members_service),
) -> MemberListResponse:
    resolved: MembersView = view if view in ("all", "invited") else "all"
    return await service.list_members(current_user.organization_id, view=resolved)

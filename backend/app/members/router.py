"""Members REST API — unified org member list."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_scoped_team_ids_for, require_permission
from app.db.session import get_session
from app.members.schemas import MemberListResponse, MembersView
from app.members.service import MembersService
from app.models.auth import User

router = APIRouter(prefix="/members", tags=["Members"])


def get_members_service(session: AsyncSession = Depends(get_session)) -> MembersService:
    return MembersService(session)


@router.get("", response_model=MemberListResponse)
async def list_members(
    view: Literal["all", "invited"] = Query(default="all"),
    current_user: User = Depends(require_permission("members", "read")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("members")),
    service: MembersService = Depends(get_members_service),
) -> MemberListResponse:
    resolved: MembersView = view if view in ("all", "invited") else "all"
    return await service.list_members(
        current_user.organization_id,
        view=resolved,
        managed_team_ids=managed_team_ids if managed_team_ids else None,
    )

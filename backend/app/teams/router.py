"""Teams REST API — OpenAPI /teams/*."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder

from app.auth.dependencies import get_current_user
from app.core.org_scope import get_operating_org_scope, OperatingOrgScope
from app.core.permissions import ORG_WIDE_ROLE_NAMES, PermissionCache, require_permission
from app.db.session import get_session
from app.models.auth import User
from app.teams.schemas import (
    TeamCreateRequest,
    TeamListResponse,
    TeamMemberAddRequest,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamResponse,
    TeamToolAssignRequest,
    TeamToolAssignmentListResponse,
    TeamToolAssignmentResponse,
    TeamSyncResponse,
    TeamToolUpdateRequest,
    TeamUpdateRequest,
)
from app.teams.service import TeamService
from app.teams.team_tool_service import TeamToolService

router = APIRouter(prefix="/teams", tags=["Teams"])

logger = logging.getLogger(__name__)

WRITE_ROLES = frozenset({"super_admin", "org_admin"})
TEAM_TOOL_WRITE_ROLES = frozenset({"super_admin", "org_admin", "team_admin"})


def get_team_service(session: AsyncSession = Depends(get_session)) -> TeamService:
    return TeamService(session)


def get_team_tool_service(session: AsyncSession = Depends(get_session)) -> TeamToolService:
    return TeamToolService(session)


async def require_team_tool_writer(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Team tool assignment — org admins use teams write; team admins use members write."""
    if current_user.role_name in ORG_WIDE_ROLE_NAMES:
        return current_user

    role_id = current_user.role_id
    if role_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )

    if await PermissionCache.check(role_id, "teams", "write", session) or await PermissionCache.check(
        role_id, "members", "write", session
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions.",
    )


# TODO: RBAC guard needed — currently allows all authenticated roles (finance_viewer, auditor, team_member)
@router.get("/{team_id}/tools", response_model=TeamToolAssignmentListResponse)
async def list_team_tools(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TeamToolService = Depends(get_team_tool_service),
) -> TeamToolAssignmentListResponse:
    return await service.list_assignments(current_user, team_id)


@router.post(
    "/{team_id}/tools",
    response_model=TeamToolAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_team_tool(
    team_id: UUID,
    body: TeamToolAssignRequest,
    current_user: User = Depends(require_team_tool_writer),
    service: TeamToolService = Depends(get_team_tool_service),
) -> TeamToolAssignmentResponse:
    return await service.create_assignment(current_user, team_id, body)


@router.patch(
    "/{team_id}/tools/{tool_id}",
    response_model=TeamToolAssignmentResponse,
)
async def update_team_tool(
    team_id: UUID,
    tool_id: UUID,
    body: TeamToolUpdateRequest,
    current_user: User = Depends(require_team_tool_writer),
    service: TeamToolService = Depends(get_team_tool_service),
) -> TeamToolAssignmentResponse:
    return await service.update_assignment(current_user, team_id, tool_id, body)


@router.delete("/{team_id}/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_tool(
    team_id: UUID,
    tool_id: UUID,
    current_user: User = Depends(require_team_tool_writer),
    service: TeamToolService = Depends(get_team_tool_service),
) -> None:
    await service.delete_assignment(current_user, team_id, tool_id)


@router.post("/{team_id}/sync", response_model=TeamSyncResponse)
async def sync_team_tools(
    team_id: UUID,
    current_user: User = Depends(require_team_tool_writer),
    service: TeamToolService = Depends(get_team_tool_service),
) -> TeamSyncResponse:
    result = await service.sync_team_tools(current_user, team_id)
    logger.info(
        "Team sync API | team_id=%s synced=%s skipped=%s failed=%s results=%s",
        team_id,
        result.synced_count,
        result.skipped_count,
        result.failed_count,
        [
            {"tool": row.tool_name, "status": row.status, "message": row.message}
            for row in result.results
        ],
    )
    return result


@router.get("", response_model=TeamListResponse)
async def list_teams(
    active: bool | None = Query(default=None),
    current_user: User = Depends(require_permission("teams", "read")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: TeamService = Depends(get_team_service),
) -> TeamListResponse:
    return await service.list_teams(current_user, active=active, scope=scope)


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: TeamCreateRequest,
    request: Request,
    current_user: User = Depends(require_permission("teams", "write")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: TeamService = Depends(get_team_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> TeamResponse:
    created = await service.create_team(current_user, body, scope=scope)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="team.create",
        resource_type="team",
        request=request,
        resource_id=created.id,
        resource_name=created.name,
    )
    return created


@router.get("/{team_id}/members", response_model=TeamMemberListResponse)
async def list_team_members(
    team_id: UUID,
    current_user: User = Depends(require_permission("teams", "read")),
    service: TeamService = Depends(get_team_service),
) -> TeamMemberListResponse:
    return await service.list_team_members(current_user, team_id)


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: UUID,
    body: TeamMemberAddRequest,
    current_user: User = Depends(require_permission("teams", "write")),
    service: TeamService = Depends(get_team_service),
) -> TeamMemberResponse:
    return await service.add_team_member(current_user, team_id, body.user_id)


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(require_permission("teams", "write")),
    service: TeamService = Depends(get_team_service),
) -> None:
    await service.remove_team_member(current_user, team_id, user_id)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: User = Depends(require_permission("teams", "read")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    return await service.get_team(current_user, team_id, scope=scope)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    body: TeamUpdateRequest,
    request: Request,
    current_user: User = Depends(require_permission("teams", "write")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: TeamService = Depends(get_team_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> TeamResponse:
    updated = await service.update_team(current_user, team_id, body, scope=scope)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="team.update",
        resource_type="team",
        request=request,
        resource_id=updated.id,
        resource_name=updated.name,
    )
    return updated


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("teams", "write")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: TeamService = Depends(get_team_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    team = await service.get_team(current_user, team_id, scope=scope)
    await service.delete_team(current_user, team_id, scope=scope)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="team.delete",
        resource_type="team",
        request=request,
        resource_id=team.id,
        resource_name=team.name,
    )

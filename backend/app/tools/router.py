"""Tools REST API — OpenAPI /tools/*."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder
from app.auth.dependencies import get_current_user
from app.core.rbac import require_team_admin_or_above
from app.db.session import get_session
from app.models.auth import User
from app.tools.schemas import ToolCreateRequest, ToolListResponse, ToolMembersListResponse, ToolResponse, ToolUpdateRequest
from app.tools.service import ToolService

router = APIRouter(prefix="/tools", tags=["Tools"])

WRITE_ROLES = frozenset({"super_admin"})


def get_tool_service(session: AsyncSession = Depends(get_session)) -> ToolService:
    return ToolService(session)


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


async def _reload_scheduler(request: Request) -> None:
    scheduler = getattr(request.app.state, "collector_scheduler", None)
    if scheduler is not None:
        await scheduler.reload()


@router.get("", response_model=ToolListResponse)
async def list_tools(
    active: bool | None = Query(default=None),
    current_user: User = Depends(require_team_admin_or_above),
    service: ToolService = Depends(get_tool_service),
) -> ToolListResponse:
    return await service.list_tools(current_user.organization_id, active=active)


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    body: ToolCreateRequest,
    request: Request,
    current_user: User = Depends(require_super_admin),
    service: ToolService = Depends(get_tool_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> ToolResponse:
    created = await service.create_tool(current_user.organization_id, body)
    await _reload_scheduler(request)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="tool.connect",
        resource_type="tool",
        request=request,
        resource_id=created.id,
        resource_name=created.name,
    )
    return created


@router.get("/{tool_id}/members", response_model=ToolMembersListResponse)
async def list_tool_members(
    tool_id: UUID,
    current_user: User = Depends(require_team_admin_or_above),
    service: ToolService = Depends(get_tool_service),
) -> ToolMembersListResponse:
    return await service.list_tool_members(current_user.organization_id, tool_id)


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: UUID,
    current_user: User = Depends(require_team_admin_or_above),
    service: ToolService = Depends(get_tool_service),
) -> ToolResponse:
    return await service.get_tool(current_user.organization_id, tool_id)


@router.patch("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: UUID,
    body: ToolUpdateRequest,
    request: Request,
    current_user: User = Depends(require_super_admin),
    service: ToolService = Depends(get_tool_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> ToolResponse:
    updated = await service.update_tool(current_user.organization_id, tool_id, body)
    await _reload_scheduler(request)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="tool.update",
        resource_type="tool",
        request=request,
        resource_id=updated.id,
        resource_name=updated.name,
    )
    return updated


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: UUID,
    request: Request,
    current_user: User = Depends(require_super_admin),
    service: ToolService = Depends(get_tool_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    tool = await service.get_tool(current_user.organization_id, tool_id)
    await service.delete_tool(current_user.organization_id, tool_id)
    await _reload_scheduler(request)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="tool.delete",
        resource_type="tool",
        request=request,
        resource_id=tool.id,
        resource_name=tool.name,
    )


@router.post("/{tool_id}/sync", response_model=ToolResponse)
async def sync_tool(
    tool_id: UUID,
    current_user: User = Depends(require_super_admin),
    service: ToolService = Depends(get_tool_service),
) -> ToolResponse:
    return await service.sync_tool(current_user.organization_id, tool_id)

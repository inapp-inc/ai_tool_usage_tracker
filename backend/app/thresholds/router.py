"""Thresholds REST API — alert rules and history."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder
from app.auth.dependencies import get_current_user
from app.core.permissions import get_scoped_team_ids_for, require_permission
from app.db.session import get_session
from app.models.auth import User
from app.thresholds.schemas import (
    ThresholdCreateRequest,
    ThresholdEventListResponse,
    ThresholdEventResponse,
    ThresholdListResponse,
    ThresholdResponse,
    ThresholdUpdateRequest,
)
from app.thresholds.service import ThresholdService

router = APIRouter(prefix="/thresholds", tags=["Thresholds"])


def get_threshold_service(session: AsyncSession = Depends(get_session)) -> ThresholdService:
    return ThresholdService(session)


@router.get("", response_model=ThresholdListResponse)
async def list_thresholds(
    current_user: User = Depends(require_permission("alerts", "read")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("alerts")),
    service: ThresholdService = Depends(get_threshold_service),
) -> ThresholdListResponse:
    return await service.list_thresholds(
        current_user.organization_id,
        team_ids=managed_team_ids if managed_team_ids else None,
    )


@router.post("", response_model=ThresholdResponse, status_code=status.HTTP_201_CREATED)
async def create_threshold(
    body: ThresholdCreateRequest,
    request: Request,
    current_user: User = Depends(require_permission("alerts", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("alerts")),
    service: ThresholdService = Depends(get_threshold_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> ThresholdResponse:
    if managed_team_ids:
        if body.team_id not in managed_team_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create threshold for a team outside your scope.",
            )
    created = await service.create_threshold(current_user.organization_id, body)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="alert.create",
        resource_type="alert",
        request=request,
        resource_id=created.id,
        resource_name=created.name,
    )
    return created


@router.get("/events", response_model=ThresholdEventListResponse)
async def list_threshold_events(
    current_user: User = Depends(require_permission("alerts", "read")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("alerts")),
    service: ThresholdService = Depends(get_threshold_service),
) -> ThresholdEventListResponse:
    return await service.list_events(
        current_user.organization_id,
        team_ids=managed_team_ids if managed_team_ids else None,
    )


@router.post("/events/{event_id}/acknowledge", response_model=ThresholdEventResponse)
async def acknowledge_threshold_event(
    event_id: UUID,
    current_user: User = Depends(require_permission("alerts", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("alerts")),
    service: ThresholdService = Depends(get_threshold_service),
) -> ThresholdEventResponse:
    return await service.acknowledge_event(
        current_user.organization_id,
        event_id,
        current_user,
        managed_team_ids=managed_team_ids if managed_team_ids else None,
    )


@router.patch("/{threshold_id}", response_model=ThresholdResponse)
async def update_threshold(
    threshold_id: UUID,
    body: ThresholdUpdateRequest,
    request: Request,
    current_user: User = Depends(require_permission("alerts", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("alerts")),
    service: ThresholdService = Depends(get_threshold_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> ThresholdResponse:
    if managed_team_ids:
        await service.assert_threshold_scope(current_user.organization_id, threshold_id, managed_team_ids)
    updated = await service.update_threshold(
        current_user.organization_id,
        threshold_id,
        body,
    )
    await record_audit_event(
        recorder,
        actor=current_user,
        action="alert.update",
        resource_type="alert",
        request=request,
        resource_id=updated.id,
        resource_name=updated.name,
    )
    return updated


@router.delete("/{threshold_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threshold(
    threshold_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("alerts", "write")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("alerts")),
    service: ThresholdService = Depends(get_threshold_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    if managed_team_ids:
        await service.assert_threshold_scope(current_user.organization_id, threshold_id, managed_team_ids)
    thresholds = await service.list_thresholds(current_user.organization_id)
    target = next((row for row in thresholds.data if row.id == threshold_id), None)
    await service.delete_threshold(current_user.organization_id, threshold_id)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="alert.delete",
        resource_type="alert",
        request=request,
        resource_id=threshold_id,
        resource_name=target.name if target else None,
    )

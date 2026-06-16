"""Thresholds REST API — alert rules and history."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
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

ADMIN_ROLES = frozenset({"super_admin", "team_admin"})


def get_threshold_service(session: AsyncSession = Depends(get_session)) -> ThresholdService:
    return ThresholdService(session)


def require_threshold_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


@router.get("", response_model=ThresholdListResponse)
async def list_thresholds(
    current_user: User = Depends(require_threshold_admin),
    service: ThresholdService = Depends(get_threshold_service),
) -> ThresholdListResponse:
    return await service.list_thresholds(current_user.organization_id)


@router.post("", response_model=ThresholdResponse, status_code=status.HTTP_201_CREATED)
async def create_threshold(
    body: ThresholdCreateRequest,
    current_user: User = Depends(require_threshold_admin),
    service: ThresholdService = Depends(get_threshold_service),
) -> ThresholdResponse:
    return await service.create_threshold(current_user.organization_id, body)


@router.get("/events", response_model=ThresholdEventListResponse)
async def list_threshold_events(
    current_user: User = Depends(require_threshold_admin),
    service: ThresholdService = Depends(get_threshold_service),
) -> ThresholdEventListResponse:
    return await service.list_events(current_user.organization_id)


@router.post("/events/{event_id}/acknowledge", response_model=ThresholdEventResponse)
async def acknowledge_threshold_event(
    event_id: UUID,
    current_user: User = Depends(require_threshold_admin),
    service: ThresholdService = Depends(get_threshold_service),
) -> ThresholdEventResponse:
    return await service.acknowledge_event(
        current_user.organization_id,
        event_id,
        current_user,
    )


@router.patch("/{threshold_id}", response_model=ThresholdResponse)
async def update_threshold(
    threshold_id: UUID,
    body: ThresholdUpdateRequest,
    current_user: User = Depends(require_threshold_admin),
    service: ThresholdService = Depends(get_threshold_service),
) -> ThresholdResponse:
    return await service.update_threshold(
        current_user.organization_id,
        threshold_id,
        body,
    )


@router.delete("/{threshold_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threshold(
    threshold_id: UUID,
    current_user: User = Depends(require_threshold_admin),
    service: ThresholdService = Depends(get_threshold_service),
) -> None:
    await service.delete_threshold(current_user.organization_id, threshold_id)

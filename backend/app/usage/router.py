"""Usage read API for collected token events."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.collector.schemas import UsageEventListResponse, UsageSummaryResponse
from app.collector.service import CollectorService
from app.core.permissions import get_scoped_team_ids_for, require_permission
from app.db.session import get_session
from app.models.auth import User

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("/events", response_model=UsageEventListResponse)
async def list_usage_events(
    collector_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_permission("insights", "read")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("insights")),
    session: AsyncSession = Depends(get_session),
) -> UsageEventListResponse:
    _ = current_user
    service = CollectorService(session)
    return UsageEventListResponse(
        data=await service.list_usage_events(
            collector_id=collector_id,
            limit=limit,
            managed_team_ids=managed_team_ids if managed_team_ids else None,
        )
    )


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    collector_id: UUID | None = None,
    current_user: User = Depends(require_permission("insights", "read")),
    managed_team_ids: list[uuid.UUID] = Depends(get_scoped_team_ids_for("insights")),
    session: AsyncSession = Depends(get_session),
) -> UsageSummaryResponse:
    _ = current_user
    service = CollectorService(session)
    return await service.usage_summary(
        collector_id=collector_id,
        managed_team_ids=managed_team_ids if managed_team_ids else None,
    )

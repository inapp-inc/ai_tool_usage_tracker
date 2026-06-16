"""Usage read API for collected token events."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.collector.schemas import UsageEventListResponse, UsageSummaryResponse
from app.collector.service import CollectorService
from app.db.session import get_session

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("/events", response_model=UsageEventListResponse)
async def list_usage_events(
    collector_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> UsageEventListResponse:
    service = CollectorService(session)
    return UsageEventListResponse(
        data=await service.list_usage_events(collector_id=collector_id, limit=limit)
    )


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    collector_id: UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> UsageSummaryResponse:
    service = CollectorService(session)
    return await service.usage_summary(collector_id=collector_id)

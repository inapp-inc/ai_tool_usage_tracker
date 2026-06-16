"""Collector REST API — configure pull interval from frontend."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.collector.schemas import (
    CollectorCreateRequest,
    CollectorListResponse,
    CollectorResponse,
    CollectorRunListResponse,
    CollectorRunResponse,
    CollectorUpdateRequest,
)
from app.collector.service import CollectorService
from app.db.session import get_session

router = APIRouter(prefix="/collectors", tags=["Collectors"])


def get_collector_service(
    session: AsyncSession = Depends(get_session),
) -> CollectorService:
    return CollectorService(session)


async def _reload_scheduler(request: Request) -> None:
    scheduler = getattr(request.app.state, "collector_scheduler", None)
    if scheduler is not None:
        await scheduler.reload()


@router.get("", response_model=CollectorListResponse)
async def list_collectors(
    service: CollectorService = Depends(get_collector_service),
) -> CollectorListResponse:
    return CollectorListResponse(data=await service.list_collectors())


@router.post("", response_model=CollectorResponse, status_code=status.HTTP_201_CREATED)
async def create_collector(
    body: CollectorCreateRequest,
    request: Request,
    service: CollectorService = Depends(get_collector_service),
) -> CollectorResponse:
    created = await service.create_collector(body)
    await _reload_scheduler(request)
    return created


@router.get("/{collector_id}", response_model=CollectorResponse)
async def get_collector(
    collector_id: UUID,
    service: CollectorService = Depends(get_collector_service),
) -> CollectorResponse:
    collector = await service.get_collector(collector_id)
    if collector is None:
        raise HTTPException(status_code=404, detail="Collector not found")
    return collector


@router.patch("/{collector_id}", response_model=CollectorResponse)
async def update_collector(
    collector_id: UUID,
    body: CollectorUpdateRequest,
    request: Request,
    service: CollectorService = Depends(get_collector_service),
) -> CollectorResponse:
    updated = await service.update_collector(collector_id, body)
    if updated is None:
        raise HTTPException(status_code=404, detail="Collector not found")
    await _reload_scheduler(request)
    return updated


@router.delete("/{collector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collector(
    collector_id: UUID,
    request: Request,
    service: CollectorService = Depends(get_collector_service),
) -> None:
    deleted = await service.delete_collector(collector_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Collector not found")
    await _reload_scheduler(request)


@router.post(
    "/{collector_id}/run",
    response_model=CollectorRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_collector_now(
    collector_id: UUID,
    service: CollectorService = Depends(get_collector_service),
) -> CollectorRunResponse:
    run = await service.run_collector(collector_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Collector not found")
    return run


@router.get("/{collector_id}/runs", response_model=CollectorRunListResponse)
async def list_collector_runs(
    collector_id: UUID,
    service: CollectorService = Depends(get_collector_service),
) -> CollectorRunListResponse:
    if await service.get_collector(collector_id) is None:
        raise HTTPException(status_code=404, detail="Collector not found")
    return CollectorRunListResponse(data=await service.list_runs(collector_id))

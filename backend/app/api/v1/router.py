"""API v1 route definitions."""

from fastapi import APIRouter, Response, status

from app.api.v1.schemas import HealthResponse
from app.config import get_settings
from app.connectivity import verify_connectivity

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["Health"],
)
async def get_health() -> Response:
    """Liveness/readiness probe matching OpenAPI HealthResponse."""
    settings = get_settings()
    connectivity = await verify_connectivity(settings)
    payload = HealthResponse(
        status="ok" if connectivity.is_healthy else "degraded",
        database=connectivity.database,  # type: ignore[arg-type]
        redis=connectivity.redis,  # type: ignore[arg-type]
    )
    response_status = (
        status.HTTP_200_OK
        if connectivity.is_healthy
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        status_code=response_status,
    )

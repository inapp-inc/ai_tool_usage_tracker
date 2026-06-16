"""API v1 route definitions."""

from fastapi import APIRouter, Response, status

from app.api.v1.schemas import HealthResponse
from app.auth.router import router as auth_router
from app.collector.router import router as collectors_router
from app.config import get_settings
from app.connectivity import verify_connectivity
from app.credentials.router import router as credentials_router
from app.members.router import router as members_router
from app.teams.router import router as teams_router
from app.thresholds.router import router as thresholds_router
from app.tools.router import router as tools_router
from app.uploads.router import router as uploads_router
from app.usage.router import router as usage_router
from app.users.router import router as users_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(collectors_router)
router.include_router(teams_router)
router.include_router(tools_router)
router.include_router(users_router)
router.include_router(members_router)
router.include_router(credentials_router)
router.include_router(thresholds_router)
router.include_router(uploads_router)
router.include_router(usage_router)


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

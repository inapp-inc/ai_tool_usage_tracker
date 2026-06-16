"""API v1 route definitions."""

from fastapi import APIRouter, Response, status

from app.admin.credentials.router import router as credentials_router
from app.admin.members.router import router as members_router
from app.admin.providers.router import router as providers_router
from app.admin.teams.router import router as teams_router
from app.admin.tools.router import router as tools_router
from app.alerts.router import router as alerts_router
from app.audit.router import router as audit_router
from app.dashboard.router import router as dashboard_router
from app.permissions.router import router as permissions_router
from app.ingestion.router import router as uploads_router
from app.reporting.router import router as reports_router
from app.usage.router import router as usage_router
from app.api.v1.schemas import HealthResponse
from app.auth.router import router as auth_router
from app.config import get_settings
from app.connectivity import verify_connectivity

router = APIRouter()
router.include_router(auth_router)
router.include_router(tools_router)
router.include_router(credentials_router)
router.include_router(providers_router)
router.include_router(teams_router)
router.include_router(members_router)
router.include_router(uploads_router)
router.include_router(alerts_router)
router.include_router(reports_router)
router.include_router(audit_router)
router.include_router(dashboard_router)
router.include_router(permissions_router)
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

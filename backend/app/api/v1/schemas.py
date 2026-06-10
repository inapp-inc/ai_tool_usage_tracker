"""Health response schema aligned with OpenAPI HealthResponse."""

from typing import Literal

from pydantic import BaseModel

HealthStatus = Literal["ok", "degraded"]
DependencyStatus = Literal["ok", "error"]


class HealthResponse(BaseModel):
    """Service health status."""

    status: HealthStatus
    database: DependencyStatus | None = None
    redis: DependencyStatus | None = None

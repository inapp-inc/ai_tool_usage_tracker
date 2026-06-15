"""FastAPI entrypoint (TASK-INF-002)."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import get_settings
from app.connectivity import verify_connectivity
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Verify PostgreSQL and Redis on startup."""
    settings = get_settings()
    connectivity = await verify_connectivity(settings)
    if not connectivity.is_healthy:
        raise RuntimeError(
            "Startup connectivity check failed: "
            f"database={connectivity.database}, redis={connectivity.redis}"
        )
    yield


app = FastAPI(
    title="AI Tool Usage Tracker",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(v1_router, prefix="/api/v1")

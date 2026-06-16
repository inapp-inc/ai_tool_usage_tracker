"""FastAPI entrypoint with in-process token collector scheduler."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.auth.service import seed_dev_admin
from app.collector.scheduler import CollectorScheduler
from app.config import get_settings
from app.connectivity import verify_connectivity
from app.core.exceptions import register_exception_handlers
from app.db.session import dispose_engine, get_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Verify PostgreSQL, seed dev admin, start collector scheduler."""
    settings = get_settings()
    connectivity = await verify_connectivity(settings)
    if not connectivity.is_healthy:
        raise RuntimeError(
            "Startup connectivity check failed: "
            f"database={connectivity.database}"
        )

    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        await seed_dev_admin(session, settings)

    scheduler: CollectorScheduler | None = None
    if settings.collector_scheduler_enabled:
        scheduler = CollectorScheduler(session_factory)
        await scheduler.start()
        app.state.collector_scheduler = scheduler

    yield

    if scheduler is not None:
        await scheduler.shutdown()
    await dispose_engine()


app = FastAPI(
    title="AI Tool Usage Tracker",
    lifespan=lifespan,
)

_settings = get_settings()
_cors_kwargs: dict[str, object] = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
_cors_origins = _settings.resolved_cors_origins()
_cors_regex = _settings.cors_origin_regex()
if _cors_origins:
    _cors_kwargs["allow_origins"] = _cors_origins
if _cors_regex:
    _cors_kwargs["allow_origin_regex"] = _cors_regex
if not _cors_origins and not _cors_regex:
    _cors_kwargs["allow_origins"] = []

app.add_middleware(CORSMiddleware, **_cors_kwargs)

register_exception_handlers(app)
app.include_router(v1_router, prefix="/api/v1")

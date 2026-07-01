"""Background collector runs — immediate sync after connect and scheduled pulls."""

from __future__ import annotations

import logging
from uuid import UUID

from app.collector.service import CollectorService
from app.db.session import get_session_factory

logger = logging.getLogger(__name__)


async def run_collector_background(collector_id: UUID) -> None:
    """Execute a full usage pull for one collector (used after credential connect)."""
    factory = get_session_factory()
    async with factory() as session:
        service = CollectorService(session)
        try:
            run = await service.run_collector(collector_id)
            if run is None:
                logger.warning("Background collector run skipped — collector %s not found", collector_id)
                return
            logger.info(
                "Background collector run finished | collector_id=%s status=%s ingested=%s",
                collector_id,
                run.status,
                run.records_ingested,
            )
        except Exception:  # noqa: BLE001
            logger.exception("Background collector run failed | collector_id=%s", collector_id)


async def run_collector_for_tool_background(tool_id: UUID) -> None:
    """Resolve collector by connected tool id and run a pull."""
    factory = get_session_factory()
    async with factory() as session:
        service = CollectorService(session)
        from sqlalchemy import select

        from app.models.collector import CollectorConfig

        result = await session.execute(
            select(CollectorConfig).where(CollectorConfig.tool_id == tool_id)
        )
        collector = result.scalar_one_or_none()
        if collector is None:
            logger.warning("No collector for tool %s — skipping background pull", tool_id)
            return

    await run_collector_background(collector.id)

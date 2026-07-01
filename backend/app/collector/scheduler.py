"""In-process collector scheduler (runs inside the API container)."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.collector.service import CollectorService

logger = logging.getLogger(__name__)


class CollectorScheduler:
    """Schedule periodic token pulls per active collector config."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._job_ids: set[str] = set()

    async def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
        await self.reload()

    async def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def reload(self) -> None:
        """Reload interval jobs from database (call after create/update/delete)."""
        try:
            async with self._session_factory() as session:
                service = CollectorService(session)
                collectors = await service.list_active_collectors()
        except ProgrammingError as exc:
            logger.warning(
                "Collector scheduler skipped reload — database tables not ready: %s",
                exc.orig,
            )
            return

        active_ids = {str(c.id) for c in collectors}
        for job_id in list(self._job_ids):
            if job_id not in active_ids:
                self._scheduler.remove_job(job_id)
                self._job_ids.discard(job_id)

        for config in collectors:
            job_id = str(config.id)
            trigger = IntervalTrigger(minutes=config.pull_interval_minutes)
            self._scheduler.add_job(
                self._run_collector,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                kwargs={"collector_id": config.id},
                max_instances=1,
                coalesce=True,
                next_run_time=datetime.now(UTC),
            )
            self._job_ids.add(job_id)
            logger.info(
                "Scheduled collector %s every %s minutes",
                config.name,
                config.pull_interval_minutes,
            )

    async def _run_collector(self, collector_id: UUID) -> None:
        async with self._session_factory() as session:
            service = CollectorService(session)
            run = await service.run_collector(collector_id)
            if run is None:
                logger.warning("Collector %s not found during scheduled run", collector_id)
                return
            logger.info(
                "Collector %s run %s: status=%s ingested=%s",
                collector_id,
                run.id,
                run.status,
                run.records_ingested,
            )

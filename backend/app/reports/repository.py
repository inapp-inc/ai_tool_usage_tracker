"""Report job data access."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reporting import ReportJob, ReportSubscription


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_organization(self, organization_id: UUID) -> list[ReportJob]:
        result = await self._session.execute(
            select(ReportJob)
            .where(ReportJob.organization_id == organization_id)
            .order_by(ReportJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, job_id: UUID, organization_id: UUID) -> ReportJob | None:
        result = await self._session.execute(
            select(ReportJob).where(
                ReportJob.id == job_id,
                ReportJob.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, row: ReportJob) -> ReportJob:
        self._session.add(row)
        await self._session.flush()
        return row

    async def delete(self, row: ReportJob) -> None:
        await self._session.delete(row)
        await self._session.flush()

    async def subscription_count(self, report_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(ReportSubscription.id)).where(
                ReportSubscription.report_id == report_id
            )
        )
        return int(result.scalar_one())


class SubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_report(self, report_id: UUID, organization_id: UUID) -> list[ReportSubscription]:
        result = await self._session.execute(
            select(ReportSubscription)
            .where(
                ReportSubscription.report_id == report_id,
                ReportSubscription.organization_id == organization_id,
            )
            .order_by(ReportSubscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        subscription_id: UUID,
        report_id: UUID,
        organization_id: UUID,
    ) -> ReportSubscription | None:
        result = await self._session.execute(
            select(ReportSubscription).where(
                ReportSubscription.id == subscription_id,
                ReportSubscription.report_id == report_id,
                ReportSubscription.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, row: ReportSubscription) -> ReportSubscription:
        self._session.add(row)
        await self._session.flush()
        return row

    async def delete(self, row: ReportSubscription) -> None:
        await self._session.delete(row)
        await self._session.flush()

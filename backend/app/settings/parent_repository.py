"""Provider parent company data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import ProviderParent


class ProviderParentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_parents(self) -> list[ProviderParent]:
        result = await self._session.execute(
            select(ProviderParent).order_by(ProviderParent.sort_order.asc(), ProviderParent.label.asc())
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> ProviderParent | None:
        return await self._session.get(ProviderParent, slug)

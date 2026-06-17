"""Provider lookup data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Provider


class ProviderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_providers(self, *, active: bool | None = None) -> list[Provider]:
        stmt = select(Provider).order_by(Provider.sort_order.asc(), Provider.label.asc())
        if active is not None:
            stmt = stmt.where(Provider.active == active)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Provider | None:
        result = await self._session.execute(
            select(Provider).where(Provider.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        slug: str,
        label: str,
        description: str | None,
        logo_url: str | None,
        sort_order: int,
    ) -> Provider:
        provider = Provider(
            slug=slug,
            label=label.strip(),
            description=description.strip() if description else None,
            logo_url=logo_url.strip() if logo_url else None,
            built_in=False,
            active=True,
            sort_order=sort_order,
        )
        self._session.add(provider)
        await self._session.flush()
        return provider

    async def delete(self, provider: Provider) -> None:
        await self._session.delete(provider)

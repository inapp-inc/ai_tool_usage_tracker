"""Provider registry data access."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import CursorError, decode_cursor, encode_cursor
from app.models.admin import Provider, Tool


class ProviderRepository:
    """CRUD for admin.providers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_providers(
        self,
        organization_id: uuid.UUID,
        *,
        active: bool | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Provider], str | None]:
        stmt = select(Provider).where(Provider.organization_id == organization_id)
        if active is not None:
            stmt = stmt.where(Provider.active == active)

        if cursor:
            try:
                parts = decode_cursor(cursor)
                cursor_name = parts["name"]
                cursor_id = uuid.UUID(parts["id"])
            except (CursorError, KeyError, ValueError) as exc:
                raise CursorError("Invalid pagination cursor") from exc
            stmt = stmt.where(
                tuple_(Provider.name, Provider.id) > tuple_(cursor_name, cursor_id)
            )

        stmt = stmt.order_by(Provider.name.asc(), Provider.id.asc()).limit(limit + 1)
        rows = list((await self._session.scalars(stmt)).all())

        next_cursor = None
        if len(rows) > limit:
            last = rows[limit - 1]
            next_cursor = encode_cursor(name=last.name, id=str(last.id))
            rows = rows[:limit]

        return rows, next_cursor

    async def get_by_id(
        self, organization_id: uuid.UUID, provider_id: uuid.UUID
    ) -> Provider | None:
        stmt = select(Provider).where(
            Provider.organization_id == organization_id,
            Provider.id == provider_id,
        )
        return await self._session.scalar(stmt)

    async def get_by_slug(
        self, organization_id: uuid.UUID, slug: str
    ) -> Provider | None:
        stmt = select(Provider).where(
            Provider.organization_id == organization_id,
            Provider.slug == slug,
        )
        return await self._session.scalar(stmt)

    async def count_by_slug(self, organization_id: uuid.UUID, slug: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Provider)
            .where(
                Provider.organization_id == organization_id,
                Provider.slug == slug,
            )
        )
        return int(await self._session.scalar(stmt) or 0)

    async def count_tools_using_vendor(
        self, organization_id: uuid.UUID, slug: str
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Tool)
            .where(
                Tool.organization_id == organization_id,
                Tool.vendor == slug,
            )
        )
        return int(await self._session.scalar(stmt) or 0)

    async def add(self, provider: Provider) -> Provider:
        self._session.add(provider)
        await self._session.flush()
        return provider

    async def save(self, provider: Provider) -> Provider:
        await self._session.flush()
        return provider

    async def delete(self, provider: Provider) -> None:
        await self._session.delete(provider)
        await self._session.flush()

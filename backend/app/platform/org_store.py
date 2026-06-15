"""Persist org-scoped lists in organization.settings JSONB."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repositories.organization import OrganizationRepository


class OrgDataStore:
    """Read/write named collections on organization.settings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._orgs = OrganizationRepository(session)

    async def list_items(
        self, organization_id: uuid.UUID, key: str
    ) -> list[dict[str, Any]]:
        org = await self._orgs.get_by_id(organization_id)
        if org is None:
            return []
        settings = dict(org.settings or {})
        items = settings.get(key, [])
        return list(items) if isinstance(items, list) else []

    async def save_items(
        self,
        organization_id: uuid.UUID,
        key: str,
        items: list[dict[str, Any]],
    ) -> None:
        org = await self._orgs.get_by_id(organization_id)
        if org is None:
            return
        settings = dict(org.settings or {})
        settings[key] = items
        org.settings = settings
        await self._session.flush()

    async def append_item(
        self,
        organization_id: uuid.UUID,
        key: str,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        items = await self.list_items(organization_id, key)
        items.insert(0, item)
        await self.save_items(organization_id, key, items)
        return item

    async def update_item(
        self,
        organization_id: uuid.UUID,
        key: str,
        item_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        items = await self.list_items(organization_id, key)
        for index, item in enumerate(items):
            if str(item.get("id")) == item_id:
                merged = {**item, **updates, "id": item_id}
                items[index] = merged
                await self.save_items(organization_id, key, items)
                return merged
        return None

    async def delete_item(
        self, organization_id: uuid.UUID, key: str, item_id: str
    ) -> bool:
        items = await self.list_items(organization_id, key)
        filtered = [item for item in items if str(item.get("id")) != item_id]
        if len(filtered) == len(items):
            return False
        await self.save_items(organization_id, key, filtered)
        return True

    async def get_item(
        self, organization_id: uuid.UUID, key: str, item_id: str
    ) -> dict[str, Any] | None:
        for item in await self.list_items(organization_id, key):
            if str(item.get("id")) == item_id:
                return deepcopy(item)
        return None

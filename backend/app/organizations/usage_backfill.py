"""Backfill tenant organization_id on usage rows missing attribution."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Tool
from app.models.collector import UsageEvent

logger = logging.getLogger(__name__)


async def backfill_usage_event_organization_ids(session: AsyncSession) -> int:
    """Set UsageEvent.organization_id from connected tool where missing."""
    result = await session.execute(
        select(UsageEvent.id, UsageEvent.tool_id).where(
            UsageEvent.organization_id.is_(None),
            UsageEvent.tool_id.is_not(None),
        )
    )
    rows = result.all()
    if not rows:
        return 0

    tool_ids = {tool_id for _, tool_id in rows if tool_id is not None}
    tools_result = await session.execute(select(Tool).where(Tool.id.in_(tool_ids)))
    org_by_tool: dict[UUID, UUID] = {
        tool.id: tool.organization_id for tool in tools_result.scalars().all()
    }

    updated = 0
    for event_id, tool_id in rows:
        org_id = org_by_tool.get(tool_id) if tool_id is not None else None
        if org_id is None:
            continue
        await session.execute(
            update(UsageEvent)
            .where(UsageEvent.id == event_id)
            .values(organization_id=org_id)
        )
        updated += 1

    if updated:
        await session.flush()
        logger.info("Backfilled organization_id on %s usage events", updated)
    return updated

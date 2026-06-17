"""Background jobs for tool usage sync."""

from __future__ import annotations

import logging
from uuid import UUID

from app.db.session import get_session_factory
from app.tools.service import ToolService

logger = logging.getLogger(__name__)


async def run_tool_sync_background(organization_id: UUID, tool_id: UUID) -> None:
    """Pull provider usage/members after a credential is connected."""
    factory = get_session_factory()
    async with factory() as session:
        service = ToolService(session)
        try:
            await service.sync_tool(organization_id, tool_id)
            logger.info("Background sync completed for tool %s", tool_id)
        except Exception:  # noqa: BLE001
            logger.exception("Background sync failed for tool %s", tool_id)

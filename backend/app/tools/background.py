"""Background jobs for tool usage sync."""

from __future__ import annotations

import logging
from uuid import UUID

from app.db.session import get_session_factory
from app.teams.team_tool_service import TeamToolService
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


async def run_team_sync_background(organization_id: UUID, team_id: UUID) -> None:
    """Pull usage/members for all connected credentials assigned to a team."""
    logger.info(
        "Background team sync started | org=%s team_id=%s",
        organization_id,
        team_id,
    )
    factory = get_session_factory()
    async with factory() as session:
        service = TeamToolService(session)
        try:
            result = await service.sync_team_tools_for_organization(organization_id, team_id)
            logger.info(
                "Background team sync completed | team_id=%s synced=%s skipped=%s failed=%s",
                team_id,
                result.synced_count,
                result.skipped_count,
                result.failed_count,
            )
        except Exception:  # noqa: BLE001
            logger.exception("Background team sync failed for team %s", team_id)

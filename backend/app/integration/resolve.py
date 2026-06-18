"""Resolve integration_config and api_endpoint from a tool or its catalogue parent."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Tool
from app.tools.catalogue import catalogue_tool_id_from_connected


def integration_config_from_tool(tool: Tool | None) -> dict:
    if tool is None:
        return {}
    raw = tool.integration_config
    if isinstance(raw, dict) and raw.get("usage"):
        return dict(raw)
    return {}


async def resolve_tool_polling_context(
    session: AsyncSession,
    tool: Tool | None,
) -> tuple[dict, str | None, dict]:
    """Return (pricing_config, api_endpoint, integration_config) for usage polling."""
    if tool is None:
        return {}, None, {}

    pricing_config = dict(tool.pricing_config) if isinstance(tool.pricing_config, dict) else {}
    api_endpoint = tool.api_endpoint
    integration_config = integration_config_from_tool(tool)

    if not integration_config.get("usage"):
        catalogue_id = catalogue_tool_id_from_connected(tool)
        if catalogue_id is not None:
            catalogue = await session.get(Tool, catalogue_id)
            if catalogue is not None:
                if not api_endpoint:
                    api_endpoint = catalogue.api_endpoint
                catalogue_config = integration_config_from_tool(catalogue)
                if catalogue_config.get("usage"):
                    integration_config = catalogue_config

    if api_endpoint:
        pricing_config.setdefault("api_endpoint", api_endpoint)
    if integration_config:
        pricing_config["integration_config"] = integration_config

    return pricing_config, api_endpoint, integration_config

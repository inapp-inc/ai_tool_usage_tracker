"""Resolve catalogue tools vs connected credential records."""

from uuid import UUID

from app.models.admin import Tool


def catalogue_tool_id_from_connected(tool: Tool) -> UUID | None:
    """Return the catalogue tool id for a connected tool, or the tool id if already catalogue."""
    if tool.catalogue_only:
        return tool.id
    config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
    raw = config.get("catalogue_tool_id")
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def connected_to_catalogue_map(tools: list[Tool]) -> dict[UUID, UUID]:
    """Map any tool id (connected or catalogue) to its catalogue tool id."""
    mapping: dict[UUID, UUID] = {}
    for tool in tools:
        if tool.catalogue_only:
            mapping[tool.id] = tool.id
            continue
        catalogue_id = catalogue_tool_id_from_connected(tool)
        if catalogue_id is not None:
            mapping[tool.id] = catalogue_id
    return mapping


def team_id_from_connected(tool: Tool) -> UUID | None:
    config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
    raw = config.get("team_id")
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def find_connected_for_catalogue(tools: list[Tool], catalogue_tool_id: UUID) -> Tool | None:
    matches = find_all_connected_for_catalogue(tools, catalogue_tool_id)
    return matches[0] if matches else None


def find_all_connected_for_catalogue(
    tools: list[Tool],
    catalogue_tool_id: UUID,
) -> list[Tool]:
    return [
        tool
        for tool in tools
        if not tool.catalogue_only and catalogue_tool_id_from_connected(tool) == catalogue_tool_id
    ]


def find_connected_for_team(
    tools: list[Tool],
    *,
    team_id: UUID,
    catalogue_tool_ids: set[UUID],
    id_to_catalogue: dict[UUID, UUID] | None = None,
) -> list[Tool]:
    """All active connected credentials for a team (by team_id and/or assigned catalogue tools)."""
    normalized_catalogue_ids: set[UUID] = set()
    for raw_id in catalogue_tool_ids:
        if id_to_catalogue is not None:
            normalized_catalogue_ids.add(id_to_catalogue.get(raw_id, raw_id))
        else:
            normalized_catalogue_ids.add(raw_id)

    results: list[Tool] = []
    seen: set[UUID] = set()
    for tool in tools:
        if tool.catalogue_only or not tool.active or tool.id in seen:
            continue

        assigned_team_id = team_id_from_connected(tool)
        catalogue_id = catalogue_tool_id_from_connected(tool)

        if assigned_team_id == team_id:
            results.append(tool)
            seen.add(tool.id)
            continue

        if (
            catalogue_id is not None
            and catalogue_id in normalized_catalogue_ids
            and (assigned_team_id is None or assigned_team_id == team_id)
        ):
            results.append(tool)
            seen.add(tool.id)

    return sorted(results, key=lambda row: (row.name or "").lower())


def usage_tool_ids_for_filter(tools: list[Tool], tool_id: UUID) -> list[UUID]:
    """Expand a catalogue tool id to connected tool ids used in usage events."""
    tool = next((row for row in tools if row.id == tool_id), None)
    if tool is None:
        return [tool_id]
    if not tool.catalogue_only:
        return [tool_id]
    connected_ids = [
        row.id
        for row in tools
        if not row.catalogue_only and catalogue_tool_id_from_connected(row) == tool_id
    ]
    return connected_ids or [tool_id]

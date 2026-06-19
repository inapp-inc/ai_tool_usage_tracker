"""Tests for catalogue vs connected tool resolution."""

from uuid import uuid4

from app.models.admin import Tool
from app.tools.catalogue import (
    catalogue_tool_id_from_connected,
    connected_to_catalogue_map,
    find_connected_for_catalogue,
    usage_tool_ids_for_filter,
)


def _make_tool(**overrides) -> Tool:
    tool = Tool(
        organization_id=uuid4(),
        name=overrides.get("name", "Tool"),
        vendor="openai",
        description=None,
        api_endpoint=None,
        pricing_model="flat_token",
        token_price=0,
        package_allowance=None,
        overage_price=None,
        pricing_config=overrides.get("pricing_config", {}),
        active=True,
        api_token_ciphertext="",
        sync_status="inactive",
        catalogue_only=overrides.get("catalogue_only", False),
    )
    tool.id = overrides.get("id", uuid4())
    return tool


def test_catalogue_tool_id_from_connected() -> None:
    catalogue_id = uuid4()
    connected = _make_tool(
        catalogue_only=False,
        pricing_config={"catalogue_tool_id": str(catalogue_id)},
    )

    assert catalogue_tool_id_from_connected(connected) == catalogue_id


def test_connected_to_catalogue_map() -> None:
    catalogue = _make_tool(catalogue_only=True)
    connected = _make_tool(
        catalogue_only=False,
        pricing_config={"catalogue_tool_id": str(catalogue.id)},
    )

    mapping = connected_to_catalogue_map([catalogue, connected])

    assert mapping[catalogue.id] == catalogue.id
    assert mapping[connected.id] == catalogue.id


def test_find_connected_for_catalogue() -> None:
    catalogue = _make_tool(catalogue_only=True)
    connected = _make_tool(
        catalogue_only=False,
        pricing_config={"catalogue_tool_id": str(catalogue.id)},
    )

    found = find_connected_for_catalogue([catalogue, connected], catalogue.id)

    assert found is connected


def test_find_connected_for_team_matches_by_team_id() -> None:
    team_id = uuid4()
    catalogue_id = uuid4()

    connected = _make_tool(
        catalogue_only=False,
        pricing_config={
            "catalogue_tool_id": str(catalogue_id),
            "team_id": str(team_id),
        },
    )

    from app.tools.catalogue import find_connected_for_team

    results = find_connected_for_team(
        [connected],
        team_id=team_id,
        catalogue_tool_ids=set(),
    )

    assert results == [connected]


def test_find_connected_for_team_filters_by_team_and_catalogue() -> None:
    team_id = uuid4()
    other_team_id = uuid4()
    catalogue_id = uuid4()
    other_catalogue_id = uuid4()

    matching = _make_tool(
        catalogue_only=False,
        pricing_config={
            "catalogue_tool_id": str(catalogue_id),
            "team_id": str(team_id),
        },
    )
    wrong_team = _make_tool(
        catalogue_only=False,
        pricing_config={
            "catalogue_tool_id": str(catalogue_id),
            "team_id": str(other_team_id),
        },
    )
    wrong_tool = _make_tool(
        catalogue_only=False,
        pricing_config={
            "catalogue_tool_id": str(other_catalogue_id),
            "team_id": str(team_id),
        },
    )

    from app.tools.catalogue import find_connected_for_team

    results = find_connected_for_team(
        [matching, wrong_team, wrong_tool],
        team_id=team_id,
        catalogue_tool_ids={catalogue_id},
    )

    assert results == [matching, wrong_tool]


def test_usage_tool_ids_for_filter_expands_catalogue() -> None:
    catalogue = _make_tool(catalogue_only=True)
    connected = _make_tool(
        catalogue_only=False,
        pricing_config={"catalogue_tool_id": str(catalogue.id)},
    )

    ids = usage_tool_ids_for_filter([catalogue, connected], catalogue.id)

    assert set(ids) == {catalogue.id, connected.id}

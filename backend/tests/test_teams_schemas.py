"""Unit tests for team request schemas."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.teams.schemas import TeamCreateRequest, TeamUpdateRequest


def test_team_create_request_includes_form_fields() -> None:
    body = TeamCreateRequest(
        name="Engineering",
        description="Platform team",
        token_budget=5_000_000,
        cost_budget=Decimal("500.00"),
        tool_ids=["tool_1", "tool_2", "tool_1"],
    )
    assert body.token_budget == 5_000_000
    assert body.cost_budget == Decimal("500.00")
    assert body.tool_ids == ["tool_1", "tool_2"]


def test_team_create_request_rejects_non_positive_token_budget() -> None:
    with pytest.raises(ValidationError):
        TeamCreateRequest(name="Engineering", token_budget=0)


def test_team_update_request_partial_fields() -> None:
    body = TeamUpdateRequest(tool_ids=["tool_3"], cost_budget=None)
    assert body.tool_ids == ["tool_3"]
    assert body.cost_budget is None
    assert body.name is None

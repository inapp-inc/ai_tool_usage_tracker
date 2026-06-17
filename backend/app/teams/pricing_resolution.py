"""Resolve effective pricing for a team–tool pair."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.models.admin import TeamTool, Tool


@dataclass(frozen=True)
class ResolvedTeamToolPricing:
    pricing_model: str
    token_price: Decimal
    output_token_price: Decimal | None
    cost_per_seat: Decimal | None
    seat_count: int | None
    package_allowance: int | None
    overage_price: Decimal | None
    plan_name: str | None
    pricing_config: dict[str, Any]
    source: str  # "team_tool" | "tool_default"


def _tool_config(tool: Tool) -> dict[str, Any]:
    return dict(tool.pricing_config) if isinstance(tool.pricing_config, dict) else {}


def _assignment_config(assignment: TeamTool) -> dict[str, Any]:
    return dict(assignment.pricing_config) if isinstance(assignment.pricing_config, dict) else {}


def _pick(team_value, tool_value, default=None):
    if team_value is not None:
        return team_value
    if tool_value is not None:
        return tool_value
    return default


def resolve_team_tool_pricing(
    assignment: TeamTool | None,
    tool: Tool,
) -> ResolvedTeamToolPricing:
    """Prefer team-tool pricing; fall back to tool defaults; zero-cost last."""
    tool_config = _tool_config(tool)

    if assignment is None or not assignment.pricing_model:
        return ResolvedTeamToolPricing(
            pricing_model=tool.pricing_model,
            token_price=tool.token_price,
            output_token_price=_decimal_or_none(tool_config.get("output_cost_per_1k")),
            cost_per_seat=_decimal_or_none(tool_config.get("cost_per_seat")),
            seat_count=_int_or_none(tool_config.get("seat_count")),
            package_allowance=tool.package_allowance,
            overage_price=tool.overage_price,
            plan_name=_str_or_none(tool_config.get("plan_name")),
            pricing_config=tool_config,
            source="tool_default",
        )

    assignment_config = _assignment_config(assignment)
    merged_config = {**tool_config, **assignment_config}

    return ResolvedTeamToolPricing(
        pricing_model=assignment.pricing_model,
        token_price=assignment.token_price if assignment.token_price is not None else tool.token_price,
        output_token_price=_pick(
            assignment.output_token_price,
            _decimal_or_none(tool_config.get("output_cost_per_1k")),
        ),
        cost_per_seat=_pick(
            assignment.cost_per_seat,
            _decimal_or_none(tool_config.get("cost_per_seat")),
        ),
        seat_count=_pick(
            assignment.seat_count,
            _int_or_none(tool_config.get("seat_count")),
        ),
        package_allowance=_pick(assignment.package_allowance, tool.package_allowance),
        overage_price=_pick(assignment.overage_price, tool.overage_price),
        plan_name=_pick(assignment.plan_name, _str_or_none(tool_config.get("plan_name"))),
        pricing_config=merged_config,
        source="team_tool",
    )


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

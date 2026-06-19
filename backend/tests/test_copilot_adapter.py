"""Tests for GitHub Copilot usage parsing."""

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.copilot_parsing import (
    parse_copilot_seat,
    parse_copilot_seat_members,
    parse_copilot_user_day,
)


def test_parse_copilot_seat_members_dedupes_logins() -> None:
    seats = [
        {"assignee": {"login": "dev-one"}},
        {"assignee": {"login": "dev-one"}},
        {"assignee": {"login": "dev-two"}},
    ]
    members = parse_copilot_seat_members(seats)
    assert [member.email for member in members] == ["dev-one", "dev-two"]


def test_parse_copilot_seat_uses_last_activity() -> None:
    seat = {
        "assignee": {"login": "kavya-sasikala-inapp"},
        "last_activity_at": "2026-06-16T09:44:43Z",
        "plan_type": "business",
        "last_activity_editor": "vscode/1.122.1/copilot-chat/0.50.1",
    }
    record = parse_copilot_seat(seat, fallback_at=datetime.now(UTC))
    assert record is not None
    assert record.user_email == "kavya-sasikala-inapp"
    assert record.input_tokens == 1
    assert "vscode" in record.model


def test_parse_copilot_user_day_extracts_token_usage() -> None:
    row = {
        "user_login": "octocat",
        "day": "2026-06-01",
        "used_cli": True,
        "totals_by_cli": {
            "token_usage": {
                "prompt_tokens_sum": 3800,
                "output_tokens_sum": 5000,
            }
        },
    }
    record = parse_copilot_user_day(row)
    assert record is not None
    assert record.user_email == "octocat"
    assert record.input_tokens == 3800
    assert record.output_tokens == 5000
    assert record.total_tokens == 8800
    assert record.estimated_cost == Decimal("0")

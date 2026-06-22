"""Tests for Copilot productivity field parsing."""

from app.copilot.productivity_parser import parse_seat_row, parse_user_metrics_row


def test_parse_user_metrics_row_maps_productivity_fields() -> None:
    row = {
        "user_login": "dev1",
        "day": "2026-06-01",
        "used_chat": True,
        "user_initiated_interaction_count": 5,
        "code_generation_activity_count": 20,
        "code_acceptance_activity_count": 14,
        "loc_suggested_to_add_sum": 100,
        "loc_added_sum": 80,
    }
    parsed = parse_user_metrics_row(row)
    assert parsed is not None
    assert parsed.user_login == "dev1"
    assert parsed.chat_turns == 5
    assert parsed.suggestions_count == 20
    assert parsed.acceptances_count == 14
    assert parsed.acceptance_rate is not None
    assert float(parsed.acceptance_rate) == 70.0


def test_parse_seat_row_maps_assignee() -> None:
    seat = {
        "assignee": {"login": "alice"},
        "created_at": "2026-01-01T00:00:00Z",
        "last_activity_at": "2026-06-01T12:00:00Z",
    }
    parsed = parse_seat_row(seat)
    assert parsed is not None
    assert parsed.user_login == "alice"
    assert parsed.seat_status == "assigned"

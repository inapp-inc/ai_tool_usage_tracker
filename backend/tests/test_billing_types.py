"""Tests for vendor billing type mapping."""

from app.tools.billing_types import billing_type_for_vendor


def test_openai_is_token_based() -> None:
    assert billing_type_for_vendor("openai") == "TOKEN_BASED"


def test_cursor_is_request_based() -> None:
    assert billing_type_for_vendor("cursor") == "REQUEST_BASED"


def test_copilot_is_seat_based() -> None:
    assert billing_type_for_vendor("copilot") == "SEAT_BASED"


def test_unknown_vendor_defaults_to_token_based() -> None:
    assert billing_type_for_vendor("unknown_vendor") == "TOKEN_BASED"

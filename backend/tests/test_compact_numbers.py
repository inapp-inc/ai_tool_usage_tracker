"""Tests for compact numeric parsing (K/M suffixes)."""

from app.integration.mapping import map_record, parse_int
from app.integration.numbers import parse_compact_int


def test_parse_compact_int_plain_number() -> None:
    assert parse_compact_int("1500") == 1500
    assert parse_compact_int(1500) == 1500
    assert parse_compact_int("1,500") == 1500


def test_parse_compact_int_k_suffix() -> None:
    assert parse_compact_int("15K") == 15_000
    assert parse_compact_int("15k") == 15_000
    assert parse_compact_int("1.5K") == 1_500


def test_parse_compact_int_m_suffix() -> None:
    assert parse_compact_int("2M") == 2_000_000
    assert parse_compact_int("1.2m") == 1_200_000


def test_parse_compact_int_invalid_returns_default() -> None:
    assert parse_compact_int("n/a", default=0) == 0
    assert parse_compact_int("", default=7) == 7


def test_map_record_parses_k_suffix_tokens() -> None:
    record = {"id": "evt-1", "date": "2026-06-01", "usage": "15K"}
    mapped = map_record(
        record,
        {
            "vendor_event_id": "id",
            "occurred_at": "date",
            "input_tokens": "usage",
            "output_tokens": "0",
            "estimated_cost": "0",
            "model": "default",
        },
    )
    assert mapped["input_tokens"] == 15_000


def test_parse_int_delegates_to_compact_parser() -> None:
    assert parse_int("3.2K") == 3_200

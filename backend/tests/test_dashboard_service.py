"""Unit tests for dashboard analytics helpers."""

from app.dashboard.service import _pct_delta, _previous_period, effective_token_total
from datetime import UTC, datetime


def test_effective_token_total_sums_input_and_output() -> None:
    assert effective_token_total(1_250_000, 980_000) == 2_230_000
    assert effective_token_total(0, 0) == 0


def test_pct_delta_handles_zero_previous() -> None:
    assert _pct_delta(100, 0) == 100.0
    assert _pct_delta(0, 0) == 0.0


def test_pct_delta_calculates_change() -> None:
    assert _pct_delta(150, 100) == 50.0
    assert _pct_delta(50, 100) == -50.0


def test_previous_period_same_duration() -> None:
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 30, 23, 59, 59, tzinfo=UTC)
    prev_from, prev_to = _previous_period(start, end)
    assert (end - start) == (prev_to - prev_from)
    assert prev_to < start

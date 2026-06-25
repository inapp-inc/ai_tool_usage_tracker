"""Tests for Anthropic Admin API query parameters."""

from datetime import UTC, datetime

from app.collector.adapters.anthropic_query import anthropic_usage_query_params


def test_anthropic_usage_query_params_use_bracket_group_by_and_snap_timestamps() -> None:
    since = datetime(2026, 5, 23, 13, 24, 47, 190157, tzinfo=UTC)
    until = datetime(2026, 6, 22, 13, 24, 47, 190157, tzinfo=UTC)
    params = anthropic_usage_query_params(since, until)
    param_map = dict(params)

    assert param_map["starting_at"] == "2026-05-23T00:00:00Z"
    assert param_map["ending_at"] == "2026-06-23T00:00:00Z"
    assert param_map["bucket_width"] == "1d"
    assert param_map["limit"] == 31
    assert ("group_by[]", "model") in params
    assert ("group_by[]", "account_id") in params


def test_anthropic_usage_query_params_limit_matches_day_span() -> None:
    since = datetime(2026, 6, 1, 15, 0, tzinfo=UTC)
    until = datetime(2026, 6, 10, 9, 30, tzinfo=UTC)
    params = dict(anthropic_usage_query_params(since, until))

    assert params["starting_at"] == "2026-06-01T00:00:00Z"
    assert params["ending_at"] == "2026-06-11T00:00:00Z"
    assert params["limit"] == 10

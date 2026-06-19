"""Shared token total helpers for usage events."""

from sqlalchemy import ColumnElement

from app.models.collector import UsageEvent


def usage_event_token_total_sql() -> ColumnElement[int]:
    """SQL expression for full token count including cache columns."""
    return (
        UsageEvent.input_tokens
        + UsageEvent.output_tokens
        + UsageEvent.cache_write_tokens
        + UsageEvent.cache_read_tokens
    )


def usage_event_token_total(
    *,
    input_tokens: int,
    output_tokens: int,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> int:
    """Python-side full token count for a usage row."""
    return input_tokens + output_tokens + cache_write_tokens + cache_read_tokens

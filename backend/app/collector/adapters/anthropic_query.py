"""Anthropic Admin API query parameter helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def snap_to_bucket_start(dt: datetime, bucket_width: str) -> datetime:
    dt = dt.astimezone(UTC).replace(microsecond=0)
    if bucket_width == "1d":
        return dt.replace(hour=0, minute=0, second=0)
    if bucket_width == "1h":
        return dt.replace(minute=0, second=0)
    return dt.replace(second=0)


def format_anthropic_rfc3339(dt: datetime, *, bucket_width: str) -> str:
    return snap_to_bucket_start(dt, bucket_width).strftime("%Y-%m-%dT%H:%M:%SZ")


def anthropic_usage_query_params(
    since: datetime,
    until: datetime,
    *,
    group_by: tuple[str, ...] = ("model", "account_id"),
) -> list[tuple[str, str | int]]:
    """Build query params for GET /v1/organizations/usage_report/messages."""
    range_seconds = max(int(until.timestamp()) - int(since.timestamp()), 60)
    if range_seconds >= 2 * 86400:
        bucket_width = "1d"
        max_limit = 31
    elif range_seconds >= 2 * 3600:
        bucket_width = "1h"
        max_limit = 168
    else:
        bucket_width = "1m"
        max_limit = 1440

    start = snap_to_bucket_start(since, bucket_width)
    end = snap_to_bucket_start(until, bucket_width)
    if until.astimezone(UTC) > end:
        if bucket_width == "1d":
            end = end + timedelta(days=1)
        elif bucket_width == "1h":
            end = end + timedelta(hours=1)
        else:
            end = end + timedelta(minutes=1)

    if bucket_width == "1d":
        bucket_count = max(1, (end.date() - start.date()).days)
    elif bucket_width == "1h":
        bucket_count = max(1, int((end - start).total_seconds() // 3600))
    else:
        bucket_count = max(1, int((end - start).total_seconds() // 60))

    limit = min(max_limit, bucket_count)

    params: list[tuple[str, str | int]] = [
        ("starting_at", format_anthropic_rfc3339(start, bucket_width=bucket_width)),
        ("ending_at", format_anthropic_rfc3339(end, bucket_width=bucket_width)),
        ("bucket_width", bucket_width),
        ("limit", limit),
    ]
    for field in group_by:
        params.append(("group_by[]", field))
    return params


def anthropic_cost_query_params(
    since: datetime,
    until: datetime,
) -> list[tuple[str, str | int]]:
    """Build query params for GET /v1/organizations/cost_report."""
    start = snap_to_bucket_start(since, "1d")
    end = snap_to_bucket_start(until, "1d")
    if until.astimezone(UTC) > end:
        end = end + timedelta(days=1)
    bucket_count = max(1, (end.date() - start.date()).days)
    limit = min(31, bucket_count)
    return [
        ("starting_at", format_anthropic_rfc3339(start, bucket_width="1d")),
        ("ending_at", format_anthropic_rfc3339(end, bucket_width="1d")),
        ("bucket_width", "1d"),
        ("limit", limit),
    ]


def usage_param_fallbacks(
    since: datetime,
    until: datetime,
) -> list[list[tuple[str, str | int]]]:
    """Progressively simpler query shapes when Anthropic returns HTTP 400."""
    return [
        anthropic_usage_query_params(since, until, group_by=("model", "account_id")),
        anthropic_usage_query_params(since, until, group_by=("model",)),
        anthropic_usage_query_params(since, until, group_by=()),
    ]

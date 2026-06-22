"""Fetch Gemini token usage from Google Cloud Monitoring quota metrics."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urlencode

from app.collector.adapters.http_utils import get_with_detail

logger = logging.getLogger(__name__)

MONITORING_BASE = "https://monitoring.googleapis.com/v3"
GEMINI_SERVICE = "generativelanguage.googleapis.com"
QUOTA_USAGE_METRIC = "serviceruntime.googleapis.com/quota/rate/net_usage"

_INPUT_TOKEN_RE = re.compile(r"input_token", re.IGNORECASE)
_OUTPUT_TOKEN_RE = re.compile(r"output_token", re.IGNORECASE)
_REQUEST_RE = re.compile(r"requests?$", re.IGNORECASE)


def resolve_gcp_project_id(pricing_config: dict | None, service_account: dict[str, Any]) -> str:
    config = pricing_config or {}
    for key in ("gcp_project_id", "google_cloud_project_id", "project_id"):
        value = str(config.get(key) or "").strip()
        if value:
            return value
    return str(service_account["project_id"]).strip()


def resolve_service_account_from_config(
    pricing_config: dict | None,
    *,
    api_token: str,
) -> dict[str, Any] | None:
    from app.collector.adapters.google_gcp_auth import parse_service_account_json

    config = pricing_config or {}
    for key in ("gcp_service_account_json", "google_service_account_json", "service_account_json"):
        raw = config.get(key)
        if raw:
            try:
                return parse_service_account_json(raw)
            except ValueError:
                continue

    token = api_token.strip()
    if token.startswith("{"):
        try:
            return parse_service_account_json(token)
        except ValueError:
            return None
    return None


def _parse_rfc3339(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(UTC)


def _metric_direction(quota_metric: str) -> str | None:
    name = quota_metric.rsplit("/", 1)[-1]
    if _INPUT_TOKEN_RE.search(name):
        return "input"
    if _OUTPUT_TOKEN_RE.search(name):
        return "output"
    if _REQUEST_RE.search(name):
        return "requests"
    return None


def _daily_usage_from_points(points: list[dict[str, Any]]) -> dict[date, int]:
    """Convert monotonic quota counter points into per-day deltas."""
    if not points:
        return {}

    parsed: list[tuple[datetime, int]] = []
    for point in points:
        interval = point.get("interval") or {}
        end_raw = interval.get("endTime") or interval.get("startTime")
        value = point.get("value") or {}
        amount = value.get("int64Value") or value.get("doubleValue") or 0
        if end_raw is None:
            continue
        try:
            parsed.append((_parse_rfc3339(str(end_raw)), int(amount)))
        except (TypeError, ValueError):
            continue

    parsed.sort(key=lambda row: row[0])
    if not parsed:
        return {}

    daily: dict[date, int] = defaultdict(int)
    previous_value: int | None = None
    previous_day: date | None = None

    for occurred_at, amount in parsed:
        day = occurred_at.date()
        if previous_value is None:
            daily[day] += max(amount, 0)
        elif day == previous_day:
            delta = amount - previous_value
            if delta >= 0:
                daily[day] += delta
        else:
            # Counter reset at day boundary — treat as fresh cumulative for the day.
            daily[day] += max(amount, 0)
        previous_value = amount
        previous_day = day

    return dict(daily)


def _merge_usage_rows(rows: dict[tuple[date, str], dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for (day, model), payload in sorted(rows.items()):
        input_tokens = int(payload.get("promptTokenCount") or 0)
        output_tokens = int(payload.get("candidatesTokenCount") or 0)
        requests = int(payload.get("requests") or 0)
        if input_tokens == 0 and output_tokens == 0 and requests == 0:
            continue
        occurred_at = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
        merged.append(
            {
                "promptTokenCount": input_tokens,
                "candidatesTokenCount": output_tokens,
                "requests": requests,
                "model": model,
                "occurred_at": occurred_at.isoformat(),
                "vendor_event_id": f"gemini-{model}-{day.isoformat()}",
            }
        )
    return merged


def parse_monitoring_time_series(payload: dict | list | None) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []

    rows: dict[tuple[date, str], dict[str, Any]] = defaultdict(
        lambda: {"promptTokenCount": 0, "candidatesTokenCount": 0, "requests": 0, "model": "gemini"}
    )

    for series in payload.get("timeSeries") or []:
        if not isinstance(series, dict):
            continue
        metric = series.get("metric") or {}
        labels = metric.get("labels") or {}
        quota_metric = str(labels.get("quota_metric") or "")
        if GEMINI_SERVICE not in quota_metric:
            continue
        direction = _metric_direction(quota_metric)
        if direction is None:
            continue

        model = str(labels.get("model") or labels.get("resource_name") or "gemini")
        daily_totals = _daily_usage_from_points(series.get("points") or [])
        for day, amount in daily_totals.items():
            if amount <= 0:
                continue
            key = (day, model)
            rows[key]["model"] = model
            if direction == "input":
                rows[key]["promptTokenCount"] += amount
            elif direction == "output":
                rows[key]["candidatesTokenCount"] += amount
            elif direction == "requests":
                rows[key]["requests"] += amount

    return _merge_usage_rows(rows)


async def fetch_gemini_monitoring_usage(
    *,
    project_id: str,
    access_token: str,
    since: datetime,
    until: datetime,
) -> list[dict[str, Any]]:
    query = {
        "filter": (
            f'metric.type="{QUOTA_USAGE_METRIC}" '
            f'AND resource.type="consumer_quota" '
            f'AND resource.labels.service="{GEMINI_SERVICE}"'
        ),
        "interval.startTime": since.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "interval.endTime": until.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "pageSize": 1000,
    }
    url = f"{MONITORING_BASE}/projects/{project_id}/timeSeries?{urlencode(query)}"
    headers = {"Authorization": f"Bearer {access_token}"}

    rows: list[dict[str, Any]] = []
    next_page: str | None = None
    while True:
        page_url = url if next_page is None else f"{MONITORING_BASE}/{next_page.lstrip('/')}"
        result = await get_with_detail(page_url, headers=headers)
        if result.status_code == 403:
            msg = (
                "GCP service account lacks Cloud Monitoring access for this project. "
                "Grant roles/monitoring.viewer on the Gemini GCP project."
            )
            raise RuntimeError(msg)
        if result.status_code >= 400:
            logger.warning(
                "Google monitoring fetch failed | project=%s status=%s body=%s",
                project_id,
                result.status_code,
                (result.text or "")[:300],
            )
            break

        payload = result.json if isinstance(result.json, dict) else {}
        rows.extend(parse_monitoring_time_series(payload))
        next_page = payload.get("nextPageToken") if isinstance(payload, dict) else None
        if not next_page:
            break

    logger.info(
        "Google monitoring fetch | project=%s rows=%s since=%s until=%s",
        project_id,
        len(rows),
        since.isoformat(),
        until.isoformat(),
    )
    return rows

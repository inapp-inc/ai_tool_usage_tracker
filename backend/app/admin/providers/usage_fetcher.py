"""Fetch live usage metrics from configured vendor APIs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.admin.providers.provider_http import (
    ProviderRequestConfig,
    cursor_daily_usage_body,
    execute_provider_request,
)


@dataclass(frozen=True)
class UsageFetchResult:
    success: bool
    message: str
    token_count: int = 0
    cost_total: float = 0.0
    daily_usage: list[dict[str, Any]] | None = None


def _cfg_number(config: dict, key: str, default: float = 0) -> float:
    value = config.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _estimate_cost_from_tool(
    usage_units: int,
    overage_units: int,
    *,
    token_price: Decimal,
    overage_price: Decimal | None,
    pricing_config: dict,
) -> float:
    ui_pricing = pricing_config.get("ui_pricing") or {}
    overage_rate = _cfg_number(
        ui_pricing if isinstance(ui_pricing, dict) else {},
        "overageRate",
        float(overage_price or token_price),
    )
    input_rate = _cfg_number(
        ui_pricing if isinstance(ui_pricing, dict) else {},
        "inputCostPer1K",
        float(token_price),
    )
    # Billable overage at overage rate; included usage at per-1k token rate / 1000.
    included_units = max(usage_units - overage_units, 0)
    overage_cost = overage_units * (overage_rate / 1000)
    included_cost = included_units * (input_rate / 1000)
    return round(overage_cost + included_cost, 2)


def _cursor_row_units(row: dict[str, Any]) -> tuple[int, int]:
    included = int(row.get("subscriptionIncludedReqs") or 0)
    usage_based = int(row.get("usageBasedReqs") or 0)
    api_key_reqs = int(row.get("apiKeyReqs") or 0)
    composer = int(row.get("composerRequests") or 0)
    chat = int(row.get("chatRequests") or 0)
    agent = int(row.get("agentRequests") or 0)
    total = included + usage_based + api_key_reqs + composer + chat + agent
    return total, usage_based


async def _fetch_cursor_usage(
    *,
    api_key: str,
    usage_api_url: str,
    days: int,
    token_price: Decimal,
    overage_price: Decimal | None,
    pricing_config: dict,
) -> UsageFetchResult:
    url = usage_api_url.strip() or "https://api.cursor.com/teams/daily-usage-data"
    config = ProviderRequestConfig(
        url=url,
        method="POST",
        auth_mode="basic",
        json_body=cursor_daily_usage_body(days=days),
    )

    try:
        response = await execute_provider_request(
            api_key=api_key,
            config=config,
            usage_api_url=url,
        )
    except Exception as exc:
        return UsageFetchResult(
            success=False,
            message=f"Failed to fetch Cursor usage: {exc}",
        )

    if response.status_code >= 400:
        return UsageFetchResult(
            success=False,
            message=f"Cursor usage API returned HTTP {response.status_code}.",
        )

    payload = response.json()
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return UsageFetchResult(
            success=False,
            message="Cursor usage API returned an unexpected response.",
        )

    daily_map: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"tokens": 0, "cost": 0.0, "overage_units": 0}
    )
    total_units = 0
    total_overage = 0

    for row in rows:
        if not isinstance(row, dict):
            continue
        day = str(row.get("day") or row.get("date") or "")[:10]
        if not day:
            continue
        units, overage = _cursor_row_units(row)
        total_units += units
        total_overage += overage
        daily_map[day]["tokens"] = int(daily_map[day]["tokens"]) + units
        daily_map[day]["overage_units"] = int(daily_map[day]["overage_units"]) + overage

    daily_usage: list[dict[str, Any]] = []
    total_cost = 0.0
    for day in sorted(daily_map.keys()):
        day_units = int(daily_map[day]["tokens"])
        day_overage = int(daily_map[day]["overage_units"])
        day_cost = _estimate_cost_from_tool(
            day_units,
            day_overage,
            token_price=token_price,
            overage_price=overage_price,
            pricing_config=pricing_config,
        )
        total_cost += day_cost
        daily_usage.append(
            {"date": day, "tokens": day_units, "cost": round(day_cost, 2)}
        )

    if not rows:
        return UsageFetchResult(
            success=True,
            message="Connection valid. No usage activity in the selected period yet.",
            token_count=0,
            cost_total=0.0,
            daily_usage=[],
        )

    return UsageFetchResult(
        success=True,
        message=(
            f"Synced live Cursor usage: {total_units:,} requests across "
            f"{len(daily_usage)} day(s), ~${total_cost:,.2f} estimated."
        ),
        token_count=total_units,
        cost_total=round(total_cost, 2),
        daily_usage=daily_usage,
    )


async def _fetch_generic_usage(
    *,
    api_key: str,
    usage_api_url: str,
) -> UsageFetchResult:
    """Best-effort GET on configured usage URL; extracts numeric totals if present."""
    config = ProviderRequestConfig(url=usage_api_url, method="GET", auth_mode="bearer")
    try:
        response = await execute_provider_request(
            api_key=api_key,
            config=config,
            usage_api_url=usage_api_url,
        )
    except Exception as exc:
        return UsageFetchResult(
            success=False,
            message=f"Failed to fetch provider usage: {exc}",
        )

    if response.status_code >= 400:
        return UsageFetchResult(
            success=False,
            message=f"Usage API returned HTTP {response.status_code}.",
        )

    try:
        payload = response.json()
    except ValueError:
        return UsageFetchResult(
            success=True,
            message="Connection valid. Usage endpoint did not return JSON metrics.",
            token_count=0,
            cost_total=0.0,
            daily_usage=[],
        )

    tokens = 0
    cost = 0.0
    if isinstance(payload, dict):
        for key in ("total_tokens", "totalTokens", "tokens", "usage"):
            if key in payload:
                tokens = int(payload[key])
                break
        for key in ("total_cost", "totalCost", "cost", "amount"):
            if key in payload:
                cost = float(payload[key])
                break

    today = datetime.now(tz=UTC).date().isoformat()
    daily_usage = (
        [{"date": today, "tokens": tokens, "cost": round(cost, 2)}]
        if tokens or cost
        else []
    )

    if tokens or cost:
        return UsageFetchResult(
            success=True,
            message=f"Synced live usage: {tokens:,} tokens, ${cost:,.2f}.",
            token_count=tokens,
            cost_total=cost,
            daily_usage=daily_usage,
        )

    return UsageFetchResult(
        success=True,
        message="Connection valid. No usage metrics returned for this provider yet.",
        token_count=0,
        cost_total=0.0,
        daily_usage=[],
    )


async def fetch_provider_usage(
    *,
    provider_slug: str,
    api_key: str,
    usage_api_url: str,
    collection_schedule: str,
    token_price: Decimal,
    overage_price: Decimal | None,
    pricing_config: dict,
) -> UsageFetchResult:
    days = 7 if collection_schedule == "hourly" else 30

    if provider_slug == "cursor":
        return await _fetch_cursor_usage(
            api_key=api_key,
            usage_api_url=usage_api_url,
            days=days,
            token_price=token_price,
            overage_price=overage_price,
            pricing_config=pricing_config,
        )

    if usage_api_url.strip().startswith(("http://", "https://")):
        return await _fetch_generic_usage(
            api_key=api_key,
            usage_api_url=usage_api_url,
        )

    return UsageFetchResult(
        success=True,
        message="Connection valid. Live usage polling is not configured for this provider.",
        token_count=0,
        cost_total=0.0,
        daily_usage=[],
    )

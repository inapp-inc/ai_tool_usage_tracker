"""Parse provider usage payloads into canonical UsageRecord rows."""

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.base import UsageRecord


def _epoch_ms_to_datetime(value: object) -> datetime:
    if isinstance(value, str) and value.isdigit():
        millis = int(value)
    elif isinstance(value, (int, float)):
        millis = int(value)
    else:
        return datetime.now(UTC)
    return datetime.fromtimestamp(millis / 1000, tz=UTC)


def parse_cursor_usage_page(payload: object) -> tuple[list[UsageRecord], bool]:
    if not isinstance(payload, dict):
        return [], False

    records: list[UsageRecord] = []
    for index, event in enumerate(payload.get("usageEvents", [])):
        if not isinstance(event, dict):
            continue

        token_usage = event.get("tokenUsage") if isinstance(event.get("tokenUsage"), dict) else {}
        input_tokens = int(token_usage.get("inputTokens", 0) or 0)
        output_tokens = int(token_usage.get("outputTokens", 0) or 0)
        cache_write = int(token_usage.get("cacheWriteTokens", 0) or 0)
        cache_read = int(token_usage.get("cacheReadTokens", 0) or 0)
        total_tokens = input_tokens + output_tokens + cache_write + cache_read

        charged_cents = event.get("chargedCents")
        if charged_cents is None and token_usage:
            charged_cents = token_usage.get("totalCents")
        try:
            estimated_cost = Decimal(str(charged_cents or 0)) / Decimal("100")
        except Exception:  # noqa: BLE001
            estimated_cost = Decimal("0")

        timestamp = event.get("timestamp")
        user_email = event.get("userEmail") or event.get("email") or ""
        model = event.get("model") or "cursor-default"
        vendor_event_id = f"cursor-{timestamp}-{user_email}-{model}-{index}"

        records.append(
            UsageRecord(
                vendor_event_id=vendor_event_id,
                model=str(model),
                occurred_at=_epoch_ms_to_datetime(timestamp),
                input_tokens=input_tokens + cache_write + cache_read,
                output_tokens=output_tokens,
                estimated_cost=estimated_cost,
            )
        )

    pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
    has_next = bool(pagination.get("hasNextPage"))
    return records, has_next

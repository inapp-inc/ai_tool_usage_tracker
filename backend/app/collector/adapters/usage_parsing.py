"""Parse provider usage payloads into canonical UsageRecord rows."""

from datetime import UTC, datetime
from decimal import Decimal
import hashlib

from app.collector.adapters.base import UsageRecord
from app.integration.numbers import parse_compact_int


def cursor_vendor_event_id(
    *,
    timestamp: object,
    user_email: object,
    model: object,
) -> str:
    """Stable id from Cursor event timestamp + user + model (no page index)."""
    ts = str(timestamp or "")
    email = str(user_email or "").strip().lower()
    model_str = str(model or "cursor-default")
    raw = f"{ts}|{email}|{model_str}"
    if len(raw) <= 200:
        return f"cursor-{ts}-{email}-{model_str}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"cursor-{ts}-{digest}"


def _epoch_ms_to_datetime(value: object) -> datetime:
    if isinstance(value, str) and value.isdigit():
        millis = int(value)
    elif isinstance(value, (int, float)):
        millis = int(value)
    else:
        return datetime.now(UTC)
    return datetime.fromtimestamp(millis / 1000, tz=UTC)


def _int_token(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _cursor_kind_is_included(kind: object) -> bool:
    """True when Cursor kind indicates usage included in plan (no billable cost)."""
    return "include" in str(kind or "").lower()


def _cursor_estimated_cost(event: dict, token_usage: dict) -> Decimal:
    """Map Cursor usageEvents cost to USD.

    When ``kind`` contains ``include`` (e.g. "Included in Business"), cost is
    zero — usage is covered by the plan; do not use ``chargedCents`` or
    ``totalCents``. Otherwise use ``chargedCents / 100``.
    """
    if _cursor_kind_is_included(event.get("kind")):
        return Decimal("0")

    try:
        return Decimal(str(event.get("chargedCents") or 0)) / Decimal("100")
    except Exception:  # noqa: BLE001
        return Decimal("0")


def parse_cursor_usage_page(payload: object) -> tuple[list[UsageRecord], bool]:
    if not isinstance(payload, dict):
        return [], False

    records: list[UsageRecord] = []
    for event in payload.get("usageEvents", []):
        if not isinstance(event, dict):
            continue

        token_usage = event.get("tokenUsage") if isinstance(event.get("tokenUsage"), dict) else {}
        input_tokens = _int_token(token_usage.get("inputTokens"))
        output_tokens = _int_token(token_usage.get("outputTokens"))
        cache_write_tokens = _int_token(token_usage.get("cacheWriteTokens"))
        cache_read_tokens = _int_token(token_usage.get("cacheReadTokens"))

        estimated_cost = _cursor_estimated_cost(event, token_usage)

        timestamp = event.get("timestamp")
        user_email = event.get("userEmail") or event.get("email") or ""
        model = event.get("model") or "cursor-default"
        vendor_event_id = cursor_vendor_event_id(
            timestamp=timestamp,
            user_email=user_email,
            model=model,
        )

        records.append(
            UsageRecord(
                vendor_event_id=vendor_event_id,
                model=str(model),
                occurred_at=_epoch_ms_to_datetime(timestamp),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_write_tokens=cache_write_tokens,
                cache_read_tokens=cache_read_tokens,
                estimated_cost=estimated_cost,
                user_email=str(user_email).strip() or None,
            )
        )

    pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
    has_next = bool(pagination.get("hasNextPage"))
    return records, has_next


def _int_field(row: dict, key: str) -> int:
    return parse_compact_int(row.get(key), default=0)


def parse_cursor_daily_usage_page(payload: object) -> tuple[list[UsageRecord], bool]:
    if not isinstance(payload, dict):
        return [], False

    records: list[UsageRecord] = []
    for index, row in enumerate(payload.get("data", [])):
        if not isinstance(row, dict):
            continue

        request_total = sum(
            _int_field(row, key)
            for key in (
                "chatRequests",
                "composerRequests",
                "agentRequests",
                "cmdkUsages",
                "bugbotUsages",
                "usageBasedReqs",
                "subscriptionIncludedReqs",
                "apiKeyReqs",
            )
        )
        line_total = _int_field(row, "totalLinesAdded") + _int_field(row, "totalLinesDeleted")
        input_tokens = request_total or line_total
        if input_tokens <= 0 and not row.get("isActive", True):
            continue

        day = row.get("day")
        date_ms = row.get("date")
        user_id = row.get("userId", index)
        email = row.get("email") or ""
        model = row.get("mostUsedModel") or "cursor-daily"
        vendor_event_id = f"cursor-daily-{day}-{user_id}-{email}-{index}"

        if isinstance(day, str) and day.strip():
            try:
                occurred_at = datetime.fromisoformat(day.strip()).replace(tzinfo=UTC)
            except ValueError:
                occurred_at = _epoch_ms_to_datetime(date_ms)
        else:
            occurred_at = _epoch_ms_to_datetime(date_ms)

        records.append(
            UsageRecord(
                vendor_event_id=vendor_event_id,
                model=str(model),
                occurred_at=occurred_at,
                input_tokens=max(input_tokens, 0),
                output_tokens=0,
                estimated_cost=Decimal("0"),
                user_email=str(email).strip() or None,
            )
        )

    pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
    has_next = bool(pagination.get("hasNextPage"))
    return records, has_next

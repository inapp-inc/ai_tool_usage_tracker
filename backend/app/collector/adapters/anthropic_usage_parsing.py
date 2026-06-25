"""Parse Anthropic Admin API usage and cost report payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.base import UsageRecord
from app.normalization.converters import token_to_usage_record
from app.normalization.token import map_anthropic_usage


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _rfc3339_to_datetime(value: object, fallback: datetime) -> datetime:
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            pass
    return fallback


def _result_rows(bucket: dict) -> list[dict]:
    results = bucket.get("results")
    if isinstance(results, list) and results:
        return [row for row in results if isinstance(row, dict)]
    return []


def _row_has_activity(row: dict) -> bool:
    cache_creation = row.get("cache_creation") if isinstance(row.get("cache_creation"), dict) else {}
    input_tokens = (
        _int(row.get("uncached_input_tokens"))
        + _int(row.get("cache_read_input_tokens"))
        + _int(cache_creation.get("ephemeral_1h_input_tokens"))
        + _int(cache_creation.get("ephemeral_5m_input_tokens"))
        + _int(row.get("input_tokens"))
    )
    output_tokens = _int(row.get("output_tokens"))
    return input_tokens > 0 or output_tokens > 0


def _admin_row_to_mapping(
    row: dict,
    *,
    bucket_start: datetime,
    account_email_map: dict[str, str] | None = None,
) -> dict:
    cache_creation = row.get("cache_creation") if isinstance(row.get("cache_creation"), dict) else {}
    cache_write = _int(cache_creation.get("ephemeral_1h_input_tokens")) + _int(
        cache_creation.get("ephemeral_5m_input_tokens")
    )
    cache_read = _int(row.get("cache_read_input_tokens"))
    uncached = _int(row.get("uncached_input_tokens"))
    output_tokens = _int(row.get("output_tokens"))
    account_id = str(row.get("account_id") or "").strip()
    api_key_id = str(row.get("api_key_id") or "").strip()
    mapped_email = (account_email_map or {}).get(account_id) if account_id else None
    user_ref = mapped_email or account_id or api_key_id or "unknown"
    model = str(row.get("model") or "claude")
    day_key = bucket_start.astimezone(UTC).date().isoformat()

    return {
        "starting_at": bucket_start.isoformat(),
        "user_email": user_ref,
        "account_id": account_id or None,
        "model": model,
        "uncached_input_tokens": uncached,
        "cache_read_input_tokens": cache_read,
        "cache_creation": cache_creation,
        "input_tokens": uncached,
        "output_tokens": output_tokens,
        "vendor_event_id": f"anthropic-{model}-{day_key}-{user_ref}",
    }


def parse_anthropic_usage_payload(
    payload: dict,
    *,
    since: datetime,
    account_email_map: dict[str, str] | None = None,
) -> list[UsageRecord]:
    records: list[UsageRecord] = []
    seen: set[str] = set()
    for bucket in payload.get("data", []):
        if not isinstance(bucket, dict):
            continue
        bucket_start = _rfc3339_to_datetime(bucket.get("starting_at"), since)
        for row in _result_rows(bucket):
            if not _row_has_activity(row):
                continue
            merged = _admin_row_to_mapping(
                row,
                bucket_start=bucket_start,
                account_email_map=account_email_map,
            )
            vendor_event_id = str(merged.get("vendor_event_id") or "")
            if vendor_event_id in seen:
                continue
            seen.add(vendor_event_id)
            normalized = map_anthropic_usage(merged, fallback_at=bucket_start)
            if normalized is not None:
                records.append(token_to_usage_record(normalized))
    return records


def _parse_cost_amount(row: dict) -> Decimal:
    try:
        raw = Decimal(str(row.get("amount") or "0"))
    except Exception:  # noqa: BLE001
        return Decimal("0")
    if raw <= 0:
        return Decimal("0")
    return raw / Decimal("100")


def parse_anthropic_costs_by_day(
    buckets: list[dict],
    *,
    since: datetime,
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for bucket in buckets:
        if not isinstance(bucket, dict):
            continue
        bucket_start = _rfc3339_to_datetime(bucket.get("starting_at"), since)
        day_key = bucket_start.astimezone(UTC).strftime("%Y-%m-%d")
        day_total = Decimal("0")
        for row in _result_rows(bucket):
            day_total += _parse_cost_amount(row)
        if day_total <= 0:
            continue
        totals[day_key] = totals.get(day_key, Decimal("0")) + day_total
    return totals


def apply_anthropic_costs_to_records(
    records: list[UsageRecord],
    buckets: list[dict],
    *,
    since: datetime,
) -> None:
    """Allocate daily cost_report amounts across usage rows for the same UTC day."""
    costs_by_day = parse_anthropic_costs_by_day(buckets, since=since)
    if not costs_by_day or not records:
        return

    records_by_day: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        if record.total_tokens <= 0:
            continue
        day_key = record.occurred_at.astimezone(UTC).strftime("%Y-%m-%d")
        records_by_day.setdefault(day_key, []).append(index)

    for day_key, day_cost in costs_by_day.items():
        indexes = records_by_day.get(day_key, [])
        if not indexes:
            continue
        remaining = day_cost
        total_tokens = sum(records[index].total_tokens for index in indexes)
        for position, index in enumerate(indexes):
            record = records[index]
            if record.estimated_cost > 0:
                remaining -= record.estimated_cost
                continue
            if total_tokens <= 0:
                share = day_cost / Decimal(len(indexes))
            elif position == len(indexes) - 1:
                share = remaining
            else:
                share = (day_cost * Decimal(record.total_tokens) / Decimal(total_tokens)).quantize(
                    Decimal("0.000001")
                )
                remaining -= share
            records[index] = UsageRecord(
                vendor_event_id=record.vendor_event_id,
                model=record.model,
                occurred_at=record.occurred_at,
                input_tokens=record.input_tokens,
                output_tokens=record.output_tokens,
                cache_write_tokens=record.cache_write_tokens,
                cache_read_tokens=record.cache_read_tokens,
                estimated_cost=share,
                user_email=record.user_email,
                user_name=record.user_name,
                requests=record.requests,
                included_in_plan=record.included_in_plan,
                cursor_kind=record.cursor_kind,
                reference_cost=record.reference_cost,
            )

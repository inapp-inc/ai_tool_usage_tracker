"""Parse OpenAI organization usage API payloads via normalized mapping."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.base import UsageRecord
from app.normalization.converters import token_to_usage_record
from app.normalization.token import map_openai_usage


def _epoch_to_datetime(value: object, fallback: datetime) -> datetime:
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(int(value), tz=UTC)
        if isinstance(value, str) and value.isdigit():
            return datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError, OSError):
        pass
    return fallback


def _result_rows(bucket: dict) -> list[dict]:
    results = bucket.get("results")
    if isinstance(results, list) and results:
        return [row for row in results if isinstance(row, dict)]
    if bucket.get("input_tokens") is not None or bucket.get("output_tokens") is not None:
        return [bucket]
    return []


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _usage_row_has_activity(row: dict) -> bool:
    input_tokens = _int(row.get("input_tokens"))
    output_tokens = _int(row.get("output_tokens"))
    requests = _int(row.get("num_model_requests") or row.get("n_requests"))
    cache_read = _int(row.get("input_cached_tokens") or row.get("cached_tokens"))
    return input_tokens > 0 or output_tokens > 0 or requests > 0 or cache_read > 0


def _parse_cost_amount(row: dict) -> Decimal:
    amount = row.get("amount") or row.get("cost_usd") or row.get("cost")
    if isinstance(amount, dict):
        value = amount.get("value")
        if value is None:
            return Decimal("0")
        raw = Decimal(str(value))
        if row.get("object") == "organization.costs.result":
            return raw
        return raw / Decimal("100") if raw >= Decimal("1") else raw
    try:
        return Decimal(str(amount or 0))
    except Exception:  # noqa: BLE001
        return Decimal("0")


def parse_openai_completions_payload(
    payload: dict,
    *,
    since: datetime,
    user_id_map: dict[str, str] | None = None,
    usage_kind: str = "completions",
    require_model: bool = False,
) -> list[UsageRecord]:
    """Map /v1/organization/usage/* response to UsageRecord rows."""
    records: list[UsageRecord] = []
    for bucket_index, bucket in enumerate(payload.get("data", [])):
        if not isinstance(bucket, dict):
            continue
        bucket_start = _epoch_to_datetime(bucket.get("start_time"), since)
        for result_index, row in enumerate(_result_rows(bucket)):
            if not _usage_row_has_activity(row):
                continue
            if require_model:
                model = row.get("model")
                if not isinstance(model, str) or not model.strip() or model.strip().lower() == "unknown":
                    continue
            merged = {**row}
            if "start_time" not in merged and bucket.get("start_time") is not None:
                merged["start_time"] = bucket.get("start_time")
            user_id = merged.get("user_id")
            mapped_email = None
            if isinstance(user_id, str) and user_id_map:
                mapped_email = user_id_map.get(user_id)
            normalized = map_openai_usage(
                merged,
                page=bucket_index,
                fallback_at=bucket_start,
                mapped_user_email=mapped_email,
                usage_kind=usage_kind,
            )
            if normalized is not None:
                records.append(token_to_usage_record(normalized))
    return records


def parse_openai_costs_payload(payload: dict) -> dict[str, Decimal]:
    """Map /v1/organization/costs buckets to vendor_event_id → USD."""
    costs: dict[str, Decimal] = {}
    for bucket in payload.get("data", []):
        if not isinstance(bucket, dict):
            continue
        bucket_start = _epoch_to_datetime(bucket.get("start_time"), datetime.now(UTC))
        for row in _result_rows(bucket):
            amount = _parse_cost_amount(row)
            if amount <= 0:
                continue
            key = str(row.get("id") or "")
            if not key:
                line_item = str(row.get("line_item") or "organization")
                project_id = str(row.get("project_id") or "org")
                key = f"openai-cost-{line_item}-{project_id}-{int(bucket_start.timestamp())}"
            costs[key] = amount
    return costs


def parse_openai_costs_as_usage_records(
    payload: dict,
    *,
    since: datetime,
) -> list[UsageRecord]:
    """Build cost-only usage rows when token usage buckets are empty."""
    records: list[UsageRecord] = []
    for bucket in payload.get("data", []):
        if not isinstance(bucket, dict):
            continue
        bucket_start = _epoch_to_datetime(bucket.get("start_time"), since)
        for row in _result_rows(bucket):
            cost = _parse_cost_amount(row)
            if cost <= 0:
                continue
            line_item = str(row.get("line_item") or "organization")
            project_id = str(row.get("project_id") or "org")
            row_id = str(row.get("id") or "")
            vendor_event_id = row_id or f"openai-cost-{line_item}-{project_id}-{int(bucket_start.timestamp())}"
            records.append(
                UsageRecord(
                    vendor_event_id=vendor_event_id,
                    model=line_item,
                    occurred_at=bucket_start,
                    input_tokens=0,
                    output_tokens=0,
                    estimated_cost=cost,
                    requests=0,
                )
            )
    return records


def parse_openai_costs_by_day(
    buckets: list[dict],
    *,
    since: datetime,
) -> dict[str, Decimal]:
    """Sum organization/costs bucket amounts by UTC day (YYYY-MM-DD)."""
    totals: dict[str, Decimal] = {}
    for bucket in buckets:
        if not isinstance(bucket, dict):
            continue
        bucket_start = _epoch_to_datetime(bucket.get("start_time"), since)
        day_key = bucket_start.astimezone(UTC).strftime("%Y-%m-%d")
        day_total = Decimal("0")
        for row in _result_rows(bucket):
            day_total += _parse_cost_amount(row)
        if day_total <= 0:
            continue
        totals[day_key] = totals.get(day_key, Decimal("0")) + day_total
    return totals


def apply_openai_costs_to_records(
    records: list[UsageRecord],
    buckets: list[dict],
    *,
    since: datetime,
) -> None:
    """Allocate daily organization costs across usage rows for the same UTC day."""
    costs_by_day = parse_openai_costs_by_day(buckets, since=since)
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


def merge_openai_costs(records: list[UsageRecord], costs: dict[str, Decimal]) -> None:
    """Apply cost API amounts to parsed usage records by vendor_event_id."""
    if not costs:
        return
    for index, record in enumerate(records):
        cost = costs.get(record.vendor_event_id or "")
        if cost is None:
            continue
        records[index] = UsageRecord(
            vendor_event_id=record.vendor_event_id,
            model=record.model,
            occurred_at=record.occurred_at,
            input_tokens=record.input_tokens,
            output_tokens=record.output_tokens,
            cache_write_tokens=record.cache_write_tokens,
            cache_read_tokens=record.cache_read_tokens,
            estimated_cost=cost,
            user_email=record.user_email,
            user_name=record.user_name,
            requests=record.requests,
        )

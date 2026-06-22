"""Token-based vendor API → NormalizedTokenEvent (Cursor excluded)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.normalization.cost_engine import apply_token_cost_from_api, apply_token_cost_from_pricing
from app.normalization.schemas import NormalizedTokenEvent


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:  # noqa: BLE001
        return Decimal("0")


def _ms_to_datetime(ms: int | None, fallback: datetime) -> datetime:
    if ms is None:
        return fallback
    try:
        return datetime.fromtimestamp(ms / 1000, tz=UTC)
    except (OSError, ValueError):
        return fallback


def _epoch_seconds_to_datetime(seconds: int | None, fallback: datetime) -> datetime:
    if seconds is None:
        return fallback
    try:
        return datetime.fromtimestamp(seconds, tz=UTC)
    except (OSError, ValueError):
        return fallback


def _sum_tokens(
    input_t: int,
    output_t: int,
    cache_write: int = 0,
    cache_read: int = 0,
) -> int:
    return input_t + output_t + cache_write + cache_read


def map_openai_usage(
    row: dict[str, Any],
    *,
    cost_row: dict[str, Any] | None = None,
    page: int | None = None,
    fallback_at: datetime,
    mapped_user_email: str | None = None,
    usage_kind: str = "completions",
) -> NormalizedTokenEvent | None:
    start_time = row.get("start_time") or row.get("startTime")
    if isinstance(start_time, str) and start_time.isdigit():
        start_time = int(start_time)
    occurred_at = _epoch_seconds_to_datetime(
        int(start_time) if isinstance(start_time, (int, float)) else None,
        fallback_at,
    )
    raw_ms = int(start_time) * 1000 if isinstance(start_time, (int, float)) else None

    input_tokens = _int(row.get("input_tokens"))
    output_tokens = _int(row.get("output_tokens"))
    cache_read = _int(row.get("input_cached_tokens") or row.get("cached_tokens"))
    requests = _int(row.get("num_model_requests") or row.get("n_requests") or 1)
    user_id = str(row.get("user_id") or row.get("user_email") or mapped_user_email or "")
    model = str(row.get("model") or "unknown")
    start_key = int(start_time) if isinstance(start_time, (int, float)) else int(fallback_at.timestamp())
    vendor_event_id = str(
        row.get("id") or f"openai-{usage_kind}-{user_id}-{model}-{start_key}"
    )

    api_cost = Decimal("0")
    api_cents: int | None = None
    if cost_row:
        amount = cost_row.get("amount")
        if isinstance(amount, dict):
            api_cost = _decimal(amount.get("value"))
            api_cents = int(api_cost * 100)
        else:
            api_cost = _decimal(cost_row.get("cost_usd") or cost_row.get("cost"))

    event = NormalizedTokenEvent(
        source="OpenAI",
        page=page,
        raw_timestamp_ms=raw_ms,
        occurred_at=occurred_at,
        user_email=mapped_user_email or row.get("user_email") or row.get("email"),
        model=model,
        kind="completion",
        api_input_tokens=input_tokens,
        api_output_tokens=output_tokens,
        api_cache_read_tokens=cache_read or None,
        parsed_input_tokens=input_tokens,
        parsed_output_tokens=output_tokens,
        parsed_cache_read_tokens=cache_read,
        parsed_total_tokens=_sum_tokens(input_tokens, output_tokens, cache_read=cache_read),
        api_charged_cents=api_cents,
        charged_cents_usd=api_cost if api_cost else None,
        estimated_cost_usd=api_cost,
        requests=requests,
        vendor_event_id=vendor_event_id,
        raw_payload=row,
    )
    return apply_token_cost_from_api(event)


def map_anthropic_usage(row: dict[str, Any], *, fallback_at: datetime) -> NormalizedTokenEvent | None:
    ts = row.get("timestamp")
    raw_ms = _int(ts) if ts is not None else None
    occurred_at = _ms_to_datetime(raw_ms, fallback_at)
    user_email = row.get("userEmail") or row.get("user_email")
    if not user_email:
        return None

    input_tokens = _int(row.get("input_tokens"))
    output_tokens = _int(row.get("output_tokens"))
    model = str(row.get("model") or "claude")

    event = NormalizedTokenEvent(
        source="Claude",
        raw_timestamp_ms=raw_ms,
        occurred_at=occurred_at,
        user_email=str(user_email),
        model=model,
        kind="message",
        api_input_tokens=input_tokens,
        api_output_tokens=output_tokens,
        parsed_input_tokens=input_tokens,
        parsed_output_tokens=output_tokens,
        parsed_total_tokens=input_tokens + output_tokens,
        vendor_event_id=f"anthropic-{raw_ms}-{user_email}",
        raw_payload=row,
    )
    return apply_token_cost_from_pricing(
        event,
        input_price_per_million=Decimal("3"),
        output_price_per_million=Decimal("15"),
    )


def map_gemini_usage(row: dict[str, Any], *, fallback_at: datetime) -> NormalizedTokenEvent | None:
    input_tokens = _int(row.get("promptTokenCount") or row.get("prompt_token_count"))
    output_tokens = _int(row.get("candidatesTokenCount") or row.get("candidates_token_count"))
    requests = _int(row.get("requests") or row.get("request_count"))
    if input_tokens == 0 and output_tokens == 0 and requests == 0:
        return None
    model = str(row.get("model") or "gemini")
    occurred_at = fallback_at
    raw_occurred = row.get("occurred_at") or row.get("occurredAt")
    if isinstance(raw_occurred, datetime):
        occurred_at = raw_occurred.astimezone(UTC)
    elif isinstance(raw_occurred, str) and raw_occurred.strip():
        try:
            occurred_at = datetime.fromisoformat(raw_occurred.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            occurred_at = fallback_at
    vendor_event_id = str(row.get("vendor_event_id") or f"gemini-{model}-{occurred_at.date()}")
    event = NormalizedTokenEvent(
        source="Gemini",
        occurred_at=occurred_at,
        model=model,
        kind="completion",
        api_input_tokens=input_tokens,
        api_output_tokens=output_tokens,
        parsed_input_tokens=input_tokens,
        parsed_output_tokens=output_tokens,
        parsed_total_tokens=input_tokens + output_tokens,
        requests=requests,
        vendor_event_id=vendor_event_id,
        raw_payload=row,
    )
    return apply_token_cost_from_pricing(
        event,
        input_price_per_million=Decimal("1.25"),
        output_price_per_million=Decimal("5"),
    )


def map_bedrock_usage(row: dict[str, Any], *, fallback_at: datetime) -> NormalizedTokenEvent | None:
    input_tokens = _int(row.get("inputTokenCount") or row.get("input_tokens"))
    output_tokens = _int(row.get("outputTokenCount") or row.get("output_tokens"))
    if input_tokens == 0 and output_tokens == 0:
        return None
    model = str(row.get("modelId") or row.get("model") or "bedrock")
    event = NormalizedTokenEvent(
        source="Bedrock",
        occurred_at=fallback_at,
        model=model,
        kind="invocation",
        api_input_tokens=input_tokens,
        api_output_tokens=output_tokens,
        parsed_input_tokens=input_tokens,
        parsed_output_tokens=output_tokens,
        parsed_total_tokens=input_tokens + output_tokens,
        vendor_event_id=f"bedrock-{model}-{fallback_at.date()}",
        raw_payload=row,
    )
    return apply_token_cost_from_pricing(
        event,
        input_price_per_million=Decimal("3"),
        output_price_per_million=Decimal("15"),
    )


def map_azure_openai_usage(
    row: dict[str, Any],
    *,
    fallback_at: datetime,
    deployment: str | None = None,
) -> NormalizedTokenEvent | None:
    """Azure usage rows mirror OpenAI token fields when available."""
    input_tokens = _int(row.get("input_tokens") or row.get("prompt_tokens"))
    output_tokens = _int(row.get("output_tokens") or row.get("completion_tokens"))
    if input_tokens == 0 and output_tokens == 0:
        return None
    model = str(row.get("model") or deployment or "azure-openai")
    start = row.get("start_time") or row.get("timestamp")
    occurred_at = fallback_at
    if isinstance(start, (int, float)):
        occurred_at = _epoch_seconds_to_datetime(int(start), fallback_at)

    event = NormalizedTokenEvent(
        source="Azure OpenAI",
        occurred_at=occurred_at,
        model=model,
        kind="completion",
        api_input_tokens=input_tokens,
        api_output_tokens=output_tokens,
        parsed_input_tokens=input_tokens,
        parsed_output_tokens=output_tokens,
        parsed_total_tokens=input_tokens + output_tokens,
        vendor_event_id=f"azure-openai-{model}-{occurred_at.date()}",
        raw_payload=row,
    )
    return apply_token_cost_from_pricing(
        event,
        input_price_per_million=Decimal("3"),
        output_price_per_million=Decimal("12"),
    )


def map_generic_token_usage(
    row: dict[str, Any],
    *,
    source: str,
    fallback_at: datetime,
) -> NormalizedTokenEvent | None:
    """Fallback for OpenRouter, DeepSeek, Groq, Mistral, Cohere-shaped payloads."""
    input_tokens = _int(
        row.get("input_tokens")
        or row.get("prompt_tokens")
        or row.get("inputTokenCount")
    )
    output_tokens = _int(
        row.get("output_tokens")
        or row.get("completion_tokens")
        or row.get("outputTokenCount")
    )
    if input_tokens == 0 and output_tokens == 0:
        return None
    model = str(row.get("model") or row.get("modelId") or source.lower())
    event = NormalizedTokenEvent(
        source=source,
        occurred_at=fallback_at,
        user_email=row.get("user_email") or row.get("userEmail"),
        model=model,
        kind=str(row.get("kind") or "completion"),
        api_input_tokens=input_tokens,
        api_output_tokens=output_tokens,
        parsed_input_tokens=input_tokens,
        parsed_output_tokens=output_tokens,
        parsed_total_tokens=input_tokens + output_tokens,
        vendor_event_id=str(row.get("vendor_event_id") or f"{source.lower()}-{model}-{fallback_at.date()}"),
        raw_payload=row,
    )
    cost = _decimal(row.get("cost_usd") or row.get("cost"))
    if cost > 0:
        return apply_token_cost_from_api(
            NormalizedTokenEvent(**{**event.__dict__, "estimated_cost_usd": cost, "charged_cents_usd": cost})
        )
    return apply_token_cost_from_pricing(
        event,
        input_price_per_million=Decimal("2"),
        output_price_per_million=Decimal("8"),
    )

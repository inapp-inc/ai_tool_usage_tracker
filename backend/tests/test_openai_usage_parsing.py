"""Tests for OpenAI usage payload parsing."""

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.openai_usage_parsing import (
    parse_openai_completions_payload,
    parse_openai_costs_as_usage_records,
    parse_openai_costs_payload,
)


def test_parse_openai_completions_payload_maps_tokens_and_requests() -> None:
    since = datetime(2026, 6, 1, tzinfo=UTC)
    payload = {
        "data": [
            {
                "start_time": int(since.timestamp()),
                "results": [
                    {
                        "id": "usage-1",
                        "model": "gpt-4o",
                        "input_tokens": 1000,
                        "output_tokens": 500,
                        "num_model_requests": 3,
                        "user_email": "dev@example.com",
                    }
                ],
            }
        ]
    }

    records = parse_openai_completions_payload(payload, since=since)
    assert len(records) == 1
    assert records[0].vendor_event_id == "usage-1"
    assert records[0].input_tokens == 1000
    assert records[0].output_tokens == 500
    assert records[0].requests == 3
    assert records[0].user_email == "dev@example.com"


def test_parse_openai_completions_payload_maps_user_id_to_email() -> None:
    since = datetime(2026, 6, 1, tzinfo=UTC)
    payload = {
        "data": [
            {
                "start_time": int(since.timestamp()),
                "results": [
                    {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "model": "gpt-4o",
                        "user_id": "user-abc",
                    }
                ],
            }
        ]
    }

    records = parse_openai_completions_payload(
        payload,
        since=since,
        user_id_map={"user-abc": "dev@example.com"},
    )
    assert len(records) == 1
    assert records[0].user_email == "dev@example.com"


def test_parse_openai_costs_as_usage_records() -> None:
    since = datetime(2026, 6, 1, tzinfo=UTC)
    payload = {
        "data": [
            {
                "start_time": int(since.timestamp()),
                "results": [
                    {
                        "object": "organization.costs.result",
                        "amount": {"value": 2.50, "currency": "usd"},
                    }
                ],
            }
        ]
    }

    records = parse_openai_costs_as_usage_records(payload, since=since)
    assert len(records) == 1
    assert records[0].estimated_cost == Decimal("2.50")
    assert records[0].input_tokens == 0


def test_apply_openai_costs_to_records_allocates_by_day() -> None:
    from app.collector.adapters.base import UsageRecord
    from app.collector.adapters.openai_usage_parsing import apply_openai_costs_to_records

    day = datetime(2026, 6, 1, tzinfo=UTC)
    records = [
        UsageRecord(
            vendor_event_id="u1",
            model="gpt-4o",
            occurred_at=day,
            input_tokens=1000,
            output_tokens=500,
            estimated_cost=Decimal("0"),
        ),
        UsageRecord(
            vendor_event_id="u2",
            model="gpt-4o-mini",
            occurred_at=day,
            input_tokens=500,
            output_tokens=250,
            estimated_cost=Decimal("0"),
        ),
    ]
    buckets = [
        {
            "start_time": int(day.timestamp()),
            "results": [
                {
                    "object": "organization.costs.result",
                    "amount": {"value": 3.0, "currency": "usd"},
                }
            ],
        }
    ]
    apply_openai_costs_to_records(records, buckets, since=day)
    assert records[0].estimated_cost == Decimal("2.000000")
    assert records[1].estimated_cost == Decimal("1.000000")
    assert sum(record.estimated_cost for record in records) == Decimal("3.000000")


def test_parse_openai_completions_payload_skips_empty_results() -> None:
    since = datetime(2026, 5, 23, tzinfo=UTC)
    payload = {
        "data": [
            {
                "object": "bucket",
                "start_time": int(since.timestamp()),
                "end_time": int(since.timestamp()) + 86400,
                "results": [],
            },
            {
                "object": "bucket",
                "start_time": int(since.timestamp()) + 86400,
                "end_time": int(since.timestamp()) + 172800,
                "results": [
                    {
                        "input_tokens": 1000,
                        "output_tokens": 200,
                        "num_model_requests": 5,
                        "model": None,
                    }
                ],
            },
        ]
    }

    records = parse_openai_completions_payload(payload, since=since)
    assert len(records) == 1
    assert records[0].input_tokens == 1000


def test_parse_openai_costs_payload_maps_amounts() -> None:
    payload = {
        "data": [
            {
                "start_time": 1717200000,
                "results": [
                    {
                        "object": "organization.costs.result",
                        "id": "usage-1",
                        "amount": {"value": 1.25, "currency": "usd"},
                    }
                ],
            }
        ]
    }

    costs = parse_openai_costs_payload(payload)
    assert costs["usage-1"] == Decimal("1.25")

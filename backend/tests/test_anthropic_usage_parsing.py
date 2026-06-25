"""Tests for Anthropic Admin API usage parsing."""

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.anthropic_usage_parsing import (
    apply_anthropic_costs_to_records,
    parse_anthropic_usage_payload,
)
from app.collector.adapters.base import UsageRecord


def test_parse_anthropic_usage_payload_maps_admin_rows() -> None:
    payload = {
        "data": [
            {
                "starting_at": "2026-06-01T00:00:00Z",
                "ending_at": "2026-06-02T00:00:00Z",
                "results": [
                    {
                        "account_id": "user_01ABC",
                        "model": "claude-sonnet-4-20250514",
                        "uncached_input_tokens": 1000,
                        "cache_read_input_tokens": 200,
                        "cache_creation": {
                            "ephemeral_5m_input_tokens": 50,
                            "ephemeral_1h_input_tokens": 0,
                        },
                        "output_tokens": 400,
                    }
                ],
            }
        ]
    }
    records = parse_anthropic_usage_payload(
        payload,
        since=datetime(2026, 6, 1, tzinfo=UTC),
        account_email_map={"user_01ABC": "dev@company.com"},
    )
    assert len(records) == 1
    assert records[0].user_email == "dev@company.com"
    assert records[0].input_tokens == 1000
    assert records[0].cache_read_tokens == 200
    assert records[0].cache_write_tokens == 50
    assert records[0].output_tokens == 400
    assert records[0].total_tokens == 1650
    assert records[0].model == "claude-sonnet-4-20250514"


def test_apply_anthropic_costs_to_records() -> None:
    records = [
        UsageRecord(
            vendor_event_id="anthropic-claude-2026-06-01-user",
            model="claude-sonnet",
            occurred_at=datetime(2026, 6, 1, 12, tzinfo=UTC),
            input_tokens=1000,
            output_tokens=500,
            estimated_cost=Decimal("0"),
        )
    ]
    cost_buckets = [
        {
            "starting_at": "2026-06-01T00:00:00Z",
            "results": [{"amount": "123.45", "currency": "USD", "cost_type": "tokens"}],
        }
    ]
    apply_anthropic_costs_to_records(records, cost_buckets, since=datetime(2026, 6, 1, tzinfo=UTC))
    assert records[0].estimated_cost == Decimal("1.2345")

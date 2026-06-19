"""Tests for Cursor usageEvents parsing."""

from decimal import Decimal

from app.collector.adapters.usage_parsing import (
    _cursor_estimated_cost,
    parse_cursor_usage_page,
)


def test_parse_cursor_usage_page_separate_token_fields() -> None:
    payload = {
        "usageEvents": [
            {
                "timestamp": "1750979225854",
                "userEmail": "dev@acme.example",
                "model": "claude-4.5-sonnet",
                "isTokenBasedCall": True,
                "tokenUsage": {
                    "inputTokens": 126,
                    "outputTokens": 450,
                    "cacheWriteTokens": 100,
                    "cacheReadTokens": 50,
                },
                "chargedCents": 21.36,
            }
        ],
        "pagination": {"hasNextPage": False},
    }
    records, has_next = parse_cursor_usage_page(payload)
    assert has_next is False
    assert len(records) == 1
    record = records[0]
    assert record.input_tokens == 126
    assert record.output_tokens == 450
    assert record.cache_write_tokens == 100
    assert record.cache_read_tokens == 50
    assert record.total_tokens == 726
    assert record.estimated_cost == Decimal("0.2136")
    assert record.user_email == "dev@acme.example"
    assert record.model == "claude-4.5-sonnet"


def test_parse_cursor_usage_page_included_in_business_has_zero_cost() -> None:
    payload = {
        "usageEvents": [
            {
                "timestamp": "1781804248151",
                "model": "default",
                "kind": "Included in Business",
                "maxMode": False,
                "requestsCosts": 7.9,
                "isTokenBasedCall": True,
                "tokenUsage": {
                    "inputTokens": 11762,
                    "outputTokens": 6052,
                    "cacheWriteTokens": 0,
                    "cacheReadTokens": 383488,
                    "totalCents": 31.781,
                },
                "userEmail": "rohith.sk@inapp.com",
                "cursorTokenFee": 0,
                "isChargeable": True,
                "serviceAccountId": "null",
                "isHeadless": False,
                "chargedCents": 14.68865,
            }
        ],
        "pagination": {"hasNextPage": False},
    }
    records, _ = parse_cursor_usage_page(payload)
    record = records[0]
    assert record.input_tokens == 11762
    assert record.output_tokens == 6052
    assert record.cache_write_tokens == 0
    assert record.cache_read_tokens == 383488
    assert record.total_tokens == 401302
    assert record.estimated_cost == Decimal("0")
    assert record.user_email == "rohith.sk@inapp.com"


def test_cursor_estimated_cost_included_kind_is_zero() -> None:
    event = {"kind": "Included in Business", "chargedCents": 14.68865}
    token_usage = {"totalCents": 31.781}
    assert _cursor_estimated_cost(event, token_usage) == Decimal("0")


def test_cursor_estimated_cost_non_included_uses_charged_cents_only() -> None:
    event = {"kind": "Usage-based", "chargedCents": 14.68865}
    token_usage = {"totalCents": 31.781}
    assert _cursor_estimated_cost(event, token_usage) == Decimal("0.1468865")

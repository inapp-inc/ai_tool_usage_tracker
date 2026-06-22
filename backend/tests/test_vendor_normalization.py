"""Tests for vendor normalization mappings (Cursor excluded)."""

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.anthropic import AnthropicUsageAdapter
from app.collector.adapters.figma import FigmaUsageAdapter
from app.collector.adapters.google import GoogleUsageAdapter
from app.collector.adapters.openai_usage_parsing import parse_openai_completions_payload
from app.collector.adapters.generic import GenericUsageAdapter
from app.normalization.converters import license_to_usage_record, token_to_usage_record
from app.normalization.license import map_figma_activity, with_license_cost
from app.normalization.productivity import map_copilot_productivity
from app.normalization.token import map_anthropic_usage, map_bedrock_usage, map_gemini_usage, map_openai_usage


def test_openai_normalized_mapping() -> None:
    row = {
        "start_time": 1717200000,
        "input_tokens": 120000,
        "output_tokens": 40000,
        "model": "gpt-4o",
        "user_id": "user123",
    }
    cost_row = {"amount": {"value": 12.50}}
    event = map_openai_usage(row, cost_row=cost_row, fallback_at=datetime(2024, 6, 1, tzinfo=UTC))
    assert event is not None
    assert event.source == "OpenAI"
    assert event.parsed_total_tokens == 160000
    assert event.estimated_cost_usd == Decimal("12.50")
    record = token_to_usage_record(event)
    assert record.input_tokens == 120000


def test_openai_completions_payload_uses_normalization() -> None:
    payload = {
        "data": [
            {
                "start_time": 1717200000,
                "results": [
                    {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "model": "gpt-4o-mini",
                        "user_id": "u1",
                    }
                ],
            }
        ]
    }
    records = parse_openai_completions_payload(payload, since=datetime(2024, 6, 1, tzinfo=UTC))
    assert len(records) == 1
    assert records[0].input_tokens == 10


def test_anthropic_normalized_mapping() -> None:
    row = {
        "timestamp": 1748829102000,
        "userEmail": "user@company.com",
        "model": "claude-sonnet",
        "input_tokens": 15000,
        "output_tokens": 3500,
    }
    event = map_anthropic_usage(row, fallback_at=datetime(2025, 6, 1, tzinfo=UTC))
    assert event is not None
    assert event.parsed_total_tokens == 18500
    records = AnthropicUsageAdapter.parse_usage_rows([row], fallback_at=datetime(2025, 6, 1, tzinfo=UTC))
    assert len(records) == 1


def test_gemini_and_bedrock_mapping() -> None:
    gemini = map_gemini_usage(
        {"promptTokenCount": 12000, "candidatesTokenCount": 3500, "model": "gemini-pro"},
        fallback_at=datetime(2025, 6, 1, tzinfo=UTC),
    )
    assert gemini is not None
    assert gemini.parsed_total_tokens == 15500

    bedrock = map_bedrock_usage(
        {"inputTokenCount": 25000, "outputTokenCount": 8000, "modelId": "anthropic.claude-sonnet"},
        fallback_at=datetime(2025, 6, 1, tzinfo=UTC),
    )
    assert bedrock is not None
    assert bedrock.model == "anthropic.claude-sonnet"


def test_copilot_productivity_mapping() -> None:
    event = map_copilot_productivity(
        {
            "user_login": "john",
            "feature": "chat",
            "editor": "VS Code",
            "language": "TypeScript",
            "active_days": 21,
            "chat_turns": 120,
            "suggestions_count": 2500,
            "acceptances_count": 1500,
            "lines_suggested": 12000,
            "lines_accepted": 8000,
            "day": "2026-06-01",
        }
    )
    assert event is not None
    assert event.user_email == "john"
    assert event.acceptance_rate == Decimal("60")


def test_figma_license_mapping() -> None:
    event = map_figma_activity(
        {
            "user": "john@company.com",
            "team": "Design Team",
            "project": "Banking App",
            "file": "Dashboard.fig",
            "action": "edited",
            "last_active": "2026-06-21",
        },
        license_type="Professional",
    )
    assert event is not None
    event = with_license_cost(event, monthly_package_cost=Decimal("150"), assigned_licenses=10)
    record = license_to_usage_record(event)
    assert record.input_tokens == 0
    assert record.estimated_cost == Decimal("15")


def test_generic_bedrock_parse_rows() -> None:
    rows = GenericUsageAdapter.parse_token_rows(
        "bedrock",
        [{"inputTokenCount": 100, "outputTokenCount": 50, "modelId": "test"}],
        fallback_at=datetime(2025, 6, 1, tzinfo=UTC),
    )
    assert len(rows) == 1
    assert rows[0].total_tokens == 150

"""Tests for Google Gemini Cloud Monitoring usage parsing."""

from datetime import UTC, datetime

from app.collector.adapters.google import GoogleUsageAdapter
from app.collector.adapters.google_monitoring import parse_monitoring_time_series


def test_parse_monitoring_time_series_daily_tokens() -> None:
    payload = {
        "timeSeries": [
            {
                "metric": {
                    "labels": {
                        "quota_metric": (
                            "generativelanguage.googleapis.com/"
                            "generate_content_paid_tier_input_token_count"
                        ),
                        "model": "gemini-2.5-flash",
                    }
                },
                "points": [
                    {
                        "interval": {"endTime": "2026-06-01T12:00:00Z"},
                        "value": {"int64Value": "1000"},
                    },
                    {
                        "interval": {"endTime": "2026-06-01T13:00:00Z"},
                        "value": {"int64Value": "2500"},
                    },
                ],
            },
            {
                "metric": {
                    "labels": {
                        "quota_metric": (
                            "generativelanguage.googleapis.com/"
                            "generate_content_paid_tier_output_token_count"
                        ),
                        "model": "gemini-2.5-flash",
                    }
                },
                "points": [
                    {
                        "interval": {"endTime": "2026-06-01T13:00:00Z"},
                        "value": {"int64Value": "400"},
                    }
                ],
            },
        ]
    }
    rows = parse_monitoring_time_series(payload)
    assert len(rows) == 1
    assert rows[0]["model"] == "gemini-2.5-flash"
    assert rows[0]["promptTokenCount"] == 2500
    assert rows[0]["candidatesTokenCount"] == 400
    assert rows[0]["vendor_event_id"] == "gemini-gemini-2.5-flash-2026-06-01"

    records = GoogleUsageAdapter.parse_usage_rows(
        rows,
        fallback_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    assert len(records) == 1
    assert records[0].total_tokens == 2900
    assert records[0].input_tokens == 2500
    assert records[0].output_tokens == 400

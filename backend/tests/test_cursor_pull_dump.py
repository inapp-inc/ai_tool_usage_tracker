"""Tests for Cursor pull JSON dumps and stable vendor ids."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.collector.adapters.cursor_dump import CursorPullDumper
from app.collector.adapters.cursor_verification_excel import VERIFICATION_FILENAME
from app.collector.adapters.usage_parsing import (
    cursor_vendor_event_id,
    parse_cursor_usage_page,
)


def test_cursor_vendor_event_id_is_stable_without_page_index() -> None:
    first = cursor_vendor_event_id(
        timestamp="1781804248151",
        user_email="rohith.sk@inapp.com",
        model="default",
    )
    second = cursor_vendor_event_id(
        timestamp="1781804248151",
        user_email="rohith.sk@inapp.com",
        model="default",
    )
    assert first == second
    assert first.startswith("cursor-1781804248151-")


def test_cursor_pull_dumper_writes_raw_parsed_and_summary(tmp_path: Path) -> None:
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 17, tzinfo=UTC)
    dumper = CursorPullDumper(tmp_path, tool_id="tool-123", since=since, until=until)

    payload = {
        "usageEvents": [
            {
                "timestamp": "1781804248151",
                "userEmail": "dev@acme.example",
                "model": "default",
                "kind": "Usage-based",
                "tokenUsage": {"inputTokens": 10, "outputTokens": 5},
                "chargedCents": 12.5,
            }
        ],
        "pagination": {"hasNextPage": False},
    }
    dumper.write_raw_page(
        source="filtered-usage-events",
        page=1,
        request_body={"page": 1},
        response_payload=payload,
        status_code=200,
    )
    records, _ = parse_cursor_usage_page(payload)
    dumper.add_parsed_records(records)
    dumper.write_parsed_records()
    summary_path = dumper.write_summary(
        pulled=len(records),
        ingested=1,
        skipped_duplicates=0,
        since=since,
        until=until,
    )

    assert summary_path.exists()
    assert (dumper.run_dir / "raw-filtered-usage-events-page-001.json").exists()
    assert (dumper.run_dir / "parsed-records.json").exists()
    assert (dumper.run_dir / VERIFICATION_FILENAME).exists()
    assert records[0].estimated_cost == Decimal("0.125")

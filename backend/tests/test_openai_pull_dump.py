"""Tests for OpenAI pull dump and verification export."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.collector.adapters.openai_dump import OpenAIPullDumper
from app.collector.adapters.openai_verification_excel import VERIFICATION_FILENAME


def test_openai_pull_dumper_writes_verification_excel(tmp_path: Path) -> None:
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 2, tzinfo=UTC)
    dumper = OpenAIPullDumper(tmp_path, tool_id="tool-1", since=since, until=until)
    dumper.write_raw_page(
        source="fetch_completions_usage",
        page=0,
        request_params={"start_time": int(since.timestamp())},
        response_payload={
            "data": [
                {
                    "start_time": int(since.timestamp()),
                    "results": [
                        {
                            "input_tokens": 100,
                            "output_tokens": 50,
                            "num_model_requests": 2,
                        }
                    ],
                }
            ]
        },
        status_code=200,
        url="https://api.openai.com/v1/organization/usage/completions",
    )
    dumper.add_parsed_records(
        [
            {
                "vendor_event_id": "openai-completions--unknown-1",
                "model": "unknown",
                "occurred_at": since.isoformat(),
                "input_tokens": 100,
                "output_tokens": 50,
                "estimated_cost": str(Decimal("1.25")),
                "requests": 2,
            }
        ]
    )
    dumper.write_parsed_records()
    dumper.write_summary(pulled=1, ingested=1, skipped_duplicates=0, since=since, until=until)

    assert (dumper.run_dir / "parsed-records.json").is_file()
    assert (dumper.run_dir / VERIFICATION_FILENAME).is_file()
    assert (dumper.run_dir / "sync-summary.json").is_file()

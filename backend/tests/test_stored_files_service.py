"""Tests for stored verification file listing."""

from datetime import UTC, datetime
from pathlib import Path

from app.collector.adapters.cursor_dump import create_cursor_pull_dumper
from app.collector.adapters.cursor_verification_excel import VERIFICATION_FILENAME
from app.config import Settings
from app.files.service import StoredFilesService


def test_list_cursor_pull_runs_includes_excel(tmp_path: Path) -> None:
    settings = Settings.model_validate(
        {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db",
            "LOCAL_STORAGE_ROOT": str(tmp_path),
        }
    )
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 17, tzinfo=UTC)
    dumper = create_cursor_pull_dumper(
        enabled=True,
        storage_root=str(tmp_path),
        tool_id="tool-abc",
        since=since,
        until=until,
    )
    assert dumper is not None
    dumper.write_raw_page(
        source="filtered-usage-events",
        page=1,
        request_body={"page": 1},
        response_payload={"usageEvents": [], "pagination": {"hasNextPage": False}},
        status_code=200,
    )
    dumper.write_summary(pulled=0, ingested=0, skipped_duplicates=0, since=since, until=until)

    service = StoredFilesService(settings)
    response = service.list_cursor_pull_runs()
    assert len(response.data) == 1
    run = response.data[0]
    assert run.tool_id == "tool-abc"
    assert run.has_verification_excel is True
    assert run.verification_excel_path is not None
    assert run.verification_excel_path.endswith(VERIFICATION_FILENAME)
    assert run.storage_path.startswith("cursor-pulls/tool-abc/")
    assert response.storage_root == str(tmp_path)

    file_path, media_type = service.resolve_cursor_pull_file(
        run.tool_id,
        run.run_id,
        VERIFICATION_FILENAME,
    )
    assert file_path.is_file()
    assert "spreadsheetml" in media_type


def test_list_backfills_excel_for_legacy_json_only_run(tmp_path: Path) -> None:
    settings = Settings.model_validate(
        {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/db",
            "LOCAL_STORAGE_ROOT": str(tmp_path),
        }
    )
    run_dir = tmp_path / "cursor-pulls" / "tool-legacy" / "20260619T120000Z"
    run_dir.mkdir(parents=True)
    (run_dir / "sync-summary.json").write_text(
        '{"pulled_records": 1, "ingested_new": 1, "skipped_duplicates": 0}',
        encoding="utf-8",
    )
    (run_dir / "raw-filtered-usage-events-page-001.json").write_text(
        """
        {
          "source": "filtered-usage-events",
          "page": 1,
          "response": {
            "usageEvents": [
              {
                "timestamp": "1",
                "userEmail": "a@example.com",
                "model": "default",
                "kind": "Usage-based",
                "tokenUsage": {"inputTokens": 10, "outputTokens": 5},
                "chargedCents": 100
              }
            ]
          }
        }
        """,
        encoding="utf-8",
    )

    response = StoredFilesService(settings).list_cursor_pull_runs()
    assert len(response.data) == 1
    assert response.data[0].has_verification_excel is True
    assert (run_dir / VERIFICATION_FILENAME).is_file()

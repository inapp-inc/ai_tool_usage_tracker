"""Write GitHub Copilot API pull payloads to JSON files for verification."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from app.collector.adapters.copilot_verification_excel import (
    VERIFICATION_FILENAME,
    write_calculation_verification_excel,
)

logger = logging.getLogger(__name__)


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class CopilotPullDumper:
    """Persist raw Copilot API responses and parsed rows under local storage."""

    def __init__(
        self,
        base_dir: Path,
        *,
        tool_id: UUID | str | None,
        since: datetime,
        until: datetime,
    ) -> None:
        started = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        tool_part = str(tool_id) if tool_id is not None else "unknown-tool"
        self.run_dir = base_dir / tool_part / started
        self._since = since.astimezone(UTC).isoformat()
        self._until = until.astimezone(UTC).isoformat()
        self._raw_pages: list[dict[str, Any]] = []
        self._parsed_rows: list[dict[str, Any]] = []
        self._metrics_file_index = 0
        self._ingested_vendor_ids: set[str] = set()
        self._skipped_duplicate_vendor_ids: set[str] = set()

    def set_ingest_audit(
        self,
        *,
        ingested_vendor_ids: list[str] | set[str],
        skipped_duplicate_vendor_ids: list[str] | set[str],
    ) -> None:
        self._ingested_vendor_ids = set(ingested_vendor_ids)
        self._skipped_duplicate_vendor_ids = set(skipped_duplicate_vendor_ids)

    def write_raw_page(
        self,
        *,
        source: str,
        page: int,
        request_body: dict[str, Any],
        response_payload: object,
        status_code: int,
    ) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "source": source,
            "page": page,
            "status_code": status_code,
            "request": request_body,
            "response": response_payload,
        }
        self._raw_pages.append(entry)
        path = self.run_dir / f"raw-{source}-page-{page:03d}.json"
        path.write_text(
            json.dumps(entry, indent=2, default=_json_default),
            encoding="utf-8",
        )
        logger.info("Copilot pull dump wrote %s", path)
        return path

    def write_metrics_rows(
        self,
        *,
        day: str,
        download_url: str,
        rows: list[dict[str, Any]],
        download_status: int | None = None,
        download_error: str | None = None,
    ) -> Path:
        self._metrics_file_index += 1
        request_body = {
            "day": day,
            "download_url": download_url,
            "download_status": download_status,
            "download_error": download_error,
        }
        self.write_raw_page(
            source="copilot-metrics-rows",
            page=self._metrics_file_index,
            request_body=request_body,
            response_payload=rows,
            status_code=download_status if download_status is not None else (200 if rows else 204),
        )
        return self.run_dir / f"raw-copilot-metrics-rows-page-{self._metrics_file_index:03d}.json"

    def add_parsed_records(self, records: list[Any]) -> None:
        for record in records:
            if is_dataclass(record):
                row = asdict(record)
            elif isinstance(record, dict):
                row = dict(record)
            else:
                continue
            for key, value in list(row.items()):
                if isinstance(value, Decimal):
                    row[key] = str(value)
                elif isinstance(value, datetime):
                    row[key] = value.astimezone(UTC).isoformat()
            self._parsed_rows.append(row)

    def write_parsed_records(self) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / "parsed-records.json"
        path.write_text(
            json.dumps(self._parsed_rows, indent=2, default=_json_default),
            encoding="utf-8",
        )
        logger.info("Copilot pull dump wrote %s (%s rows)", path, len(self._parsed_rows))
        return path

    def write_summary(
        self,
        *,
        pulled: int,
        ingested: int,
        skipped_duplicates: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "provider": "copilot",
            "since": (since or datetime.fromisoformat(self._since)).astimezone(UTC).isoformat(),
            "until": (until or datetime.fromisoformat(self._until)).astimezone(UTC).isoformat(),
            "pulled_records": pulled,
            "ingested_new": ingested,
            "skipped_duplicates": skipped_duplicates,
            "raw_page_count": len(self._raw_pages),
            "parsed_record_count": len(self._parsed_rows),
            "ingested_vendor_ids": sorted(self._ingested_vendor_ids),
            "skipped_duplicate_vendor_ids": sorted(self._skipped_duplicate_vendor_ids),
            "dump_directory": str(self.run_dir),
        }
        path = self.run_dir / "sync-summary.json"
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        excel_path = self.run_dir / VERIFICATION_FILENAME
        write_calculation_verification_excel(
            output_path=excel_path,
            raw_pages=self._raw_pages,
            parsed_records=self._parsed_rows,
            pulled=pulled,
            ingested=ingested,
            skipped_duplicates=skipped_duplicates,
            ingested_vendor_ids=self._ingested_vendor_ids,
            skipped_duplicate_vendor_ids=self._skipped_duplicate_vendor_ids,
            since=summary["since"],
            until=summary["until"],
        )
        summary["verification_excel"] = VERIFICATION_FILENAME
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        logger.info(
            "Copilot sync summary | pulled=%s ingested=%s skipped_duplicates=%s dir=%s excel=%s",
            pulled,
            ingested,
            skipped_duplicates,
            self.run_dir,
            excel_path,
        )
        return path


def create_copilot_pull_dumper(
    *,
    enabled: bool,
    storage_root: str,
    tool_id: UUID | str | None,
    since: datetime,
    until: datetime,
) -> CopilotPullDumper | None:
    if not enabled:
        return None
    base_dir = Path(storage_root) / "copilot-pulls"
    return CopilotPullDumper(base_dir, tool_id=tool_id, since=since, until=until)

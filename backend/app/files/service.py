"""Read stored verification artifacts from local storage."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.collector.adapters.cursor_verification_excel import (
    VERIFICATION_FILENAME,
    write_calculation_verification_excel,
)
from app.config import Settings
from app.files.schemas import CursorPullFileItem, CursorPullRunItem, CursorPullRunListResponse

logger = logging.getLogger(__name__)

_RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")
_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9._-]+$")


class StoredFilesService:
    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.local_storage_root)
        self._cursor_pulls = self._root / "cursor-pulls"

    def list_cursor_pull_runs(self) -> CursorPullRunListResponse:
        if not self._cursor_pulls.is_dir():
            return CursorPullRunListResponse(
                storage_root=str(self._root),
                cursor_pulls_dir=str(self._cursor_pulls),
                data=[],
            )

        runs: list[CursorPullRunItem] = []
        for tool_dir in sorted(self._cursor_pulls.iterdir(), reverse=True):
            if not tool_dir.is_dir():
                continue
            for run_dir in sorted(tool_dir.iterdir(), reverse=True):
                if not run_dir.is_dir() or not _RUN_ID_PATTERN.match(run_dir.name):
                    continue
                summary = self._read_summary(run_dir)
                storage_path = f"cursor-pulls/{tool_dir.name}/{run_dir.name}"
                excel_path = self._ensure_verification_excel(run_dir, summary)
                has_excel = excel_path.is_file()
                files = [
                    CursorPullFileItem(
                        name=path.name,
                        download_path=self._download_api_path(
                            tool_dir.name,
                            run_dir.name,
                            path.name,
                        ),
                    )
                    for path in sorted(run_dir.iterdir())
                    if path.is_file()
                ]
                runs.append(
                    CursorPullRunItem(
                        tool_id=tool_dir.name,
                        run_id=run_dir.name,
                        storage_path=storage_path,
                        since=summary.get("since") if summary else None,
                        until=summary.get("until") if summary else None,
                        pulled_records=summary.get("pulled_records") if summary else None,
                        ingested_new=summary.get("ingested_new") if summary else None,
                        skipped_duplicates=summary.get("skipped_duplicates")
                        if summary
                        else None,
                        has_verification_excel=has_excel,
                        verification_excel_path=self._download_api_path(
                            tool_dir.name,
                            run_dir.name,
                            VERIFICATION_FILENAME,
                        )
                        if has_excel
                        else None,
                        files=files,
                    )
                )
        return CursorPullRunListResponse(
            storage_root=str(self._root),
            cursor_pulls_dir=str(self._cursor_pulls),
            data=runs,
        )

    def resolve_cursor_pull_file(
        self,
        tool_id: str,
        run_id: str,
        filename: str,
    ) -> tuple[Path, str]:
        self._validate_segment(tool_id, "tool_id")
        self._validate_segment(run_id, "run_id")
        if not _SAFE_FILENAME.match(filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename.",
            )

        run_dir = (self._cursor_pulls / tool_id / run_id).resolve()
        if not str(run_dir).startswith(str(self._cursor_pulls.resolve())):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path.")
        if not run_dir.is_dir():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

        if filename == VERIFICATION_FILENAME and not (run_dir / filename).is_file():
            summary = self._read_summary(run_dir)
            self._ensure_verification_excel(run_dir, summary)

        file_path = (run_dir / filename).resolve()
        if not str(file_path).startswith(str(run_dir)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path.")
        if not file_path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

        media_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if filename.endswith(".xlsx")
            else "application/json"
            if filename.endswith(".json")
            else "application/octet-stream"
        )
        return file_path, media_type

    def _ensure_verification_excel(
        self,
        run_dir: Path,
        summary: dict[str, Any] | None,
    ) -> Path:
        excel_path = run_dir / VERIFICATION_FILENAME
        if excel_path.is_file():
            return excel_path

        raw_pages = self._load_raw_pages(run_dir)
        if not raw_pages:
            return excel_path

        try:
            write_calculation_verification_excel(
                output_path=excel_path,
                raw_pages=raw_pages,
                pulled=int(summary.get("pulled_records") or 0) if summary else 0,
                ingested=int(summary.get("ingested_new") or 0) if summary else 0,
                skipped_duplicates=int(summary.get("skipped_duplicates") or 0)
                if summary
                else 0,
            )
            logger.info("Backfilled verification Excel for %s", run_dir)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to backfill verification Excel for %s", run_dir)
        return excel_path

    @staticmethod
    def _load_raw_pages(run_dir: Path) -> list[dict[str, Any]]:
        pages: list[dict[str, Any]] = []
        for path in sorted(run_dir.glob("raw-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                pages.append(payload)
        return pages

    @staticmethod
    def _download_api_path(tool_id: str, run_id: str, filename: str) -> str:
        return f"/files/cursor-pulls/{tool_id}/{run_id}/{filename}"

    @staticmethod
    def _validate_segment(value: str, label: str) -> None:
        if not value or ".." in value or "/" in value or "\\" in value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {label}.",
            )

    @staticmethod
    def _read_summary(run_dir: Path) -> dict[str, Any] | None:
        summary_path = run_dir / "sync-summary.json"
        if not summary_path.is_file():
            return None
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

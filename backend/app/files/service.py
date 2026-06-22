"""Read stored verification artifacts from local storage."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.collector.adapters.copilot_verification_excel import (
    VERIFICATION_FILENAME as COPILOT_VERIFICATION_FILENAME,
    write_calculation_verification_excel as write_copilot_verification_excel,
)
from app.collector.adapters.openai_verification_excel import (
    VERIFICATION_FILENAME as OPENAI_VERIFICATION_FILENAME,
    write_calculation_verification_excel as write_openai_verification_excel,
)
from app.collector.adapters.cursor_verification_excel import (
    VERIFICATION_FILENAME as CURSOR_VERIFICATION_FILENAME,
    write_calculation_verification_excel as write_cursor_verification_excel,
)
from app.config import Settings
from app.files.schemas import CursorPullFileItem, CursorPullRunItem, CursorPullRunListResponse

logger = logging.getLogger(__name__)

VERIFICATION_FILENAME = CURSOR_VERIFICATION_FILENAME

_RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")
_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9._-]+$")


class StoredFilesService:
    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.local_storage_root)
        self._cursor_pulls = self._root / "cursor-pulls"
        self._copilot_pulls = self._root / "copilot-pulls"
        self._openai_pulls = self._root / "openai-pulls"

    def list_cursor_pull_runs(self) -> CursorPullRunListResponse:
        return self._list_pull_runs(
            pulls_dir=self._cursor_pulls,
            pulls_dir_label=str(self._cursor_pulls),
            download_prefix="/files/cursor-pulls",
            write_excel=self._write_cursor_verification_excel,
        )

    def list_copilot_pull_runs(self) -> CursorPullRunListResponse:
        response = self._list_pull_runs(
            pulls_dir=self._copilot_pulls,
            pulls_dir_label=str(self._copilot_pulls),
            download_prefix="/files/copilot-pulls",
            write_excel=self._write_copilot_verification_excel,
        )
        return CursorPullRunListResponse(
            storage_root=response.storage_root,
            cursor_pulls_dir=response.cursor_pulls_dir,
            data=response.data,
        )

    def resolve_cursor_pull_file(
        self,
        tool_id: str,
        run_id: str,
        filename: str,
    ) -> tuple[Path, str]:
        return self._resolve_pull_file(
            self._cursor_pulls,
            tool_id,
            run_id,
            filename,
            write_excel=self._write_cursor_verification_excel,
        )

    def resolve_copilot_pull_file(
        self,
        tool_id: str,
        run_id: str,
        filename: str,
    ) -> tuple[Path, str]:
        return self._resolve_pull_file(
            self._copilot_pulls,
            tool_id,
            run_id,
            filename,
            write_excel=self._write_copilot_verification_excel,
            verification_filename=COPILOT_VERIFICATION_FILENAME,
        )

    def list_openai_pull_runs(self) -> CursorPullRunListResponse:
        response = self._list_pull_runs(
            pulls_dir=self._openai_pulls,
            pulls_dir_label=str(self._openai_pulls),
            download_prefix="/files/openai-pulls",
            write_excel=self._write_openai_verification_excel,
            verification_filename=OPENAI_VERIFICATION_FILENAME,
        )
        return CursorPullRunListResponse(
            storage_root=response.storage_root,
            cursor_pulls_dir=response.cursor_pulls_dir,
            data=response.data,
        )

    def resolve_openai_pull_file(
        self,
        tool_id: str,
        run_id: str,
        filename: str,
    ) -> tuple[Path, str]:
        return self._resolve_pull_file(
            self._openai_pulls,
            tool_id,
            run_id,
            filename,
            write_excel=self._write_openai_verification_excel,
            verification_filename=OPENAI_VERIFICATION_FILENAME,
        )

    def _list_pull_runs(
        self,
        *,
        pulls_dir: Path,
        pulls_dir_label: str,
        download_prefix: str,
        write_excel: Callable[..., Path],
        verification_filename: str = VERIFICATION_FILENAME,
    ) -> CursorPullRunListResponse:
        if not pulls_dir.is_dir():
            return CursorPullRunListResponse(
                storage_root=str(self._root),
                cursor_pulls_dir=pulls_dir_label,
                data=[],
            )

        runs: list[CursorPullRunItem] = []
        for tool_dir in sorted(pulls_dir.iterdir(), reverse=True):
            if not tool_dir.is_dir():
                continue
            for run_dir in sorted(tool_dir.iterdir(), reverse=True):
                if not run_dir.is_dir() or not _RUN_ID_PATTERN.match(run_dir.name):
                    continue
                summary = self._read_summary(run_dir)
                storage_path = f"{pulls_dir.name}/{tool_dir.name}/{run_dir.name}"
                excel_path = self._ensure_verification_excel(run_dir, summary, write_excel)
                has_excel = excel_path.is_file()
                files = [
                    CursorPullFileItem(
                        name=path.name,
                        download_path=f"{download_prefix}/{tool_dir.name}/{run_dir.name}/{path.name}",
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
                        verification_excel_path=(
                            f"{download_prefix}/{tool_dir.name}/{run_dir.name}/{verification_filename}"
                            if has_excel
                            else None
                        ),
                        files=files,
                    )
                )
        return CursorPullRunListResponse(
            storage_root=str(self._root),
            cursor_pulls_dir=pulls_dir_label,
            data=runs,
        )

    def _resolve_pull_file(
        self,
        pulls_dir: Path,
        tool_id: str,
        run_id: str,
        filename: str,
        *,
        write_excel: Callable[..., Path],
        verification_filename: str = VERIFICATION_FILENAME,
    ) -> tuple[Path, str]:
        self._validate_segment(tool_id, "tool_id")
        self._validate_segment(run_id, "run_id")
        if not _SAFE_FILENAME.match(filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename.",
            )

        run_dir = (pulls_dir / tool_id / run_id).resolve()
        if not str(run_dir).startswith(str(pulls_dir.resolve())):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path.")
        if not run_dir.is_dir():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

        if filename == verification_filename and not (run_dir / filename).is_file():
            summary = self._read_summary(run_dir)
            self._ensure_verification_excel(run_dir, summary, write_excel)

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
        write_excel: Callable[..., Path],
    ) -> Path:
        excel_path = run_dir / VERIFICATION_FILENAME
        if excel_path.is_file():
            return excel_path

        raw_pages = self._load_raw_pages(run_dir)
        if not raw_pages:
            return excel_path

        parsed_records: list[dict[str, Any]] | None = None
        parsed_path = run_dir / "parsed-records.json"
        if parsed_path.is_file():
            try:
                payload = json.loads(parsed_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, list):
                parsed_records = payload

        try:
            ingested_ids = summary.get("ingested_vendor_ids") if summary else None
            skipped_ids = summary.get("skipped_duplicate_vendor_ids") if summary else None
            write_excel(
                output_path=excel_path,
                raw_pages=raw_pages,
                parsed_records=parsed_records,
                pulled=int(summary.get("pulled_records") or 0) if summary else 0,
                ingested=int(summary.get("ingested_new") or 0) if summary else 0,
                skipped_duplicates=int(summary.get("skipped_duplicates") or 0)
                if summary
                else 0,
                ingested_vendor_ids=set(ingested_ids or []),
                skipped_duplicate_vendor_ids=set(skipped_ids or []),
                since=str(summary.get("since")) if summary and summary.get("since") else None,
                until=str(summary.get("until")) if summary and summary.get("until") else None,
            )
            logger.info("Backfilled verification Excel for %s", run_dir)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to backfill verification Excel for %s", run_dir)
        return excel_path

    @staticmethod
    def _write_cursor_verification_excel(**kwargs: Any) -> Path:
        return write_cursor_verification_excel(
            output_path=kwargs["output_path"],
            raw_pages=kwargs["raw_pages"],
            pulled=kwargs["pulled"],
            ingested=kwargs["ingested"],
            skipped_duplicates=kwargs["skipped_duplicates"],
        )

    @staticmethod
    def _write_copilot_verification_excel(**kwargs: Any) -> Path:
        return write_copilot_verification_excel(**kwargs)

    @staticmethod
    def _write_openai_verification_excel(**kwargs: Any) -> Path:
        return write_openai_verification_excel(**kwargs)

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

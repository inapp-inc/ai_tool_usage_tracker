"""File upload ingestion service."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.tools.csv_importer import (
    CsvColumnMapping,
    CsvImportParseError,
    CsvImportResult,
    inspect_tool_usage_csv,
    parse_tool_usage_csv,
)
from app.admin.tools.schemas import ToolCsvColumnMapping, ToolCsvInspectResponse
from app.auth.service import AuthenticatedUser
from app.config import get_settings
from app.platform.org_store import OrgDataStore

UPLOADS_KEY = "uploads"
MAX_BYTES = 50 * 1024 * 1024


class UploadNotFoundError(Exception):
    """Upload not found."""


class UploadCsvError(Exception):
    """CSV upload could not be inspected or parsed."""


class UploadService:
    """Org-scoped usage file uploads."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._store = OrgDataStore(session)
        self._settings = get_settings()

    def _storage_dir(self, organization_id: uuid.UUID) -> Path:
        root = Path(self._settings.local_storage_root) / "uploads" / str(organization_id)
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _csv_mapping_from_schema(
        mapping: ToolCsvColumnMapping | None,
    ) -> CsvColumnMapping | None:
        if mapping is None or not mapping.token_column:
            return None
        return CsvColumnMapping(
            token_column=mapping.token_column,
            cost_column=mapping.cost_column,
            date_column=mapping.date_column,
            date_from_column=mapping.date_from_column,
            date_to_column=mapping.date_to_column,
        )

    def _meta_path(self, organization_id: uuid.UUID, upload_id: str) -> Path:
        return self._storage_dir(organization_id) / f"{upload_id}.meta.json"

    def _load_saved_mapping(
        self, organization_id: uuid.UUID, upload_id: str
    ) -> ToolCsvColumnMapping | None:
        meta_path = self._meta_path(organization_id, upload_id)
        if not meta_path.exists():
            return None
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return ToolCsvColumnMapping.model_validate(data)

    async def list_uploads(self, user: AuthenticatedUser) -> list[dict[str, Any]]:
        return await self._store.list_items(user.organization_id, UPLOADS_KEY)

    async def create_upload(
        self,
        user: AuthenticatedUser,
        *,
        file_name: str,
        content: bytes,
        team_id: str | None,
    ) -> dict[str, Any]:
        if len(content) > MAX_BYTES:
            raise ValueError("File exceeds the 50 MB limit.")
        upload_id = str(uuid.uuid4())
        path = self._storage_dir(user.organization_id) / f"{upload_id}.csv"
        path.write_bytes(content)

        record = {
            "id": upload_id,
            "file_name": file_name,
            "format": "json" if file_name.lower().endswith(".json") else "csv",
            "status": "preview_ready",
            "row_count": None,
            "error_count": None,
            "error_message": None,
            "uploaded_by_name": user.display_name or user.email,
            "team_id": team_id,
            "team_name": None,
            "file_size_kb": max(1, round(len(content) / 1024)),
            "created_at": datetime.now(UTC).isoformat(),
            "processed_at": datetime.now(UTC).isoformat(),
        }
        await self._store.append_item(user.organization_id, UPLOADS_KEY, record)
        await self._session.commit()
        return record

    async def get_upload(
        self, user: AuthenticatedUser, upload_id: str
    ) -> dict[str, Any]:
        record = await self._store.get_item(
            user.organization_id, UPLOADS_KEY, upload_id
        )
        if record is None:
            raise UploadNotFoundError
        return record

    async def _read_content(self, user: AuthenticatedUser, upload_id: str) -> bytes:
        path = self._storage_dir(user.organization_id) / f"{upload_id}.csv"
        if not path.exists():
            raise UploadNotFoundError
        return path.read_bytes()

    async def inspect_upload(
        self, user: AuthenticatedUser, upload_id: str
    ) -> ToolCsvInspectResponse:
        record = await self.get_upload(user, upload_id)
        if record.get("format") != "csv":
            raise UploadCsvError("Column mapping is only supported for CSV uploads.")

        content = await self._read_content(user, upload_id)
        try:
            inspected = inspect_tool_usage_csv(content)
        except CsvImportParseError as exc:
            raise UploadCsvError(str(exc)) from exc

        suggested = inspected.suggested_mapping
        return ToolCsvInspectResponse(
            headers=inspected.headers,
            row_count=inspected.row_count,
            format_hint=inspected.format_hint,
            suggested_mapping=ToolCsvColumnMapping(
                token_column=suggested.token_column,
                cost_column=suggested.cost_column,
                date_column=suggested.date_column,
                date_from_column=suggested.date_from_column,
                date_to_column=suggested.date_to_column,
            ),
        )

    @staticmethod
    def _preview_rows_from_parsed(
        parsed: CsvImportResult,
        *,
        file_name: str,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for index, day in enumerate(parsed.daily_usage, start=1):
            rows.append(
                {
                    "row_index": index,
                    "user_id": "csv",
                    "user_name": "CSV import",
                    "model": file_name,
                    "tokens": day["tokens"],
                    "cost": day["cost"],
                    "timestamp": f"{day['date']}T00:00:00Z",
                    "status": "valid",
                    "error_reason": None,
                }
            )
        return rows

    async def get_preview(
        self,
        user: AuthenticatedUser,
        upload_id: str,
        *,
        mapping: ToolCsvColumnMapping | None = None,
    ) -> dict[str, Any]:
        record = await self.get_upload(user, upload_id)
        content = await self._read_content(user, upload_id)
        file_name = record.get("file_name", "upload.csv")

        if record.get("format") == "json":
            return {
                "upload_id": upload_id,
                "file_name": file_name,
                "total_rows": 0,
                "valid_rows": 0,
                "error_rows": 0,
                "rows": [],
                "token_count": 0,
                "cost_total": 0.0,
                "date_from": None,
                "date_to": None,
                "source_row_count": 0,
                "parse_error": "JSON uploads do not support column mapping yet.",
                "needs_mapping": False,
            }

        csv_mapping = self._csv_mapping_from_schema(mapping)
        if csv_mapping is None:
            csv_mapping = self._csv_mapping_from_schema(
                self._load_saved_mapping(user.organization_id, upload_id)
            )

        try:
            parsed = parse_tool_usage_csv(content, mapping=csv_mapping)
        except CsvImportParseError as exc:
            return {
                "upload_id": upload_id,
                "file_name": file_name,
                "total_rows": 0,
                "valid_rows": 0,
                "error_rows": 0,
                "rows": [],
                "token_count": 0,
                "cost_total": 0.0,
                "date_from": None,
                "date_to": None,
                "source_row_count": 0,
                "parse_error": str(exc),
                "needs_mapping": True,
            }

        rows = self._preview_rows_from_parsed(parsed, file_name=file_name)
        if mapping is not None:
            await self.save_column_mapping(
                user,
                upload_id,
                mapping.model_dump(exclude_none=True),
            )

        await self._store.update_item(
            user.organization_id,
            UPLOADS_KEY,
            upload_id,
            {
                "status": "preview_ready",
                "row_count": parsed.row_count,
                "error_count": 0,
                "error_message": None,
            },
        )
        await self._session.commit()

        return {
            "upload_id": upload_id,
            "file_name": file_name,
            "total_rows": len(rows),
            "valid_rows": len(rows),
            "error_rows": 0,
            "rows": rows,
            "token_count": parsed.token_count,
            "cost_total": parsed.cost_total,
            "date_from": parsed.date_from,
            "date_to": parsed.date_to,
            "source_row_count": parsed.row_count,
            "parse_error": None,
            "needs_mapping": False,
        }

    async def submit_upload(
        self,
        user: AuthenticatedUser,
        upload_id: str,
        *,
        team_id: str | None,
    ) -> dict[str, Any]:
        record = await self.get_upload(user, upload_id)
        updated = await self._store.update_item(
            user.organization_id,
            UPLOADS_KEY,
            upload_id,
            {
                "status": "completed",
                "team_id": team_id,
                "processed_at": datetime.now(UTC).isoformat(),
            },
        )
        await self._session.commit()
        return updated or record

    async def delete_upload(self, user: AuthenticatedUser, upload_id: str) -> None:
        storage_dir = self._storage_dir(user.organization_id)
        for suffix in (".csv", ".meta.json"):
            path = storage_dir / f"{upload_id}{suffix}"
            if path.exists():
                path.unlink()
        deleted = await self._store.delete_item(
            user.organization_id, UPLOADS_KEY, upload_id
        )
        if not deleted:
            raise UploadNotFoundError
        await self._session.commit()

    async def save_column_mapping(
        self,
        user: AuthenticatedUser,
        upload_id: str,
        mapping: dict[str, str | None],
    ) -> None:
        meta_path = self._meta_path(user.organization_id, upload_id)
        meta_path.write_text(json.dumps(mapping), encoding="utf-8")

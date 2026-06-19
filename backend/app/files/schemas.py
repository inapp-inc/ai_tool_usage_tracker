"""Schemas for stored verification file downloads."""

from pydantic import BaseModel, Field


class CursorPullFileItem(BaseModel):
    name: str
    download_path: str


class CursorPullRunItem(BaseModel):
    tool_id: str
    run_id: str
    storage_path: str
    since: str | None = None
    until: str | None = None
    pulled_records: int | None = None
    ingested_new: int | None = None
    skipped_duplicates: int | None = None
    has_verification_excel: bool = False
    verification_excel_path: str | None = None
    files: list[CursorPullFileItem] = Field(default_factory=list)


class CursorPullRunListResponse(BaseModel):
    storage_root: str
    cursor_pulls_dir: str
    data: list[CursorPullRunItem]

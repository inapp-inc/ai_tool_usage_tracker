"""Pydantic schemas for Uploads API."""

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

UploadStatusApi = Literal[
    "pending",
    "pending_mapping",
    "parsing",
    "preview_ready",
    "committing",
    "completed",
    "failed",
    "deleted",
]


class UploadResponse(BaseModel):
    id: UUID
    team_id: UUID | None = None
    tool_id: UUID | None = None
    team_name: str | None = None
    filename: str
    detected_format: str | None = None
    size_bytes: int
    status: UploadStatusApi
    total_rows: int | None = None
    matched_rows: int | None = None
    unmatched_rows: int | None = None
    error_message: str | None = None
    uploaded_by_name: str | None = None
    tool_name: str | None = None
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    created_at: datetime
    completed_at: datetime | None = None


class UploadCreateResponse(BaseModel):
    upload_id: UUID
    status: UploadStatusApi
    filename: str
    size_bytes: int
    upload: UploadResponse


class ParsedUsageRowResponse(BaseModel):
    row_number: int
    user_email: str | None = None
    matched_user_id: UUID | None = None
    user_name: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    occurred_at: datetime | None = None
    model: str | None = None
    cost: float = 0.0
    status: Literal["valid", "error"] = "valid"
    error_reason: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    mapped_data: dict[str, Any] = Field(default_factory=dict)


class UploadPreviewResponse(BaseModel):
    upload_id: UUID
    filename: str
    team_id: UUID | None = None
    team_name: str | None = None
    tool_id: UUID | None = None
    total_rows: int
    matched_rows: int
    unmatched_rows: int
    rows: list[ParsedUsageRowResponse]
    copilot_summary: dict[str, Any] | None = None
    figma_summary: dict[str, Any] | None = None


class UploadCommitRequest(BaseModel):
    team_id: UUID | None = None
    row_numbers: list[int] | None = None


class UploadColumnMappingRequest(BaseModel):
    email: str | None = None
    cost: str | None = None
    model: str | None = None
    input_tokens: str | None = None
    output_tokens: str | None = None
    tokens: str | None = None
    timestamp: str | None = None
    tool: str | None = None
    sku: str | None = None
    unit_type: str | None = None
    monthly_amount: str | None = None
    net_amount: str | None = None
    quantity: str | None = None
    billing_period_start: str | None = None
    billing_period_end: str | None = None
    user_login: str | None = None
    user_id: str | None = None
    user_email: str | None = None
    user_name: str | None = None
    seat_type: str | None = None
    seat_credits_used: str | None = None
    paid_credits_used: str | None = None
    last_activity: str | None = None
    usage_period_start: str | None = None
    usage_period_end: str | None = None


class UploadMappingField(BaseModel):
    key: str
    label: str
    required: bool = False


class UploadMappingResponse(BaseModel):
    upload_id: UUID
    filename: str
    headers: list[str]
    fields: list[UploadMappingField]
    suggested_mapping: dict[str, str | None]
    column_mapping: dict[str, str | None] | None = None
    sample_row: dict[str, Any] = Field(default_factory=dict)


class PaginationMeta(BaseModel):
    limit: int | None = None
    next_cursor: str | None = None
    has_more: bool = False


class UploadListResponse(BaseModel):
    data: list[UploadResponse]
    meta: PaginationMeta

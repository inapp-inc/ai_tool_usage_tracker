"""Pydantic schemas for Reports API."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ReportTypeApi = Literal[
    "tool_usage_summary",
    "team_usage",
    "cost",
    "user_usage",
    "alert_history",
    "api_key_activity",
]
ReportFormatApi = Literal["json", "csv", "pdf"]
JobStatusApi = Literal["pending", "processing", "completed", "failed"]


class ReportGenerateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    report_type: ReportTypeApi
    from_dt: datetime = Field(alias="from")
    to_dt: datetime = Field(alias="to")
    format: ReportFormatApi = "csv"
    team_id: UUID | None = None
    tool_id: UUID | None = None
    user_id: UUID | None = None
    schedule: str = "once"
    team_ids: list[UUID] = Field(default_factory=list)
    async_mode: bool = Field(default=False, alias="async")

    model_config = {"populate_by_name": True}


class ReportJobResponse(BaseModel):
    job_id: UUID
    name: str
    report_type: ReportTypeApi
    status: JobStatusApi
    format: ReportFormatApi
    from_dt: datetime = Field(serialization_alias="from")
    to_dt: datetime = Field(serialization_alias="to")
    schedule: str
    team_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    file_size_kb: int | None = None
    created_by_name: str | None = None
    subscription_count: int = 0

    model_config = {"populate_by_name": True}


class ReportListResponse(BaseModel):
    data: list[ReportJobResponse]


class SubscriptionCreateRequest(BaseModel):
    channel: Literal["email", "in_app", "both"]
    cadence: Literal["daily", "weekly", "monthly"]
    email_recipients: list[str] = Field(default_factory=list)


class SubscriptionResponse(BaseModel):
    id: UUID
    report_id: UUID
    channel: str
    cadence: str
    email_recipients: list[str]
    created_at: datetime
    created_by_name: str | None = None


class SubscriptionListResponse(BaseModel):
    data: list[SubscriptionResponse]

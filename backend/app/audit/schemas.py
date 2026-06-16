"""Audit log query schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

AuditOutcome = Literal["success", "failure"]


class AuditLogEntryResponse(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    actor_email: str | None = None
    actor_display_name: str | None = None
    actor_role: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    resource_name: str | None = None
    description: str
    outcome: AuditOutcome
    source_ip: str | None = None
    correlation_id: str | None = None
    created_at: datetime


class PaginationMeta(BaseModel):
    limit: int = 50
    has_more: bool = False
    next_cursor: str | None = None


class AuditLogListResponse(BaseModel):
    data: list[AuditLogEntryResponse]
    meta: PaginationMeta


class AuditLogExportRequest(BaseModel):
    from_dt: datetime = Field(alias="from")
    to_dt: datetime = Field(alias="to")
    actor_id: UUID | None = None
    action: str | None = None
    resource_type: str | None = None
    q: str | None = None

    model_config = {"populate_by_name": True}

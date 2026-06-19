"""Pydantic schemas for Thresholds / Alerts API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ThresholdTypeApi = Literal["token_count", "package_utilization_pct", "cost_amount"]
ThresholdScopeApi = Literal["organization", "team", "user", "tool"]
AlertSeverityApi = Literal["info", "warning", "critical"]


class ThresholdResponse(BaseModel):
    id: UUID
    name: str
    threshold_type: ThresholdTypeApi
    scope: ThresholdScopeApi
    tool_id: UUID | None = None
    team_id: UUID | None = None
    user_id: UUID | None = None
    team_name: str | None = None
    limit_value: Decimal
    severity: AlertSeverityApi
    active: bool
    notify_email: bool
    notify_in_app: bool
    webhook_url: str | None = None
    email_recipients: list[str] = Field(default_factory=list)
    trigger_count: int = 0
    last_triggered_at: datetime | None = None
    created_at: datetime


class ThresholdCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    threshold_type: ThresholdTypeApi
    scope: ThresholdScopeApi
    tool_id: UUID | None = None
    team_id: UUID | None = None
    user_id: UUID | None = None
    limit_value: Decimal = Field(ge=0)
    severity: AlertSeverityApi
    notify_email: bool = False
    notify_in_app: bool = True
    webhook_url: str | None = Field(default=None, max_length=512)
    email_recipients: list[str] = Field(default_factory=list)
    active: bool = True


class ThresholdUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    threshold_type: ThresholdTypeApi | None = None
    scope: ThresholdScopeApi | None = None
    tool_id: UUID | None = None
    team_id: UUID | None = None
    user_id: UUID | None = None
    limit_value: Decimal | None = Field(default=None, ge=0)
    severity: AlertSeverityApi | None = None
    notify_email: bool | None = None
    notify_in_app: bool | None = None
    webhook_url: str | None = Field(default=None, max_length=512)
    email_recipients: list[str] | None = None
    active: bool | None = None


class ThresholdEventResponse(BaseModel):
    id: UUID
    rule_id: UUID
    rule_name: str
    severity: AlertSeverityApi
    message: str
    team_name: str | None = None
    triggered_at: datetime
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None


class PaginationMeta(BaseModel):
    limit: int | None = None
    next_cursor: str | None = None
    has_more: bool = False


class ThresholdListResponse(BaseModel):
    data: list[ThresholdResponse]
    meta: PaginationMeta


class ThresholdEventListResponse(BaseModel):
    data: list[ThresholdEventResponse]
    meta: PaginationMeta

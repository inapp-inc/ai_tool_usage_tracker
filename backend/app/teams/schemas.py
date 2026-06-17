"""Pydantic schemas aligned with OpenAPI Team components."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MemberSource = Literal["platform", "tool", "upload"]


def _normalize_tool_ids(tool_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for tool_id in tool_ids:
        value = tool_id.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    token_budget: int | None = Field(default=None, gt=0)
    cost_budget: Decimal | None = Field(default=None, ge=0)
    tool_ids: list[str] = Field(default_factory=list)

    @field_validator("tool_ids")
    @classmethod
    def validate_tool_ids(cls, value: list[str]) -> list[str]:
        return _normalize_tool_ids(value)


class TeamUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    active: bool | None = None
    token_budget: int | None = Field(default=None, gt=0)
    cost_budget: Decimal | None = Field(default=None, ge=0)
    tool_ids: list[str] | None = None

    @field_validator("tool_ids")
    @classmethod
    def validate_tool_ids(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _normalize_tool_ids(value)


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    active: bool
    member_count: int = 0
    token_budget: int | None = None
    cost_budget: Decimal | None = None
    tool_ids: list[str] = Field(default_factory=list)
    tokens_used: int = 0
    pricing_total: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    last_synced_at: datetime | None = None
    created_at: datetime


class PaginationMeta(BaseModel):
    limit: int | None = None
    next_cursor: str | None = None
    has_more: bool = False


class TeamListResponse(BaseModel):
    data: list[TeamResponse]
    meta: PaginationMeta


class TeamMemberAddRequest(BaseModel):
    user_id: UUID


class TeamMemberResponse(BaseModel):
    user_id: UUID | None = None
    email: str
    display_name: str | None = None
    joined_at: datetime | None = None
    source: MemberSource = "platform"
    tool_id: UUID | None = None
    tool_name: str | None = None


class TeamMemberListResponse(BaseModel):
    data: list[TeamMemberResponse]
    meta: PaginationMeta


class TeamToolAssignmentResponse(BaseModel):
    id: UUID
    team_id: UUID
    tool_id: UUID
    tool_name: str
    pricing_model: str | None = None
    token_price: Decimal | None = None
    output_token_price: Decimal | None = None
    cost_per_seat: Decimal | None = None
    seat_count: int | None = None
    package_allowance: int | None = None
    overage_price: Decimal | None = None
    plan_name: str | None = None
    pricing_config: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TeamToolAssignRequest(BaseModel):
    tool_id: UUID
    pricing_model: str | None = None
    token_price: Decimal | None = Field(default=None, ge=0)
    output_token_price: Decimal | None = Field(default=None, ge=0)
    cost_per_seat: Decimal | None = Field(default=None, ge=0)
    seat_count: int | None = Field(default=None, ge=0)
    package_allowance: int | None = Field(default=None, ge=0)
    overage_price: Decimal | None = Field(default=None, ge=0)
    plan_name: str | None = Field(default=None, max_length=200)
    pricing_config: dict | None = None


class TeamToolUpdateRequest(BaseModel):
    pricing_model: str | None = None
    token_price: Decimal | None = Field(default=None, ge=0)
    output_token_price: Decimal | None = Field(default=None, ge=0)
    cost_per_seat: Decimal | None = Field(default=None, ge=0)
    seat_count: int | None = Field(default=None, ge=0)
    package_allowance: int | None = Field(default=None, ge=0)
    overage_price: Decimal | None = Field(default=None, ge=0)
    plan_name: str | None = Field(default=None, max_length=200)
    pricing_config: dict | None = None


class TeamToolAssignmentListResponse(BaseModel):
    data: list[TeamToolAssignmentResponse]
    meta: PaginationMeta


class TeamToolSyncResult(BaseModel):
    tool_id: UUID
    tool_name: str
    status: Literal["synced", "skipped", "failed"]
    message: str | None = None


class TeamSyncResponse(BaseModel):
    team_id: UUID
    synced_count: int
    skipped_count: int
    failed_count: int
    results: list[TeamToolSyncResult]

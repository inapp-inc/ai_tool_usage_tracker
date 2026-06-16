"""Pydantic schemas aligned with OpenAPI Team components."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MemberSource = Literal["platform", "tool"]


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

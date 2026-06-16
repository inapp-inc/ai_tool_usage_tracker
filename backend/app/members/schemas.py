"""Pydantic schemas for unified Members API."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.auth.schemas import Role

MemberSource = Literal["platform", "tool", "upload"]
MembersView = Literal["all", "invited"]


class MemberTeamSummary(BaseModel):
    id: UUID
    name: str
    joined_at: datetime | None = None


class MemberResponse(BaseModel):
    user_id: UUID | None = None
    email: str
    display_name: str | None = None
    role: Role | None = None
    active: bool | None = None
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    joined_at: datetime | None = None
    source: MemberSource = "platform"
    tool_id: UUID | None = None
    tool_name: str | None = None
    teams: list[MemberTeamSummary] = Field(default_factory=list)


class PaginationMeta(BaseModel):
    limit: int | None = None
    next_cursor: str | None = None
    has_more: bool = False


class MemberListResponse(BaseModel):
    data: list[MemberResponse]
    meta: PaginationMeta

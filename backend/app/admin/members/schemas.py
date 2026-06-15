"""Member management API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MemberTeamRef(BaseModel):
    id: UUID
    name: str


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    platform_role: str
    teams: list[MemberTeamRef] = Field(default_factory=list)
    status: str
    last_active_at: datetime | None = None
    created_at: datetime


class MemberListResponse(BaseModel):
    data: list[MemberResponse]


class MemberInviteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    platform_role: str
    team_ids: list[UUID] = Field(default_factory=list)


class MemberUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    platform_role: str | None = None
    team_ids: list[UUID] | None = None
    status: str | None = None

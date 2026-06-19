"""Pydantic schemas for Users API (org member admin)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.auth.schemas import Role

MemberSource = Literal["platform", "tool"]


class UserTeamSummary(BaseModel):
    id: UUID
    name: str
    joined_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: EmailStr
    display_name: str | None = None
    role: Role
    role_id: UUID | None = None
    role_name: str | None = None
    active: bool
    last_login_at: datetime | None = None
    created_at: datetime
    teams: list[UserTeamSummary] = Field(default_factory=list)


class UserCreateResponse(UserResponse):
    """Returned only from POST /users — includes the one-time temporary password."""

    temporary_password: str | None = None


class UserCreateRequest(BaseModel):
    email: EmailStr
    display_name: str | None = Field(default=None, max_length=200)
    role: Role = "team_member"
    role_id: UUID | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    team_ids: list[UUID] = Field(default_factory=list)


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    role: Role | None = None
    role_id: UUID | None = None
    active: bool | None = None
    team_ids: list[UUID] | None = None


class PaginationMeta(BaseModel):
    limit: int | None = None
    next_cursor: str | None = None
    has_more: bool = False


class UserListResponse(BaseModel):
    data: list[UserResponse]
    meta: PaginationMeta

"""Pydantic schemas aligned with OpenAPI auth components."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal[
    "super_admin",
    "org_admin",
    "team_admin",
    "finance_viewer",
    "team_member",
    "auditor",
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    display_name: str | None = None
    role: Role
    role_id: UUID | None = None
    role_name: str | None = None
    organization_id: UUID
    organization_name: str | None = None
    organization_slug: str | None = None
    team_ids: list[UUID] = Field(default_factory=list)

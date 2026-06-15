"""Auth API schemas aligned with OpenAPI."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Role = Literal[
    "super_admin",
    "team_admin",
    "finance_viewer",
    "team_member",
    "auditor",
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    display_name: str | None = None
    role: Role
    organization_id: str
    team_ids: list[str] = Field(default_factory=list)

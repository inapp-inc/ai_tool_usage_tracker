"""Pydantic schemas for Credentials API (tool-backed)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

CredentialEnvironment = Literal["production", "sandbox"]


class CredentialResponse(BaseModel):
    id: UUID
    label: str
    description: str
    tool_id: UUID
    tool_name: str
    team_id: UUID | None = None
    team_name: str | None = None
    environment: CredentialEnvironment
    masked_secret: str
    status: Literal["active", "inactive"]
    rotation_reminder_days: int | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime
    created_by_name: str | None = None


class CredentialCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    tool_id: UUID
    team_id: UUID
    environment: CredentialEnvironment = "production"
    secret_value: str = Field(min_length=1, max_length=4096)
    rotation_reminder_days: int | None = Field(default=None, gt=0)
    expires_at: datetime | None = None


class CredentialUpdateRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    team_id: UUID | None = None
    environment: CredentialEnvironment | None = None
    secret_value: str | None = Field(default=None, min_length=1, max_length=4096)
    rotation_reminder_days: int | None = Field(default=None, gt=0)
    expires_at: datetime | None = None
    active: bool | None = None


class CredentialCreateResponseBody(BaseModel):
    credential: CredentialResponse
    plain_secret: str


class PaginationMeta(BaseModel):
    limit: int | None = None
    next_cursor: str | None = None
    has_more: bool = False


class CredentialListResponse(BaseModel):
    data: list[CredentialResponse]
    meta: PaginationMeta


class CredentialSecretResponse(BaseModel):
    secret_value: str


class CredentialValidateRequest(BaseModel):
    tool_id: UUID
    secret_value: str = Field(min_length=1, max_length=4096)


class CredentialValidateResponse(BaseModel):
    valid: bool
    provider: str
    message: str | None = None

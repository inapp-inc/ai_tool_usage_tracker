"""Pydantic schemas for Credentials API (live provider connections)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CredentialResponse(BaseModel):
    id: UUID
    label: str
    description: str
    vendor: str
    catalogue_tool_id: UUID | None = None
    catalogue_tool_name: str | None = None
    tool_id: UUID
    tool_name: str
    team_id: UUID | None = None
    team_name: str | None = None
    api_endpoint: str | None = None
    masked_secret: str
    status: Literal["active", "inactive"]
    pull_interval_minutes: int = 60
    rotation_reminder_days: int | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime
    created_by_name: str | None = None


class CredentialCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    tool_id: UUID = Field(description="Catalogue tool id from the Tools page.")
    team_id: UUID
    secret_value: str = Field(min_length=1, max_length=4096)
    pull_interval_minutes: int = Field(default=60, ge=5, le=1440)
    rotation_reminder_days: int | None = Field(default=None, gt=0)
    expires_at: datetime | None = None


class CredentialUpdateRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    team_id: UUID | None = None
    secret_value: str | None = Field(default=None, min_length=1, max_length=4096)
    pull_interval_minutes: int | None = Field(default=None, ge=5, le=1440)
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
    model_config = ConfigDict(extra="ignore")

    tool_id: UUID = Field(description="Catalogue tool id from the Tools page.")
    secret_value: str = Field(min_length=1, max_length=4096)


class CredentialValidateResponse(BaseModel):
    valid: bool
    provider: str
    message: str | None = None

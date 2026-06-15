"""Pydantic schemas for credentials API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CredentialEnvironment = Literal["sandbox", "production"]


class CredentialCreateRequest(BaseModel):
    tool_id: UUID
    team_id: UUID | None = None
    environment: CredentialEnvironment
    secret_value: str = Field(min_length=1, max_length=4096)
    label: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=500)
    rotation_reminder_days: int | None = None
    expires_at: datetime | None = None

    @field_validator("team_id", mode="before")
    @classmethod
    def empty_team_id_to_none(cls, value: object) -> object:
        if value == "" or value is None:
            return None
        return value


class CredentialUpdateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    team_id: UUID | None = None
    environment: CredentialEnvironment | None = None
    rotation_reminder_days: int | None = None
    expires_at: datetime | None = None
    status: Literal["active", "inactive"] | None = None


class CredentialRotateRequest(BaseModel):
    secret_value: str = Field(min_length=1, max_length=4096)


class CredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tool_id: UUID
    team_id: UUID | None
    environment: CredentialEnvironment
    masked_secret: str
    label: str = ""
    description: str = ""
    status: Literal["active", "inactive"] = "active"
    rotation_reminder_days: int | None = None
    expires_at: datetime | None
    last_rotated_at: datetime | None
    created_at: datetime


class CredentialListResponse(BaseModel):
    data: list[CredentialResponse]
    meta: dict

"""Pydantic schemas for provider registry API."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


class ProviderCreateRequest(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=100)
    usage_api_url: str = Field(min_length=8, max_length=2048)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not SLUG_PATTERN.match(normalized):
            msg = (
                "Slug must start with a letter and contain only lowercase "
                "letters, numbers, and underscores"
            )
            raise ValueError(msg)
        return normalized

    @field_validator("usage_api_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed.startswith(("http://", "https://")):
            raise ValueError("Usage API URL must start with http:// or https://")
        return trimmed


class ProviderUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    usage_api_url: str | None = Field(default=None, min_length=8, max_length=2048)
    description: str | None = Field(default=None, max_length=500)
    active: bool | None = None

    @field_validator("usage_api_url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        trimmed = value.strip()
        if not trimmed.startswith(("http://", "https://")):
            raise ValueError("Usage API URL must start with http:// or https://")
        return trimmed


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    slug: str
    name: str
    usage_api_url: str
    description: str | None = None
    is_system: bool
    active: bool
    created_at: datetime
    updated_at: datetime


class PaginationMeta(BaseModel):
    limit: int
    next_cursor: str | None = None
    has_more: bool = False


class ProviderListResponse(BaseModel):
    data: list[ProviderResponse]
    meta: PaginationMeta


class ValidateProviderRequest(BaseModel):
    provider_slug: str = Field(min_length=1, max_length=64)
    api_token: str = Field(min_length=1)


class ValidateProviderResponse(BaseModel):
    valid: bool
    message: str
    status_code: int | None = None

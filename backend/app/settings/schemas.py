"""Pydantic schemas for Settings API."""

import re

from pydantic import BaseModel, Field, field_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9_]+$")


class ProviderResponse(BaseModel):
    slug: str
    label: str
    description: str | None = None
    logo_url: str | None = None
    parent_slug: str | None = None
    parent_label: str | None = None
    adapter_key: str | None = None
    requires_api_endpoint: bool = False
    built_in: bool
    active: bool
    sort_order: int


class ProviderListResponse(BaseModel):
    data: list[ProviderResponse]


class ProviderParentResponse(BaseModel):
    slug: str
    label: str
    sort_order: int


class ProviderParentListResponse(BaseModel):
    data: list[ProviderParentResponse]


class ProviderCreateRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    logo_url: str | None = Field(default=None, max_length=512)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        slug = value.strip().lower().replace(" ", "_").replace("-", "_")
        if not SLUG_PATTERN.match(slug):
            msg = "slug must contain only lowercase letters, numbers, and underscores."
            raise ValueError(msg)
        return slug


class ProviderUpdateRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    logo_url: str | None = Field(default=None, max_length=512)
    active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)

"""Pydantic schemas for teams API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    settings: dict = Field(default_factory=dict)


class TeamUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    active: bool | None = None
    settings: dict | None = None


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    active: bool
    member_count: int = 0
    settings: dict = Field(default_factory=dict)
    created_at: datetime


class PaginationMeta(BaseModel):
    limit: int
    next_cursor: str | None = None
    has_more: bool = False


class TeamListResponse(BaseModel):
    data: list[TeamResponse]
    meta: PaginationMeta

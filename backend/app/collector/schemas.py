"""Pydantic schemas for collector API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CollectorProvider = Literal[
    "openai",
    "anthropic",
    "google",
    "azure_openai",
    "cohere",
    "mistral",
    "custom",
    "mabl",
    "windsurf",
    "cursor",
]
CollectorRunStatus = Literal["queued", "running", "completed", "failed"]
RunTrigger = Literal["scheduled", "manual"]


class CollectorCreateRequest(BaseModel):
    """Connect a provider and set pull interval from the frontend."""

    name: str = Field(min_length=1, max_length=100)
    provider: CollectorProvider
    api_token: str = Field(min_length=1, max_length=4096)
    pull_interval_minutes: int = Field(default=60, ge=5, le=1440)
    active: bool = True
    pricing_config: dict = Field(default_factory=dict)


class CollectorUpdateRequest(BaseModel):
    """Update collector schedule or credentials."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    api_token: str | None = Field(default=None, min_length=1, max_length=4096)
    pull_interval_minutes: int | None = Field(default=None, ge=5, le=1440)
    active: bool | None = None
    pricing_config: dict | None = None


class CollectorResponse(BaseModel):
    """Collector config returned to the frontend (no plaintext token)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    provider: str
    api_token_masked: str
    pull_interval_minutes: int
    active: bool
    last_run_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class CollectorListResponse(BaseModel):
    data: list[CollectorResponse]


class CollectorRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collector_id: UUID
    status: str
    records_ingested: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class CollectorRunListResponse(BaseModel):
    data: list[CollectorRunResponse]


class UsageEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collector_id: UUID | None
    provider: str
    model: str | None
    occurred_at: datetime
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: Decimal
    vendor_event_id: str | None
    created_at: datetime


class UsageEventListResponse(BaseModel):
    data: list[UsageEventResponse]


class UsageSummaryResponse(BaseModel):
    total_tokens: int
    total_cost: Decimal
    event_count: int
    period_from: datetime | None = None
    period_to: datetime | None = None

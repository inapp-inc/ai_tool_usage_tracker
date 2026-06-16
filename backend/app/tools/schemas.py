"""Pydantic schemas for Tools API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.tools.pricing import validate_vendor

PricingModel = Literal["flat_token", "package_with_overage", "custom"]
SyncStatus = Literal["active", "inactive", "error"]


class ToolCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    vendor: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    pricing_model: PricingModel
    token_price: Decimal = Field(ge=0)
    package_allowance: int | None = Field(default=None, ge=0)
    overage_price: Decimal | None = Field(default=None, ge=0)
    pricing_config: dict = Field(default_factory=dict)
    api_key: str = Field(min_length=1, max_length=4096)

    @field_validator("vendor")
    @classmethod
    def normalize_vendor(cls, value: str) -> str:
        return validate_vendor(value)


class ToolUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    vendor: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    pricing_model: PricingModel | None = None
    token_price: Decimal | None = Field(default=None, ge=0)
    package_allowance: int | None = Field(default=None, ge=0)
    overage_price: Decimal | None = Field(default=None, ge=0)
    pricing_config: dict | None = None
    active: bool | None = None
    api_key: str | None = Field(default=None, min_length=1, max_length=4096)

    @field_validator("vendor")
    @classmethod
    def normalize_vendor(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_vendor(value)


class ToolMemberResponse(BaseModel):
    email: str
    name: str | None = None


class ToolMembersListResponse(BaseModel):
    data: list[ToolMemberResponse]
    member_count: int


class ToolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    vendor: str
    description: str | None = None
    pricing_model: str
    token_price: Decimal
    package_allowance: int | None = None
    overage_price: Decimal | None = None
    pricing_config: dict = Field(default_factory=dict)
    active: bool
    api_token_masked: str
    token_count: int
    cost_total: Decimal
    balance_tokens: int | None = None
    member_count: int = 0
    sync_status: SyncStatus
    last_sync_at: datetime | None = None
    last_sync_error: str | None = None
    created_at: datetime
    updated_at: datetime


class PaginationMeta(BaseModel):
    limit: int | None = None
    next_cursor: str | None = None
    has_more: bool = False


class ToolListResponse(BaseModel):
    data: list[ToolResponse]
    meta: PaginationMeta

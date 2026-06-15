"""Pydantic schemas for tools API."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

PricingModel = Literal["flat_token", "package_with_overage", "custom"]


class ToolCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    vendor: str = Field(min_length=1, max_length=100)
    pricing_model: PricingModel
    token_price: Decimal = Field(ge=0)
    package_allowance: int | None = Field(default=None, ge=0)
    overage_price: Decimal | None = Field(default=None, ge=0)
    pricing_config: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_package_pricing(self) -> "ToolCreateRequest":
        if self.pricing_model == "package_with_overage":
            if self.package_allowance is None or self.overage_price is None:
                msg = (
                    "package_allowance and overage_price are required when "
                    "pricing_model is package_with_overage"
                )
                raise ValueError(msg)
        return self


class ToolUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    vendor: str | None = Field(default=None, max_length=100)
    pricing_model: PricingModel | None = None
    token_price: Decimal | None = Field(default=None, ge=0)
    package_allowance: int | None = Field(default=None, ge=0)
    overage_price: Decimal | None = Field(default=None, ge=0)
    active: bool | None = None
    pricing_config: dict | None = None


class ToolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    vendor: str
    pricing_model: PricingModel
    token_price: Decimal
    package_allowance: int | None
    overage_price: Decimal | None
    active: bool
    pricing_config: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime | None = None


class PaginationMeta(BaseModel):
    limit: int
    next_cursor: str | None = None
    has_more: bool = False


class ToolListResponse(BaseModel):
    data: list[ToolResponse]
    meta: PaginationMeta


class ToolSyncResponse(BaseModel):
    valid: bool
    message: str
    tool: ToolResponse


class ToolCsvDailyUsageRow(BaseModel):
    date: str
    tokens: int
    cost: float


class ToolCsvColumnMapping(BaseModel):
    token_column: str | None = None
    cost_column: str | None = None
    date_column: str | None = None
    date_from_column: str | None = None
    date_to_column: str | None = None


class ToolCsvInspectResponse(BaseModel):
    headers: list[str]
    row_count: int
    format_hint: str
    suggested_mapping: ToolCsvColumnMapping


class ToolCsvImportPreview(BaseModel):
    file_name: str
    row_count: int
    token_count: int
    cost_total: float
    date_from: str | None = None
    date_to: str | None = None
    daily_usage: list[ToolCsvDailyUsageRow] = Field(default_factory=list)


class ToolCsvImportResponse(BaseModel):
    message: str
    tool: ToolResponse
    preview: ToolCsvImportPreview

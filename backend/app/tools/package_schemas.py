"""Pydantic schemas for tool packages."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.tools.schemas import PaginationMeta


class ToolPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tool_id: UUID
    package_name: str
    billing_type: str
    monthly_price: Decimal | None = None
    yearly_price: Decimal | None = None
    seat_limit: int | None = None
    token_limit: int | None = None
    request_limit: int | None = None
    credit_limit: Decimal | None = None
    currency: str
    is_active: bool


class ToolPackageListResponse(BaseModel):
    data: list[ToolPackageResponse]
    meta: PaginationMeta

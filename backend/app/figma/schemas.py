"""Pydantic schemas for Figma billing analytics API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class FigmaBillingPeriodOption(BaseModel):
    import_id: str
    usage_period_start: date | None = None
    usage_period_end: date | None = None
    upload_filename: str | None = None


class FigmaInsight(BaseModel):
    severity: str
    title: str
    message: str


class FigmaBillingCostTrendPoint(BaseModel):
    label: str
    iso_date: str
    """Cumulative cost through this date (matches period total on last day)."""
    cost: Decimal
    daily_cost: Decimal = Decimal("0")
    usage_period_start: date | None = None
    usage_period_end: date | None = None


class FigmaBillingPeriodRow(BaseModel):
    usage_period_start: date | None = None
    usage_period_end: date | None = None
    paid_credits_used: Decimal = Decimal("0")
    seat_cost: Decimal = Decimal("0")
    paid_cost: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    full_seat_count: int = 0
    view_seat_count: int = 0
    user_count: int = 0
    upload_filename: str | None = None
    imported_at: datetime | None = None


class FigmaBillingTopUser(BaseModel):
    user_email: str | None = None
    user_name: str | None = None
    figma_user_id: str | None = None
    seat_type: str | None = None
    seat_credits_used: Decimal = Decimal("0")
    paid_credits_used: Decimal = Decimal("0")
    seat_cost_usd: Decimal = Decimal("0")
    paid_cost_usd: Decimal = Decimal("0")
    total_cost_usd: Decimal = Decimal("0")
    percent_of_total: float = 0.0


class FigmaBillingPeriodUser(BaseModel):
    user_email: str | None = None
    user_name: str | None = None
    figma_user_id: str | None = None
    seat_type: str | None = None
    seat_credits_used: Decimal = Decimal("0")
    paid_credits_used: Decimal = Decimal("0")
    seat_cost_usd: Decimal = Decimal("0")
    paid_cost_usd: Decimal = Decimal("0")
    total_cost_usd: Decimal = Decimal("0")


class FigmaBillingPeriodUsersResponse(BaseModel):
    usage_period_start: date | None = None
    usage_period_end: date | None = None
    total_cost: Decimal = Decimal("0")
    total_paid_cost: Decimal = Decimal("0")
    total_seat_cost: Decimal = Decimal("0")
    users: list[FigmaBillingPeriodUser] = Field(default_factory=list)


class FigmaBillingCreditTotals(BaseModel):
    total_seat_credits_used: Decimal = Decimal("0")
    total_paid_credits_used: Decimal = Decimal("0")


class FigmaBillingInsightsResponse(BaseModel):
    team_id: str
    tool_id: str
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    has_import: bool = False
    has_config: bool = False
    imports_outside_filter: bool = False
    full_seat_cost_usd: Decimal | None = None
    view_seat_cost_usd: Decimal | None = None
    credits_per_usd: Decimal | None = None
    configured_seat_cost: Decimal | None = None
    seat_cost: Decimal | None = None
    paid_cost: Decimal | None = None
    total_cost: Decimal | None = None
    monthly_budget: Decimal | None = None
    alert_threshold_usd: Decimal | None = None
    budget_remaining: Decimal | None = None
    budget_alert_triggered: bool = False
    full_seat_count: int | None = None
    view_seat_count: int | None = None
    user_count: int | None = None
    credits: FigmaBillingCreditTotals = Field(default_factory=FigmaBillingCreditTotals)
    available_periods: list[FigmaBillingPeriodOption] = Field(default_factory=list)
    active_billing_period_start: date | None = None
    active_billing_period_end: date | None = None
    periods: list[FigmaBillingPeriodRow] = Field(default_factory=list)
    cost_trend: list[FigmaBillingCostTrendPoint] = Field(default_factory=list)
    top_users: list[FigmaBillingTopUser] = Field(default_factory=list)
    insights: list[FigmaInsight] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

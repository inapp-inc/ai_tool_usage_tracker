"""Pydantic schemas for Copilot productivity analytics API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CopilotMetricCard(BaseModel):
    label: str
    value: str | int | float
    unit: str | None = None


class CopilotChartPoint(BaseModel):
    label: str
    value: float


class CopilotOverviewResponse(BaseModel):
    team_id: str
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    total_seats: int
    assigned_seats: int
    active_users: int
    inactive_users: int
    monthly_cost: Decimal
    seat_utilization_pct: float
    average_acceptance_rate: float | None
    monthly_cost_limit: Decimal | None = None
    additional_cost: Decimal | None = None
    budget_remaining: Decimal | None = None
    alert_threshold_usd: Decimal | None = None
    budget_alert_triggered: bool = False
    data_source: str = "config"
    seat_utilization: list[CopilotChartPoint]
    active_users_trend: list[CopilotChartPoint]
    suggestions_vs_acceptances: list[CopilotChartPoint]
    top_languages: list[CopilotChartPoint]
    ide_distribution: list[CopilotChartPoint]

    model_config = {"populate_by_name": True}


class CopilotUserSummary(BaseModel):
    user_login: str
    user_email: str | None
    active_days: int
    chat_turns: int
    suggestions_count: int
    acceptances_count: int
    acceptance_rate: float | None
    estimated_cost: Decimal
    last_activity_at: str | None = None


class CopilotUserListResponse(BaseModel):
    team_id: str
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    users: list[CopilotUserSummary]

    model_config = {"populate_by_name": True}


class CopilotUserDetailResponse(CopilotUserSummary):
    team_id: str
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    daily_usage: list[CopilotChartPoint]
    language_distribution: list[CopilotChartPoint]
    ide_usage: list[CopilotChartPoint]

    model_config = {"populate_by_name": True}


class CopilotInsight(BaseModel):
    kind: str
    title: str
    message: str
    severity: str = "info"


class CopilotInsightsResponse(BaseModel):
    team_id: str
    insights: list[CopilotInsight]


class CopilotBillingPeriodRow(BaseModel):
    billing_period_start: date | None
    billing_period_end: date | None
    sku: str
    monthly_cost_limit: Decimal
    additional_cost: Decimal
    credits_cost: Decimal = Decimal("0")
    total_cost: Decimal
    seat_count: int | None = None
    upload_filename: str | None = None
    imported_at: datetime | None = None


class CopilotBillingCostTrendPoint(BaseModel):
    label: str
    iso_date: str
    cost: Decimal
    billing_period_start: date | None = None
    billing_period_end: date | None = None


class CopilotBillingTopUser(BaseModel):
    user_login: str
    user_id: str | None = None
    display_name: str | None = None
    cost: Decimal
    net_cost: Decimal = Decimal("0")
    quantity: int = 0


class CopilotBillingPeriodUser(BaseModel):
    user_id: str
    user_login: str
    display_name: str | None = None
    gross_cost: Decimal
    net_cost: Decimal = Decimal("0")
    quantity: int = 0


class CopilotBillingPeriodUsersResponse(BaseModel):
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    total_gross: Decimal = Decimal("0")
    total_net: Decimal = Decimal("0")
    users: list[CopilotBillingPeriodUser] = Field(default_factory=list)


class CopilotBillingSkuBreakdown(BaseModel):
    sku: str
    label: str
    cost: Decimal


class CopilotBillingQuantityTotals(BaseModel):
    total_quantity: int = 0
    ai_credits_quantity: int = 0
    user_months_quantity: int = 0


class CopilotBillingInsightsResponse(BaseModel):
    team_id: str
    tool_id: str
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    has_import: bool = False
    has_config: bool = False
    pricing_model: str | None = None
    cost_per_seat: Decimal | None = None
    team_size: int | None = None
    configured_monthly_cost: Decimal | None = None
    imports_outside_filter: bool = False
    monthly_cost_limit: Decimal | None = None
    additional_cost: Decimal | None = None
    credits_cost: Decimal | None = None
    total_cost: Decimal | None = None
    monthly_budget: Decimal | None = None
    alert_threshold_usd: Decimal | None = None
    budget_remaining: Decimal | None = None
    budget_alert_triggered: bool = False
    seat_count: int | None = None
    quantities: CopilotBillingQuantityTotals = Field(default_factory=CopilotBillingQuantityTotals)
    periods: list[CopilotBillingPeriodRow] = Field(default_factory=list)
    cost_trend: list[CopilotBillingCostTrendPoint] = Field(default_factory=list)
    top_users: list[CopilotBillingTopUser] = Field(default_factory=list)
    sku_breakdown: list[CopilotBillingSkuBreakdown] = Field(default_factory=list)
    insights: list[CopilotInsight] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class CopilotSeatReportRow(BaseModel):
    user_login: str
    user_email: str | None
    assigned_at: str | None
    last_activity_at: str | None
    seat_status: str
    monthly_cost: Decimal


class CopilotProductivityReportRow(BaseModel):
    user_login: str
    language: str
    editor: str
    suggestions_count: int
    acceptances_count: int
    acceptance_rate: float | None
    chat_turns: int


class CopilotCostReportRow(BaseModel):
    user_login: str
    package: str | None
    estimated_monthly_cost: Decimal
    activity_status: str

"""Pydantic schemas for Copilot productivity analytics API."""

from __future__ import annotations

from datetime import date
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

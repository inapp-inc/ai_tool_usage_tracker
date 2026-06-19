"""Pydantic schemas for dashboard / insights API."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TrendGranularityApi = Literal["daily", "weekly", "monthly"]


class ActiveCountsWidget(BaseModel):
    """Catalogue tool and active team counts (aligned with Tools / Teams admin lists)."""

    active_tools: int
    active_teams: int


class TokenUsageWidget(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    last_updated_at: datetime


class CostOverviewWidget(BaseModel):
    actual_spend: Decimal
    package_allowance: Decimal
    allowance_consumed_pct: float | None = None
    overage_cost: Decimal
    last_updated_at: datetime


class UsageByToolItem(BaseModel):
    tool_id: UUID
    tool_name: str
    total_tokens: int
    estimated_cost: Decimal | None = None
    share_pct: float


class UsageByTeamItem(BaseModel):
    team_id: UUID
    team_name: str
    total_tokens: int
    estimated_cost: Decimal


class UsageByTeamResponse(BaseModel):
    data: list[UsageByTeamItem]
    last_updated_at: datetime


class TopConsumerItem(BaseModel):
    entity_id: UUID
    entity_name: str
    total_tokens: int
    estimated_cost: Decimal | None = None
    team_id: UUID | None = None
    team_name: str | None = None
    user_email: str | None = None
    request_count: int | None = None


class TopConsumersResponse(BaseModel):
    teams: list[TopConsumerItem] = Field(default_factory=list)
    users: list[TopConsumerItem] = Field(default_factory=list)


class ActiveAlertSummary(BaseModel):
    alert_id: UUID
    severity: Literal["info", "warning", "critical"]
    threshold_type: str
    tool_name: str | None = None
    team_name: str | None = None
    current_value: Decimal
    limit_value: Decimal
    triggered_at: datetime
    title: str


class ActiveAlertsResponse(BaseModel):
    data: list[ActiveAlertSummary]


class TrendPoint(BaseModel):
    period_start: datetime
    total_tokens: int
    estimated_cost: Decimal | None = None


class TrendsResponse(BaseModel):
    granularity: TrendGranularityApi
    data: list[TrendPoint]


class UsageByToolResponse(BaseModel):
    data: list[UsageByToolItem]
    last_updated_at: datetime


class MyUsageResponse(BaseModel):
    total_tokens: int
    estimated_cost: Decimal
    by_tool: list[UsageByToolItem]


class DailyBreakdownUser(BaseModel):
    user_id: UUID
    user_name: str
    tokens: int
    cost: Decimal


class DailyBreakdownTeam(BaseModel):
    team_id: UUID
    team_name: str
    tokens: int
    cost: Decimal
    users: list[DailyBreakdownUser]


class DailyBreakdownResponse(BaseModel):
    data: list[DailyBreakdownTeam]

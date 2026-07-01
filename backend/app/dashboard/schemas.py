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
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    included_tokens: int | None = None
    billable_tokens: int | None = None
    breakdown_available: bool = False
    last_updated_at: datetime


class CostOverviewWidget(BaseModel):
    actual_spend: Decimal
    package_allowance: Decimal
    allowance_consumed_pct: float | None = None
    overage_cost: Decimal
    included_tokens: int | None = None
    billable_tokens: int | None = None
    included_cost: Decimal | None = None
    billable_cost: Decimal | None = None
    breakdown_available: bool = False
    last_updated_at: datetime


class OrganizationCostSummary(BaseModel):
    """Organization-wide cost rollup from team pricing totals and additional billable spend."""

    tools_cost: Decimal = Field(
        description="Sum of team tools pricing (package/subscription amounts configured per team)."
    )
    additional_billable_cost: Decimal = Field(
        description="Spend beyond team tools pricing (imports, overage, unscoped usage)."
    )
    total_cost: Decimal = Field(description="Tools cost + additional billable cost.")
    team_count: int = 0
    connected_tool_count: int = 0


class OrganizationCostBreakdownItem(BaseModel):
    organization_id: UUID
    organization_name: str
    tools_cost: Decimal
    additional_billable_cost: Decimal
    total_cost: Decimal
    connected_tool_count: int = 0


class OrganizationCostBreakdownResponse(BaseModel):
    data: list[OrganizationCostBreakdownItem]


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
    included_cost: Decimal | None = None
    billable_cost: Decimal | None = None
    breakdown_available: bool = False


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

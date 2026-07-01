/** Maps OpenAPI dashboard responses to frontend dashboard types. */

import { format, parseISO } from "date-fns";

import type {
  DashboardStats,
  OrganizationCostSummary,
  RecentAlert,
  TeamCostDataPoint,
  TokenDataPoint,
  TopUser,
} from "../dashboard";

export interface ApiTokenUsageWidget {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cache_write_tokens?: number;
  cache_read_tokens?: number;
  included_tokens?: number | null;
  billable_tokens?: number | null;
  breakdown_available?: boolean;
  last_updated_at: string;
}

export interface ApiCostOverviewWidget {
  actual_spend: number;
  package_allowance: number;
  allowance_consumed_pct?: number | null;
  overage_cost: number;
  included_tokens?: number | null;
  billable_tokens?: number | null;
  included_cost?: number | null;
  billable_cost?: number | null;
  breakdown_available?: boolean;
  last_updated_at: string;
}

export interface ApiUsageByToolItem {
  tool_id: string;
  tool_name: string;
  total_tokens: number;
  estimated_cost?: number | null;
  share_pct: number;
}

export interface ApiUsageByTeamItem {
  team_id: string;
  team_name: string;
  total_tokens: number;
  estimated_cost: number;
}

export interface ApiUsageByTeamResponse {
  data: ApiUsageByTeamItem[];
  last_updated_at: string;
}

export interface ApiTopConsumerItem {
  entity_id: string;
  entity_name: string;
  total_tokens: number;
  estimated_cost?: number | null;
  team_id?: string | null;
  team_name?: string | null;
  user_email?: string | null;
  request_count?: number | null;
}

export interface ApiTopConsumersResponse {
  teams?: ApiTopConsumerItem[];
  users?: ApiTopConsumerItem[];
}

export interface ApiActiveAlertSummary {
  alert_id: string;
  severity: "critical" | "warning" | "info";
  threshold_type: string;
  tool_name?: string | null;
  team_name?: string | null;
  current_value: number;
  limit_value: number;
  triggered_at: string;
  title: string;
}

export interface ApiActiveAlertsResponse {
  data: ApiActiveAlertSummary[];
}

export interface ApiTrendPoint {
  period_start: string;
  total_tokens: number;
  estimated_cost?: number | null;
  included_cost?: number | null;
  billable_cost?: number | null;
  breakdown_available?: boolean;
}

export interface ApiTrendsResponse {
  granularity: "daily" | "weekly" | "monthly";
  data: ApiTrendPoint[];
}

export interface ApiActiveCountsWidget {
  active_tools: number;
  active_teams: number;
}

export interface ApiOrganizationCostSummary {
  tools_cost: number | string;
  additional_billable_cost: number | string;
  total_cost: number | string;
  team_count: number;
  connected_tool_count?: number;
}

export interface ApiOrganizationCostBreakdownItem {
  organization_id: string;
  organization_name: string;
  tools_cost: number | string;
  additional_billable_cost: number | string;
  total_cost: number | string;
  connected_tool_count?: number;
}

export function mapOrganizationCostSummary(
  api: ApiOrganizationCostSummary,
): OrganizationCostSummary {
  const parse = (value: number | string) => {
    const n = typeof value === "number" ? value : Number(value);
    return Number.isNaN(n) ? 0 : n;
  };
  return {
    toolsCost: parse(api.tools_cost),
    additionalBillableCost: parse(api.additional_billable_cost),
    totalCost: parse(api.total_cost),
    teamCount: api.team_count,
    connectedToolCount: api.connected_tool_count ?? 0,
  };
}

export function mapOrganizationCostBreakdownItem(
  api: ApiOrganizationCostBreakdownItem,
): import("../dashboard").OrganizationCostBreakdownItem {
  const parse = (value: number | string) => {
    const n = typeof value === "number" ? value : Number(value);
    return Number.isNaN(n) ? 0 : n;
  };
  return {
    organizationId: api.organization_id,
    organizationName: api.organization_name,
    toolsCost: parse(api.tools_cost),
    additionalBillableCost: parse(api.additional_billable_cost),
    totalCost: parse(api.total_cost),
    connectedToolCount: api.connected_tool_count ?? 0,
  };
}

export function buildDashboardStats(
  tokens: ApiTokenUsageWidget,
  cost: ApiCostOverviewWidget,
  activeCounts: ApiActiveCountsWidget,
  deltas: {
    tokens_delta: number;
    cost_delta: number;
    tools_delta: number;
    teams_delta: number;
  },
): DashboardStats {
  const inputTokens = tokens.input_tokens ?? 0;
  const outputTokens = tokens.output_tokens ?? 0;
  const totalTokens = Math.max(
    tokens.total_tokens,
    inputTokens + outputTokens,
  );

  return {
    totalTokens,
    totalCost: Number(cost.actual_spend),
    activeTools: activeCounts.active_tools,
    activeTeams: activeCounts.active_teams,
    tokensDelta: deltas.tokens_delta,
    costDelta: deltas.cost_delta,
    toolsDelta: deltas.tools_delta,
    teamsDelta: deltas.teams_delta,
    breakdownAvailable: Boolean(tokens.breakdown_available ?? cost.breakdown_available),
    includedTokens: tokens.included_tokens ?? undefined,
    billableTokens: tokens.billable_tokens ?? undefined,
    inputTokens: inputTokens,
    outputTokens: outputTokens,
    cacheWriteTokens: tokens.cache_write_tokens ?? 0,
    cacheReadTokens: tokens.cache_read_tokens ?? 0,
    includedCost: cost.included_cost != null ? Number(cost.included_cost) : undefined,
    billableCost: cost.billable_cost != null ? Number(cost.billable_cost) : undefined,
    packageAllowance: Number(cost.package_allowance),
    allowanceConsumedPct: cost.allowance_consumed_pct ?? null,
    overageCost: Number(cost.overage_cost),
  };
}

export function mapTrendPoints(points: ApiTrendPoint[]): TokenDataPoint[] {
  return points.map((point) => ({
    date: format(parseISO(point.period_start), "MMM d"),
    isoDate: point.period_start,
    tokens: point.total_tokens,
    cost: Number(point.estimated_cost ?? 0),
  }));
}

export function mapTeamCostRows(rows: ApiUsageByTeamItem[]): TeamCostDataPoint[] {
  return rows.map((row) => ({
    team: row.team_name,
    cost: Number(row.estimated_cost),
  }));
}

export function mapTopUsers(
  users: ApiTopConsumerItem[],
  totalTokens: number,
): TopUser[] {
  return users.map((user) => ({
    id: user.entity_id,
    name: user.entity_name,
    team: user.team_name ?? "—",
    tokens: user.total_tokens,
    cost: Number(user.estimated_cost ?? 0),
    percentOfTotal: totalTokens > 0 ? user.total_tokens / totalTokens : 0,
  }));
}

export function mapRecentAlerts(alerts: ApiActiveAlertSummary[]): RecentAlert[] {
  return alerts.map((alert) => ({
    id: alert.alert_id,
    title: alert.title,
    severity: alert.severity,
    triggeredAt: alert.triggered_at,
    team: alert.team_name ?? "Organization",
  }));
}

export function dashboardQuery(
  from: string,
  to: string,
  filters?: { teamId?: string; toolId?: string },
): string {
  const params = new URLSearchParams({ from, to });
  if (filters?.teamId && filters.teamId !== "all") {
    params.set("team_id", filters.teamId);
  }
  if (filters?.toolId && filters.toolId !== "all") {
    params.set("tool_id", filters.toolId);
  }
  return params.toString();
}

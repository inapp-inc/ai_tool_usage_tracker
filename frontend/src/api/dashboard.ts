import { apiRequest } from "./client";
import {
  buildDashboardStats,
  dashboardQuery,
  mapRecentAlerts,
  mapTeamCostRows,
  mapTopUsers,
  mapTrendPoints,
  type ApiActiveAlertSummary,
  type ApiActiveCountsWidget,
  type ApiCostOverviewWidget,
  type ApiTokenUsageWidget,
  type ApiTopConsumersResponse,
  type ApiTrendPoint,
  type ApiUsageByToolItem,
  type ApiUsageByTeamItem,
} from "./adapters/dashboard";

export const ALL_TEAMS = "all";
export const ALL_TOOLS = "all";

export interface DashboardFilters {
  teamId?: string;
  toolId?: string;
}

export interface DashboardStats {
  totalTokens: number;
  totalCost: number;
  activeTools: number;
  activeTeams: number;
  tokensDelta: number;
  costDelta: number;
  toolsDelta: number;
  teamsDelta: number;
  breakdownAvailable?: boolean;
  includedTokens?: number;
  billableTokens?: number;
  inputTokens?: number;
  outputTokens?: number;
  cacheWriteTokens?: number;
  cacheReadTokens?: number;
  includedCost?: number;
  billableCost?: number;
  packageAllowance?: number;
  allowanceConsumedPct?: number | null;
  overageCost?: number;
}

export interface TokenDataPoint {
  date: string;
  isoDate: string;
  tokens: number;
  cost: number;
}

export interface TeamCostDataPoint {
  team: string;
  cost: number;
}

export interface TopUser {
  id: string;
  name: string;
  team: string;
  tokens: number;
  cost: number;
  percentOfTotal: number;
}

export interface RecentAlert {
  id: string;
  title: string;
  severity: "critical" | "warning" | "info";
  triggeredAt: string;
  team: string;
}

function normalizeFilters(filters?: DashboardFilters): DashboardFilters | undefined {
  if (!filters) {
    return undefined;
  }
  return {
    teamId:
      filters.teamId && filters.teamId !== ALL_TEAMS && filters.teamId !== ""
        ? filters.teamId
        : undefined,
    toolId:
      filters.toolId && filters.toolId !== ALL_TOOLS && filters.toolId !== ""
        ? filters.toolId
        : undefined,
  };
}

async function fetchPeriodDeltas(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<{
  tokens_delta: number;
  cost_delta: number;
  tools_delta: number;
  teams_delta: number;
}> {
  const normalized = normalizeFilters(filters);
  const prevDurationMs = new Date(to).getTime() - new Date(from).getTime();
  const prevTo = new Date(new Date(from).getTime() - 1).toISOString();
  const prevFrom = new Date(new Date(from).getTime() - prevDurationMs).toISOString();

  const [currentTokens, prevTokens, currentCost, prevCost] = await Promise.all([
    apiRequest<ApiTokenUsageWidget>(`/dashboard/tokens?${dashboardQuery(from, to, normalized)}`),
    apiRequest<ApiTokenUsageWidget>(`/dashboard/tokens?${dashboardQuery(prevFrom, prevTo, normalized)}`),
    apiRequest<ApiCostOverviewWidget>(`/dashboard/cost?${dashboardQuery(from, to, normalized)}`),
    apiRequest<ApiCostOverviewWidget>(`/dashboard/cost?${dashboardQuery(prevFrom, prevTo, normalized)}`),
  ]);

  const pct = (current: number, previous: number) =>
    previous === 0 ? (current > 0 ? 100 : 0) : ((current - previous) / previous) * 100;

  return {
    tokens_delta: Math.round(pct(currentTokens.total_tokens, prevTokens.total_tokens) * 10) / 10,
    cost_delta: Math.round(pct(Number(currentCost.actual_spend), Number(prevCost.actual_spend)) * 10) / 10,
    tools_delta: 0,
    teams_delta: 0,
  };
}

export async function fetchDashboardStats(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<DashboardStats> {
  const normalized = normalizeFilters(filters);
  const query = dashboardQuery(from, to, normalized);
  const countsQuery = normalized?.teamId
    ? `team_id=${encodeURIComponent(normalized.teamId)}`
    : "";
  const [tokens, cost, activeCounts, deltas] = await Promise.all([
    apiRequest<ApiTokenUsageWidget>(`/dashboard/tokens?${query}`),
    apiRequest<ApiCostOverviewWidget>(`/dashboard/cost?${query}`),
    apiRequest<ApiActiveCountsWidget>(`/dashboard/active-counts?${countsQuery}`),
    fetchPeriodDeltas(from, to, filters),
  ]);

  return buildDashboardStats(tokens, cost, activeCounts, deltas);
}

export async function fetchTokenTimeseries(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<TokenDataPoint[]> {
  const normalized = normalizeFilters(filters);
  const query = `${dashboardQuery(from, to, normalized)}&granularity=daily`;
  const trends = await apiRequest<ApiTrendPoint[]>(`/dashboard/trends?${query}`);
  return mapTrendPoints(trends);
}

export async function fetchTeamCost(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<TeamCostDataPoint[]> {
  const normalized = normalizeFilters(filters);
  const teams = await apiRequest<ApiUsageByTeamItem[]>(
    `/dashboard/usage-by-team?${dashboardQuery(from, to, normalized)}`,
  );
  return mapTeamCostRows(teams);
}

export async function fetchTopUsers(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<TopUser[]> {
  const normalized = normalizeFilters(filters);
  const query = `${dashboardQuery(from, to, normalized)}&entity=users&limit=8`;
  const [consumers, tokens] = await Promise.all([
    apiRequest<ApiTopConsumersResponse>(`/dashboard/top-consumers?${query}`),
    apiRequest<ApiTokenUsageWidget>(`/dashboard/tokens?${dashboardQuery(from, to, normalized)}`),
  ]);
  return mapTopUsers(consumers.users ?? [], tokens.total_tokens);
}

export async function fetchRecentAlerts(filters?: DashboardFilters): Promise<RecentAlert[]> {
  const normalized = normalizeFilters(filters);
  const params = new URLSearchParams({ limit: "5" });
  if (normalized?.teamId) {
    params.set("team_id", normalized.teamId);
  }
  const alerts = await apiRequest<ApiActiveAlertSummary[]>(`/dashboard/alerts?${params.toString()}`);
  return mapRecentAlerts(alerts);
}

export const dashboardApi = {
  fetchDashboardStats,
  fetchTokenTimeseries,
  fetchTeamCost,
  fetchTopUsers,
  fetchRecentAlerts,
};

import { differenceInCalendarDays, parseISO } from "date-fns";

import { apiRequest } from "./client";
import { fetchTeams } from "./teams";
import { ALL_TEAMS, ALL_TOOLS, type DashboardFilters } from "./dashboard";
import {
  buildUsageSummary,
  mapDailyBreakdownTeams,
  mapDailyUsagePoints,
  mapUserUsageRows,
  mergeTeamUsageRows,
  usageQuery,
  type ApiCostOverviewWidget,
  type ApiDailyBreakdownTeam,
  type ApiTokenUsageWidget,
  type ApiTopConsumersResponse,
  type ApiTrendPoint,
  type ApiUsageByTeamItem,
} from "./adapters/usage";

export { ALL_TEAMS, ALL_TOOLS };
export type { DashboardFilters };

export interface UsageSummary {
  totalTokens: number;
  totalCost: number;
  avgCostPerToken: number;
  periodDays: number;
}

export interface TeamUsageRow {
  teamId: string;
  teamName: string;
  tokens: number;
  cost: number;
  percentOfTotal: number;
  memberCount: number;
  tokenBudget: number | null;
  costBudget: number | null;
  budgetUtilization: number | null;
  trend: number;
}

export interface DailyUsagePoint {
  date: string;
  isoDate: string;
  tokens: number;
  cost: number;
}

export interface UserUsageRow {
  userId: string;
  userName: string;
  userEmail: string;
  teamId: string;
  teamName: string;
  tokens: number;
  cost: number;
  percentOfTeamTotal: number;
  requestCount: number;
  avgTokensPerRequest: number;
}

export interface DailyBreakdownTeam {
  teamId: string;
  teamName: string;
  tokens: number;
  cost: number;
  users: {
    userId: string;
    userName: string;
    tokens: number;
    cost: number;
  }[];
}

export interface MyUsageTool {
  toolId: string;
  toolName: string;
  tokens: number;
  cost: number;
  sharePct: number;
}

export interface MyUsageData {
  totalTokens: number;
  totalCost: number;
  periodDays: number;
  tools: MyUsageTool[];
}

function myUsagePeriodDays(from: string, to: string): number {
  return Math.max(1, differenceInCalendarDays(parseISO(to), parseISO(from)) + 1);
}

export async function fetchMyUsage(from: string, to: string): Promise<MyUsageData> {
  const params = new URLSearchParams({ from, to });
  const raw = await apiRequest<{
    total_tokens: number;
    estimated_cost: number;
    by_tool: Array<{
      tool_id: string;
      tool_name: string;
      total_tokens: number;
      estimated_cost: number | null;
      share_pct: number;
    }>;
  }>(`/dashboard/my-usage?${params.toString()}`);

  return {
    totalTokens: raw.total_tokens,
    totalCost: Number(raw.estimated_cost),
    periodDays: myUsagePeriodDays(from, to),
    tools: raw.by_tool.map((tool) => ({
      toolId: tool.tool_id,
      toolName: tool.tool_name,
      tokens: tool.total_tokens,
      cost: Number(tool.estimated_cost ?? 0),
      sharePct: tool.share_pct,
    })),
  };
}

function normalizeFilters(filters?: DashboardFilters): DashboardFilters | undefined {
  if (!filters) {
    return undefined;
  }
  return {
    teamId: filters.teamId && filters.teamId !== ALL_TEAMS ? filters.teamId : undefined,
    toolId: filters.toolId && filters.toolId !== ALL_TOOLS ? filters.toolId : undefined,
  };
}

async function fetchTeamTrends(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<Record<string, number>> {
  const normalized = normalizeFilters(filters);
  const prevDurationMs = new Date(to).getTime() - new Date(from).getTime();
  const prevTo = new Date(new Date(from).getTime() - 1).toISOString();
  const prevFrom = new Date(new Date(from).getTime() - prevDurationMs).toISOString();

  const [current, previous] = await Promise.all([
    apiRequest<ApiUsageByTeamItem[]>(`/dashboard/usage-by-team?${usageQuery(from, to, undefined, normalized)}`),
    apiRequest<ApiUsageByTeamItem[]>(`/dashboard/usage-by-team?${usageQuery(prevFrom, prevTo, undefined, normalized)}`),
  ]);

  const previousMap = new Map(
    previous.map((row) => [row.team_id, row.total_tokens]),
  );

  const pct = (value: number, prior: number) =>
    prior === 0 ? (value > 0 ? 100 : 0) : ((value - prior) / prior) * 100;

  const trends: Record<string, number> = {};
  for (const row of current) {
    const prior = previousMap.get(row.team_id) ?? 0;
    trends[row.team_id] = Math.round(pct(row.total_tokens, prior) * 10) / 10;
  }
  return trends;
}

export async function fetchUsageSummary(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<UsageSummary> {
  const normalized = normalizeFilters(filters);
  const query = usageQuery(from, to, undefined, normalized);
  const [tokens, cost] = await Promise.all([
    apiRequest<ApiTokenUsageWidget>(`/dashboard/tokens?${query}`),
    apiRequest<ApiCostOverviewWidget>(`/dashboard/cost?${query}`),
  ]);
  return buildUsageSummary(tokens, cost, from, to);
}

export async function fetchTeamUsage(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<TeamUsageRow[]> {
  const normalized = normalizeFilters(filters);
  const query = usageQuery(from, to, undefined, normalized);
  const [usage, teams, trends] = await Promise.all([
    apiRequest<ApiUsageByTeamItem[]>(`/dashboard/usage-by-team?${query}`),
    fetchTeams(),
    fetchTeamTrends(from, to, filters),
  ]);
  return mergeTeamUsageRows(usage, teams, trends);
}

export async function fetchDailyUsage(
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<DailyUsagePoint[]> {
  const normalized = normalizeFilters(filters);
  const query = usageQuery(from, to, { granularity: "daily" }, normalized);
  const trends = await apiRequest<ApiTrendPoint[]>(`/dashboard/trends?${query}`);
  return mapDailyUsagePoints(trends);
}

async function fetchTeamUserConsumers(
  teamId: string,
  from: string,
  to: string,
  toolId: string | null,
  filters?: DashboardFilters,
): Promise<ApiTopConsumersResponse> {
  const normalized = normalizeFilters(filters);
  const extra: Record<string, string> = {
    entity: "users",
    team_id: teamId,
    limit: "50",
  };
  if (toolId) {
    extra.tool_id = toolId;
  }
  return apiRequest<ApiTopConsumersResponse>(
    `/dashboard/top-consumers?${usageQuery(from, to, extra, normalized)}`,
  );
}

export async function fetchUserUsage(
  teamId: string,
  from: string,
  to: string,
  filters?: DashboardFilters,
): Promise<UserUsageRow[]> {
  const [consumers, teams] = await Promise.all([
    fetchTeamUserConsumers(teamId, from, to, null, filters),
    fetchTeams(),
  ]);
  const teamName = teams.find((team) => team.id === teamId)?.name ?? "Team";
  return mapUserUsageRows(consumers.users ?? [], teamId, teamName);
}

export async function fetchTeamDrilldown(
  teamId: string,
  from: string,
  to: string,
  toolId: string | null,
  filters?: DashboardFilters,
): Promise<UserUsageRow[]> {
  const [consumers, teams] = await Promise.all([
    fetchTeamUserConsumers(teamId, from, to, toolId, filters),
    fetchTeams(),
  ]);
  const teamName = teams.find((team) => team.id === teamId)?.name ?? "Team";
  return mapUserUsageRows(consumers.users ?? [], teamId, teamName);
}

export async function fetchToolOptions(): Promise<{ id: string; name: string }[]> {
  const rows = await apiRequest<Array<{ id: string; name: string }>>("/tools?active=true");
  return rows.map((row) => ({ id: row.id, name: row.name }));
}

export async function fetchDailyBreakdown(
  dateIso: string,
  teamId: string | null,
  toolId: string | null,
  filters?: DashboardFilters,
): Promise<DailyBreakdownTeam[]> {
  const normalized = normalizeFilters(filters);
  const dateParam = dateIso.includes("T") ? dateIso : `${dateIso}T00:00:00.000Z`;
  const params = new URLSearchParams({ date: dateParam });
  if (teamId && teamId !== ALL_TEAMS) {
    params.set("team_id", teamId);
  } else if (normalized?.teamId) {
    params.set("team_id", normalized.teamId);
  }
  const effectiveToolId = toolId && toolId !== ALL_TOOLS ? toolId : normalized?.toolId;
  if (effectiveToolId) {
    params.set("tool_id", effectiveToolId);
  }
  const response = await apiRequest<ApiDailyBreakdownTeam[]>(
    `/dashboard/daily-breakdown?${params.toString()}`,
  );
  return mapDailyBreakdownTeams(response);
}

export const usageApi = {
  fetchUsageSummary,
  fetchTeamUsage,
  fetchDailyUsage,
  fetchUserUsage,
  fetchTeamDrilldown,
  fetchToolOptions,
  fetchDailyBreakdown,
  fetchMyUsage,
};

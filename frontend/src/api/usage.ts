import { differenceInCalendarDays, format, parseISO } from "date-fns";

import { apiRequest } from "./client";
import { fetchTools } from "./tools";

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

function periodDays(from: string, to: string): number {
  return Math.max(
    1,
    differenceInCalendarDays(parseISO(to), parseISO(from)) + 1,
  );
}

export async function fetchUsageSummary(
  from: string,
  to: string,
): Promise<UsageSummary> {
  const raw = await apiRequest<{
    total_tokens: number;
    total_cost: number;
  }>(`/dashboard/summary?${new URLSearchParams({ from, to })}`);
  const totalTokens = raw.total_tokens;
  const totalCost = raw.total_cost;
  return {
    totalTokens,
    totalCost,
    avgCostPerToken: totalTokens > 0 ? totalCost / totalTokens : 0,
    periodDays: periodDays(from, to),
  };
}

export async function fetchTeamUsage(
  from: string,
  to: string,
  toolId?: string | null,
): Promise<TeamUsageRow[]> {
  const params = new URLSearchParams({ from, to });
  if (toolId) {
    params.set("tool_id", toolId);
  }

  const [usageRows, tools] = await Promise.all([
    apiRequest<
      Array<{
        team_id: string;
        team_name: string;
        total_tokens: number;
        estimated_cost: number;
      }>
    >(`/dashboard/usage-by-team?${params}`),
    fetchTools(),
  ]);

  const toolMap = new Map(tools.map((tool) => [tool.id, tool]));
  const totalTokens = usageRows.reduce((sum, row) => sum + row.total_tokens, 0);

  return usageRows.map((row) => {
    const tool = toolMap.get(row.team_id);
    const tokenBudget = tool?.pricing.includedTokens ?? null;
    const tokens = row.total_tokens;
    return {
      teamId: row.team_id,
      teamName: row.team_name,
      tokens,
      cost: Number(row.estimated_cost ?? 0),
      percentOfTotal: totalTokens > 0 ? tokens / totalTokens : 0,
      memberCount: 0,
      tokenBudget,
      costBudget: tool?.pricing.flatMonthlyCost ?? null,
      budgetUtilization:
        tokenBudget == null ? null : Math.min((tokens / tokenBudget) * 100, 100),
      trend: 0,
    };
  });
}

export async function fetchDailyUsage(
  from: string,
  to: string,
): Promise<DailyUsagePoint[]> {
  const rows = await apiRequest<
    Array<{
      period_start: string;
      total_tokens: number;
      estimated_cost?: number;
    }>
  >(
    `/dashboard/trends?${new URLSearchParams({
      from,
      to,
      granularity: "daily",
    })}`,
  );
  return rows.map((point) => ({
    date: format(parseISO(point.period_start), "MMM d"),
    tokens: point.total_tokens,
    cost: Number(point.estimated_cost ?? 0),
  }));
}

export async function fetchUserUsage(
  teamId: string,
  from: string,
  to: string,
): Promise<UserUsageRow[]> {
  void teamId;
  void from;
  void to;
  return [];
}

export async function fetchTeamDrilldown(
  teamId: string,
  from: string,
  to: string,
  toolId: string | null,
): Promise<UserUsageRow[]> {
  void toolId;
  return fetchUserUsage(teamId, from, to);
}

export async function fetchToolOptions(): Promise<{ id: string; name: string }[]> {
  const tools = await fetchTools();
  return tools.map((tool) => ({ id: tool.id, name: tool.name }));
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

export async function fetchDailyBreakdown(
  date: string,
  teamId: string | null,
  toolId: string | null,
): Promise<DailyBreakdownTeam[]> {
  void date;
  void teamId;
  void toolId;
  return [];
}

export interface MyUsageTeam {
  team_id: string;
  team_name: string;
  total_tokens: number;
  estimated_cost: number;
}

export interface MyUsageResponse {
  user_id: string;
  email: string;
  display_name: string | null;
  role: string;
  period: { from: string; to: string };
  teams: MyUsageTeam[];
}

export async function fetchMyUsage(
  from: string,
  to: string,
): Promise<MyUsageResponse> {
  return apiRequest<MyUsageResponse>(
    `/usage/me?${new URLSearchParams({ from, to })}`,
  );
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

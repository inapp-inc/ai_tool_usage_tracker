/** Maps OpenAPI dashboard / usage responses to frontend usage types. */

import { differenceInCalendarDays, format, parseISO } from "date-fns";

import type { Team } from "../teams";
import type {
  DailyBreakdownTeam,
  DailyUsagePoint,
  TeamUsageRow,
  UsageSummary,
  UserUsageRow,
} from "../usage";
import type {
  ApiTopConsumerItem,
  ApiTopConsumersResponse,
  ApiTrendPoint,
  ApiTrendsResponse,
  ApiUsageByTeamItem,
  ApiUsageByTeamResponse,
} from "./dashboard";

export interface ApiDailyBreakdownUser {
  user_id: string;
  user_name: string;
  tokens: number;
  cost: number;
}

export interface ApiDailyBreakdownTeam {
  team_id: string;
  team_name: string;
  tokens: number;
  cost: number;
  users: ApiDailyBreakdownUser[];
}

export interface ApiDailyBreakdownResponse {
  data: ApiDailyBreakdownTeam[];
}

export interface ApiTokenUsageWidget {
  input_tokens?: number;
  output_tokens?: number;
  total_tokens: number;
}

export interface ApiCostOverviewWidget {
  actual_spend: number;
}

function periodDays(from: string, to: string): number {
  return Math.max(
    1,
    differenceInCalendarDays(parseISO(to), parseISO(from)) + 1,
  );
}

export function buildUsageSummary(
  tokens: ApiTokenUsageWidget,
  cost: ApiCostOverviewWidget,
  from: string,
  to: string,
): UsageSummary {
  const inputTokens = tokens.input_tokens ?? 0;
  const outputTokens = tokens.output_tokens ?? 0;
  const totalTokens = Math.max(tokens.total_tokens, inputTokens + outputTokens);
  const totalCost = Number(cost.actual_spend);
  return {
    totalTokens,
    totalCost,
    avgCostPerToken: totalTokens > 0 ? totalCost / totalTokens : 0,
    periodDays: periodDays(from, to),
  };
}

export function mapDailyUsagePoints(points: ApiTrendPoint[]): DailyUsagePoint[] {
  return points.map((point) => ({
    date: format(parseISO(point.period_start), "MMM d"),
    isoDate: point.period_start,
    tokens: point.total_tokens,
    cost: Number(point.estimated_cost ?? 0),
  }));
}

export function mergeTeamUsageRows(
  usageRows: ApiUsageByTeamItem[],
  teams: Team[],
  trends: Record<string, number>,
): TeamUsageRow[] {
  const teamMap = new Map(teams.map((team) => [team.id, team]));
  const totalTokens = usageRows.reduce((sum, row) => sum + row.total_tokens, 0);

  return usageRows.map((row) => {
    const team = teamMap.get(row.team_id);
    const tokenBudget = team?.tokenBudget ?? null;
    const budgetUtilization =
      tokenBudget != null && tokenBudget > 0
        ? Math.min((row.total_tokens / tokenBudget) * 100, 100)
        : null;

    return {
      teamId: row.team_id,
      teamName: row.team_name,
      tokens: row.total_tokens,
      cost: Number(row.estimated_cost),
      percentOfTotal: totalTokens > 0 ? row.total_tokens / totalTokens : 0,
      memberCount: team?.memberCount ?? 0,
      tokenBudget,
      costBudget: team?.costBudget ?? null,
      budgetUtilization,
      trend: trends[row.team_id] ?? 0,
    };
  });
}

export function mapUserUsageRows(
  users: ApiTopConsumerItem[],
  teamId: string,
  teamName: string,
): UserUsageRow[] {
  const teamTotal = users.reduce((sum, user) => sum + user.total_tokens, 0);

  return users.map((user) => {
    const tokens = user.total_tokens;
    const requestCount = user.request_count ?? 0;
    return {
      userId: user.entity_id,
      userName: user.entity_name,
      userEmail: user.user_email ?? "",
      teamId,
      teamName,
      tokens,
      cost: Number(user.estimated_cost ?? 0),
      percentOfTeamTotal: teamTotal > 0 ? tokens / teamTotal : 0,
      requestCount,
      avgTokensPerRequest: requestCount > 0 ? Math.round(tokens / requestCount) : 0,
    };
  });
}

export function mapDailyBreakdownTeams(rows: ApiDailyBreakdownTeam[]): DailyBreakdownTeam[] {
  return rows.map((row) => ({
    teamId: row.team_id,
    teamName: row.team_name,
    tokens: row.tokens,
    cost: Number(row.cost),
    users: row.users.map((user) => ({
      userId: user.user_id,
      userName: user.user_name,
      tokens: user.tokens,
      cost: Number(user.cost),
    })),
  }));
}

export function usageQuery(
  from: string,
  to: string,
  extra?: Record<string, string>,
  filters?: { teamId?: string; toolId?: string },
): string {
  const params = new URLSearchParams({ from, to, ...extra });
  if (filters?.teamId && filters.teamId !== "all") {
    params.set("team_id", filters.teamId);
  }
  if (filters?.toolId && filters.toolId !== "all") {
    params.set("tool_id", filters.toolId);
  }
  return params.toString();
}

export type { ApiUsageByTeamItem, ApiTopConsumersResponse, ApiTrendsResponse };

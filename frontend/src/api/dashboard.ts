import { format, parseISO } from "date-fns";

import { apiRequest } from "./client";

export interface DashboardStats {
  totalTokens: number;
  totalCost: number;
  activeTools: number;
  activeTeams: number;
  tokensDelta: number;
  costDelta: number;
  toolsDelta: number;
  teamsDelta: number;
}

export interface TokenDataPoint {
  date: string;
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

function periodQuery(from: string, to: string, toolId?: string | null): string {
  const params = new URLSearchParams({ from, to });
  if (toolId) {
    params.set("tool_id", toolId);
  }
  return params.toString();
}

interface SummaryResponse {
  total_tokens: number;
  total_cost: number;
  active_tools: number;
  active_teams: number;
  tokens_delta: number;
  cost_delta: number;
  tools_delta: number;
  teams_delta: number;
}

export async function fetchDashboardStats(
  from: string,
  to: string,
): Promise<DashboardStats> {
  const raw = await apiRequest<SummaryResponse>(
    `/dashboard/summary?${periodQuery(from, to)}`,
  );
  return {
    totalTokens: raw.total_tokens,
    totalCost: raw.total_cost,
    activeTools: raw.active_tools,
    activeTeams: raw.active_teams,
    tokensDelta: raw.tokens_delta,
    costDelta: raw.cost_delta,
    toolsDelta: raw.tools_delta,
    teamsDelta: raw.teams_delta,
  };
}

export async function fetchTokenTimeseries(
  from: string,
  to: string,
): Promise<TokenDataPoint[]> {
  const rows = await apiRequest<Array<{
    period_start: string;
    total_tokens: number;
    estimated_cost?: number;
  }>>(`/dashboard/trends?${periodQuery(from, to)}&granularity=daily`);
  return rows.map((point) => ({
    date: format(parseISO(point.period_start), "MMM d"),
    tokens: point.total_tokens,
    cost: Number(point.estimated_cost ?? 0),
  }));
}

export async function fetchTeamCost(
  from: string,
  to: string,
  toolId?: string | null,
): Promise<TeamCostDataPoint[]> {
  const rows = await apiRequest<Array<{ team_name: string; estimated_cost: number }>>(
    `/dashboard/usage-by-team?${periodQuery(from, to, toolId)}`,
  );
  return rows.map((row) => ({
    team: row.team_name,
    cost: Number(row.estimated_cost ?? 0),
  }));
}

export async function fetchTopUsers(
  from: string,
  to: string,
): Promise<TopUser[]> {
  const rows = await apiRequest<Array<{
    entity_id: string;
    entity_name: string;
    total_tokens: number;
    estimated_cost?: number;
  }>>(`/dashboard/top-consumers?${periodQuery(from, to)}&limit=10`);
  const totalTokens = rows.reduce((sum, row) => sum + row.total_tokens, 0);
  return rows.map((row) => ({
    id: row.entity_id,
    name: row.entity_name,
    team: row.entity_name,
    tokens: row.total_tokens,
    cost: Number(row.estimated_cost ?? 0),
    percentOfTotal: totalTokens > 0 ? row.total_tokens / totalTokens : 0,
  }));
}

export async function fetchRecentAlerts(): Promise<RecentAlert[]> {
  const rows = await apiRequest<Array<{
    id: string;
    title: string;
    severity: RecentAlert["severity"];
    triggered_at: string;
    team_name?: string;
  }>>("/dashboard/alerts");
  return rows.map((row) => ({
    id: row.id,
    title: row.title,
    severity: row.severity,
    triggeredAt: row.triggered_at,
    team: row.team_name ?? "",
  }));
}

export const dashboardApi = {
  fetchDashboardStats,
  fetchTokenTimeseries,
  fetchTeamCost,
  fetchTopUsers,
  fetchRecentAlerts,
};

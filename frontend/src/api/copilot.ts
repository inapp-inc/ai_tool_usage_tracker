import { apiRequest } from "@/api/client";

export type CopilotChartPoint = {
  label: string;
  value: number;
};

export type CopilotOverview = {
  team_id: string;
  from_date: string;
  to_date: string;
  total_seats: number;
  assigned_seats: number;
  active_users: number;
  inactive_users: number;
  monthly_cost: string;
  seat_utilization_pct: number;
  average_acceptance_rate: number | null;
  seat_utilization: CopilotChartPoint[];
  active_users_trend: CopilotChartPoint[];
  suggestions_vs_acceptances: CopilotChartPoint[];
  top_languages: CopilotChartPoint[];
  ide_distribution: CopilotChartPoint[];
};

export type CopilotUserSummary = {
  user_login: string;
  user_email: string | null;
  active_days: number;
  chat_turns: number;
  suggestions_count: number;
  acceptances_count: number;
  acceptance_rate: number | null;
  estimated_cost: string;
  last_activity_at: string | null;
};

export type CopilotInsight = {
  kind: string;
  title: string;
  message: string;
  severity: string;
};

function copilotQuery(teamId: string, from: string, to: string): string {
  return `team_id=${encodeURIComponent(teamId)}&from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`;
}

export async function fetchCopilotOverview(
  teamId: string,
  from: string,
  to: string,
): Promise<CopilotOverview> {
  return apiRequest<CopilotOverview>(`/copilot/overview?${copilotQuery(teamId, from, to)}`);
}

export async function fetchCopilotUsers(
  teamId: string,
  from: string,
  to: string,
): Promise<{ users: CopilotUserSummary[] }> {
  return apiRequest<{ users: CopilotUserSummary[] }>(`/copilot/users?${copilotQuery(teamId, from, to)}`);
}

export async function fetchCopilotInsights(
  teamId: string,
  from: string,
  to: string,
): Promise<{ insights: CopilotInsight[] }> {
  return apiRequest<{ insights: CopilotInsight[] }>(`/copilot/insights?${copilotQuery(teamId, from, to)}`);
}

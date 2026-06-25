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
  monthly_cost_limit: string | null;
  additional_cost: string | null;
  budget_remaining: string | null;
  alert_threshold_usd: string | null;
  budget_alert_triggered: boolean;
  data_source: string;
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

export type CopilotBillingPeriod = {
  billing_period_start: string | null;
  billing_period_end: string | null;
  sku: string;
  monthly_cost_limit: string;
  additional_cost: string;
  credits_cost: string;
  total_cost: string;
  seat_count: number | null;
  upload_filename: string | null;
  imported_at: string | null;
};

export type CopilotBillingCostTrendPoint = {
  label: string;
  iso_date: string;
  cost: string;
  billing_period_start: string | null;
  billing_period_end: string | null;
};

export type CopilotBillingTopUser = {
  user_login: string;
  user_id: string | null;
  display_name: string | null;
  cost: string;
  net_cost: string;
  quantity: number;
};

export type CopilotBillingPeriodUser = {
  user_id: string;
  user_login: string;
  display_name: string | null;
  gross_cost: string;
  net_cost: string;
  quantity: number;
};

export type CopilotBillingPeriodUsers = {
  billing_period_start: string | null;
  billing_period_end: string | null;
  total_gross: string;
  total_net: string;
  users: CopilotBillingPeriodUser[];
};

export type CopilotBillingSkuBreakdown = {
  sku: string;
  label: string;
  cost: string;
};

export type CopilotBillingQuantityTotals = {
  total_quantity: number;
  ai_credits_quantity: number;
  user_months_quantity: number;
};

export type CopilotBillingInsights = {
  team_id: string;
  tool_id: string;
  from_date: string;
  to_date: string;
  has_import: boolean;
  has_config: boolean;
  pricing_model: string | null;
  imports_outside_filter: boolean;
  cost_per_seat: string | null;
  team_size: number | null;
  configured_monthly_cost: string | null;
  monthly_cost_limit: string | null;
  additional_cost: string | null;
  credits_cost: string | null;
  total_cost: string | null;
  monthly_budget: string | null;
  alert_threshold_usd: string | null;
  budget_remaining: string | null;
  budget_alert_triggered: boolean;
  seat_count: number | null;
  quantities: CopilotBillingQuantityTotals;
  periods: CopilotBillingPeriod[];
  cost_trend: CopilotBillingCostTrendPoint[];
  top_users: CopilotBillingTopUser[];
  sku_breakdown: CopilotBillingSkuBreakdown[];
  insights: CopilotInsight[];
};

export async function fetchCopilotInsights(
  teamId: string,
  from: string,
  to: string,
): Promise<{ insights: CopilotInsight[] }> {
  return apiRequest<{ insights: CopilotInsight[] }>(`/copilot/insights?${copilotQuery(teamId, from, to)}`);
}

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

export async function fetchCopilotBillingDayUsers(
  teamId: string,
  toolId: string,
  onDate: string,
): Promise<CopilotBillingPeriodUsers> {
  const params = new URLSearchParams({
    team_id: teamId,
    tool_id: toolId,
    on_date: onDate,
  });
  return apiRequest<CopilotBillingPeriodUsers>(`/copilot/billing-day-users?${params.toString()}`);
}

export async function fetchCopilotBillingPeriodUsers(
  teamId: string,
  toolId: string,
  periodStart: string | null,
  periodEnd: string | null,
): Promise<CopilotBillingPeriodUsers> {
  const params = new URLSearchParams({
    team_id: teamId,
    tool_id: toolId,
  });
  if (periodStart) {
    params.set("period_start", periodStart);
  }
  if (periodEnd) {
    params.set("period_end", periodEnd);
  }
  return apiRequest<CopilotBillingPeriodUsers>(`/copilot/billing-period-users?${params.toString()}`);
}

export async function fetchCopilotBillingInsights(
  teamId: string,
  toolId: string,
  from: string,
  to: string,
): Promise<CopilotBillingInsights> {
  return apiRequest<CopilotBillingInsights>(
    `/copilot/billing-insights?team_id=${encodeURIComponent(teamId)}&tool_id=${encodeURIComponent(toolId)}&from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
  );
}

import { apiRequest } from "./client";

export type FigmaBillingCostTrendPoint = {
  label: string;
  iso_date: string;
  cost: number | string;
  daily_cost?: number | string;
  usage_period_start?: string | null;
  usage_period_end?: string | null;
};

export type FigmaBillingPeriodRow = {
  usage_period_start: string | null;
  usage_period_end: string | null;
  seat_cost: number | string;
  paid_cost: number | string;
  total_cost: number | string;
  paid_credits_used?: number | string;
  full_seat_count: number;
  view_seat_count: number;
  user_count: number;
  upload_filename: string | null;
  imported_at: string | null;
};

export type FigmaBillingTopUser = {
  user_email: string | null;
  user_name: string | null;
  figma_user_id: string | null;
  seat_type: string | null;
  seat_credits_used: number | string;
  paid_credits_used: number | string;
  seat_cost_usd: number | string;
  paid_cost_usd: number | string;
  total_cost_usd: number | string;
  percent_of_total: number;
};

export type FigmaBillingPeriodUser = {
  user_email: string | null;
  user_name: string | null;
  figma_user_id: string | null;
  seat_type: string | null;
  seat_credits_used: number | string;
  paid_credits_used: number | string;
  seat_cost_usd: number | string;
  paid_cost_usd: number | string;
  total_cost_usd: number | string;
};

export type FigmaBillingPeriodOption = {
  import_id: string;
  usage_period_start: string | null;
  usage_period_end: string | null;
  upload_filename: string | null;
};

export type FigmaBillingInsights = {
  team_id: string;
  tool_id: string;
  from: string;
  to: string;
  has_import: boolean;
  has_config: boolean;
  imports_outside_filter: boolean;
  subscription_start?: string | null;
  full_seat_cost_usd: number | string | null;
  view_seat_cost_usd: number | string | null;
  credits_per_usd: number | string | null;
  configured_seat_cost: number | string | null;
  seat_cost: number | string | null;
  paid_cost: number | string | null;
  total_cost: number | string | null;
  monthly_budget: number | string | null;
  alert_threshold_usd: number | string | null;
  budget_remaining: number | string | null;
  budget_alert_triggered: boolean;
  full_seat_count: number | null;
  view_seat_count: number | null;
  user_count: number | null;
  credits: {
    total_seat_credits_used: number | string;
    total_paid_credits_used: number | string;
  };
  available_periods: FigmaBillingPeriodOption[];
  active_billing_period_start: string | null;
  active_billing_period_end: string | null;
  periods: FigmaBillingPeriodRow[];
  cost_trend: FigmaBillingCostTrendPoint[];
  top_users: FigmaBillingTopUser[];
  insights: Array<{ severity: string; title: string; message: string }>;
};

export type FigmaBillingPeriodUsers = {
  usage_period_start: string | null;
  usage_period_end: string | null;
  total_cost: number | string;
  total_paid_cost: number | string;
  total_seat_cost: number | string;
  users: FigmaBillingPeriodUser[];
};

export async function fetchFigmaBillingInsights(
  teamId: string,
  toolId: string,
  from: string,
  to: string,
): Promise<FigmaBillingInsights> {
  const params = new URLSearchParams({
    team_id: teamId,
    tool_id: toolId,
    from,
    to,
  });
  return apiRequest<FigmaBillingInsights>(`/figma/billing-insights?${params.toString()}`);
}

export async function fetchFigmaBillingDayUsers(
  teamId: string,
  toolId: string,
  onDate: string,
): Promise<FigmaBillingPeriodUsers> {
  const params = new URLSearchParams({
    team_id: teamId,
    tool_id: toolId,
    on_date: onDate,
  });
  return apiRequest<FigmaBillingPeriodUsers>(`/figma/billing-day-users?${params.toString()}`);
}

export async function fetchFigmaBillingPeriodUsers(
  teamId: string,
  toolId: string,
  periodStart: string | null,
  periodEnd: string | null,
): Promise<FigmaBillingPeriodUsers> {
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
  return apiRequest<FigmaBillingPeriodUsers>(
    `/figma/billing-period-users?${params.toString()}`,
  );
}

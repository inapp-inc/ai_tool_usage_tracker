import { apiRequest } from "./client";
import {
  mapApiThreshold,
  mapApiThresholdEvent,
  toThresholdCreateBody,
  toThresholdUpdateBody,
  type ApiThreshold,
  type ApiThresholdEvent,
} from "./adapters/alerts";

export type AlertSeverity = "critical" | "warning" | "info";
export type ThresholdType = "token_count" | "cost_usd" | "budget_percent";
export type ThresholdScope = "organization" | "team" | "user";
export type AlertChannel = "in_app" | "email" | "in_app_and_email";

export interface AlertRule {
  id: string;
  name: string;
  severity: AlertSeverity;
  thresholdType: ThresholdType;
  thresholdValue: number;
  scope: ThresholdScope;
  teamId: string | null;
  teamName: string | null;
  channel: AlertChannel;
  emailRecipients: string[];
  status: "active" | "inactive";
  triggerCount: number;
  lastTriggeredAt: string | null;
  createdAt: string;
}

export interface AlertEvent {
  id: string;
  ruleId: string | null;
  ruleName: string;
  severity: AlertSeverity;
  message: string;
  teamName: string | null;
  triggeredAt: string;
  acknowledgedAt: string | null;
  acknowledgedBy: string | null;
}

export interface CreateAlertRuleRequest {
  name: string;
  severity: AlertSeverity;
  thresholdType: ThresholdType;
  thresholdValue: number;
  scope: ThresholdScope;
  teamId: string | null;
  channel: AlertChannel;
  emailRecipients: string[];
}

export type UpdateAlertRuleRequest = Partial<CreateAlertRuleRequest> & {
  status?: "active" | "inactive";
};

export type { ApiThreshold, ApiThresholdEvent } from "./adapters/alerts";

export async function fetchAlertRules(): Promise<AlertRule[]> {
  const rows = await apiRequest<ApiThreshold[]>("/thresholds");
  return rows.map(mapApiThreshold);
}

export async function createAlertRule(body: CreateAlertRuleRequest): Promise<AlertRule> {
  const created = await apiRequest<ApiThreshold>("/thresholds", {
    method: "POST",
    body: JSON.stringify(toThresholdCreateBody(body)),
  });
  return mapApiThreshold(created);
}

export async function updateAlertRule(
  id: string,
  body: UpdateAlertRuleRequest,
): Promise<AlertRule> {
  const updated = await apiRequest<ApiThreshold>(`/thresholds/${id}`, {
    method: "PATCH",
    body: JSON.stringify(toThresholdUpdateBody(body)),
  });
  return mapApiThreshold(updated);
}

export async function deleteAlertRule(id: string): Promise<void> {
  await apiRequest<void>(`/thresholds/${id}`, { method: "DELETE" });
}

export async function fetchAlertHistory(): Promise<AlertEvent[]> {
  const rows = await apiRequest<ApiThresholdEvent[]>("/thresholds/events");
  return rows.map(mapApiThresholdEvent);
}

export async function acknowledgeAlert(id: string): Promise<AlertEvent> {
  const updated = await apiRequest<ApiThresholdEvent>(
    `/thresholds/events/${id}/acknowledge`,
    { method: "POST" },
  );
  return mapApiThresholdEvent(updated);
}

export const alertsApi = {
  fetchAlertRules,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  fetchAlertHistory,
  acknowledgeAlert,
};

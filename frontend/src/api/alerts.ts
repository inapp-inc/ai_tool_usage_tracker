import { apiRequest } from "./client";

export type AlertSeverity = "critical" | "warning" | "info";
export type ThresholdType = "token_count" | "cost_usd" | "budget_percent";
export type ThresholdScope = "organization" | "team" | "tool" | "user";
export type AlertChannel = "email" | "webhook" | "both";

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
  webhookUrl: string | null;
  emailRecipients: string[];
  status: "active" | "inactive";
  triggerCount: number;
  lastTriggeredAt: string | null;
  createdAt: string;
}

export interface AlertEvent {
  id: string;
  ruleId: string;
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
  teamName: string | null;
  channel: AlertChannel;
  webhookUrl: string | null;
  emailRecipients: string[];
}

export type UpdateAlertRuleRequest = Partial<CreateAlertRuleRequest> & {
  status?: "active" | "inactive";
};

interface BackendAlertRule {
  id: string;
  name: string;
  severity: AlertSeverity;
  threshold_type: ThresholdType;
  threshold_value: number;
  scope: ThresholdScope;
  team_id: string | null;
  team_name: string | null;
  channel: AlertChannel;
  webhook_url: string | null;
  email_recipients: string[];
  status: "active" | "inactive";
  trigger_count: number;
  last_triggered_at: string | null;
  created_at: string;
}

interface BackendAlertEvent {
  id: string;
  rule_id: string;
  rule_name: string;
  severity: AlertSeverity;
  message: string;
  team_name: string | null;
  triggered_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
}

function mapRule(row: BackendAlertRule): AlertRule {
  return {
    id: row.id,
    name: row.name,
    severity: row.severity,
    thresholdType: row.threshold_type,
    thresholdValue: row.threshold_value,
    scope: row.scope,
    teamId: row.team_id,
    teamName: row.team_name,
    channel: row.channel,
    webhookUrl: row.webhook_url,
    emailRecipients: row.email_recipients ?? [],
    status: row.status,
    triggerCount: row.trigger_count ?? 0,
    lastTriggeredAt: row.last_triggered_at,
    createdAt: row.created_at,
  };
}

function mapEvent(row: BackendAlertEvent): AlertEvent {
  return {
    id: row.id,
    ruleId: row.rule_id,
    ruleName: row.rule_name,
    severity: row.severity,
    message: row.message,
    teamName: row.team_name,
    triggeredAt: row.triggered_at,
    acknowledgedAt: row.acknowledged_at,
    acknowledgedBy: row.acknowledged_by,
  };
}

export async function fetchAlertRules(): Promise<AlertRule[]> {
  const rows = await apiRequest<BackendAlertRule[]>("/alerts/rules");
  return rows.map(mapRule);
}

export async function createAlertRule(
  body: CreateAlertRuleRequest,
): Promise<AlertRule> {
  const created = await apiRequest<BackendAlertRule>("/alerts/rules", {
    method: "POST",
    body: JSON.stringify({
      name: body.name,
      severity: body.severity,
      threshold_type: body.thresholdType,
      threshold_value: body.thresholdValue,
      scope: body.scope,
      team_id: body.teamId,
      team_name: body.teamName,
      channel: body.channel,
      webhook_url: body.webhookUrl,
      email_recipients: body.emailRecipients,
    }),
  });
  return mapRule(created);
}

export async function updateAlertRule(
  id: string,
  body: UpdateAlertRuleRequest,
): Promise<AlertRule> {
  const payload: Record<string, unknown> = {};
  if (body.name !== undefined) payload.name = body.name;
  if (body.severity !== undefined) payload.severity = body.severity;
  if (body.thresholdType !== undefined) payload.threshold_type = body.thresholdType;
  if (body.thresholdValue !== undefined) payload.threshold_value = body.thresholdValue;
  if (body.scope !== undefined) payload.scope = body.scope;
  if (body.teamId !== undefined) payload.team_id = body.teamId;
  if (body.teamName !== undefined) payload.team_name = body.teamName;
  if (body.channel !== undefined) payload.channel = body.channel;
  if (body.webhookUrl !== undefined) payload.webhook_url = body.webhookUrl;
  if (body.emailRecipients !== undefined) {
    payload.email_recipients = body.emailRecipients;
  }
  if (body.status !== undefined) payload.status = body.status;

  const updated = await apiRequest<BackendAlertRule>(`/alerts/rules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return mapRule(updated);
}

export async function deleteAlertRule(id: string): Promise<void> {
  await apiRequest<void>(`/alerts/rules/${id}`, { method: "DELETE" });
}

export async function fetchAlertHistory(): Promise<AlertEvent[]> {
  const rows = await apiRequest<BackendAlertEvent[]>("/alerts/events");
  return rows.map(mapEvent);
}

export async function acknowledgeAlert(id: string): Promise<AlertEvent> {
  const updated = await apiRequest<BackendAlertEvent>(
    `/alerts/events/${id}/acknowledge`,
    { method: "POST" },
  );
  return mapEvent(updated);
}

export const alertsApi = {
  fetchAlertRules,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  fetchAlertHistory,
  acknowledgeAlert,
};

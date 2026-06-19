/** Maps OpenAPI Threshold / ThresholdEvent to frontend AlertRule / AlertEvent. */

import type {
  AlertChannel,
  AlertEvent,
  AlertRule,
  AlertSeverity,
  CreateAlertRuleRequest,
  ThresholdScope,
  ThresholdType,
  UpdateAlertRuleRequest,
} from "../alerts";

export interface ApiThreshold {
  id: string;
  name: string;
  threshold_type: string;
  scope: string;
  tool_id?: string | null;
  team_id?: string | null;
  user_id?: string | null;
  team_name?: string | null;
  limit_value: number;
  severity: string;
  active: boolean;
  notify_email: boolean;
  notify_in_app: boolean;
  webhook_url?: string | null;
  email_recipients?: string[];
  trigger_count?: number;
  last_triggered_at?: string | null;
  created_at: string;
}

export interface ApiThresholdEvent {
  id: string;
  rule_id: string;
  rule_name: string;
  severity: string;
  message: string;
  team_name?: string | null;
  triggered_at: string;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
}

const THRESHOLD_TYPE_TO_API: Record<ThresholdType, string> = {
  token_count: "token_count",
  cost_usd: "cost_amount",
  budget_percent: "package_utilization_pct",
};

const THRESHOLD_TYPE_FROM_API: Record<string, ThresholdType> = {
  token_count: "token_count",
  cost_amount: "cost_usd",
  package_utilization_pct: "budget_percent",
};

function channelFromApi(threshold: ApiThreshold): AlertChannel {
  if (threshold.notify_email && threshold.notify_in_app) {
    return "in_app_and_email";
  }
  if (threshold.notify_email) {
    return "email";
  }
  return "in_app";
}

function channelToApi(channel: AlertChannel): {
  notify_email: boolean;
  notify_in_app: boolean;
} {
  switch (channel) {
    case "in_app":
      return { notify_email: false, notify_in_app: true };
    case "email":
      return { notify_email: true, notify_in_app: false };
    case "in_app_and_email":
      return { notify_email: true, notify_in_app: true };
  }
}

function severityFromApi(value: string): AlertSeverity {
  if (value === "critical" || value === "warning" || value === "info") {
    return value;
  }
  return "warning";
}

function scopeFromApi(value: string): ThresholdScope {
  if (value === "organization" || value === "team" || value === "user") {
    return value;
  }
  if (value === "tool") {
    return "team";
  }
  return "organization";
}

export function mapApiThreshold(api: ApiThreshold): AlertRule {
  return {
    id: api.id,
    name: api.name,
    severity: severityFromApi(api.severity),
    thresholdType: THRESHOLD_TYPE_FROM_API[api.threshold_type] ?? "token_count",
    thresholdValue: Number(api.limit_value),
    scope: scopeFromApi(api.scope),
    teamId: api.team_id ?? null,
    teamName: api.team_name ?? null,
    channel: channelFromApi(api),
    emailRecipients: api.email_recipients ?? [],
    status: api.active ? "active" : "inactive",
    triggerCount: api.trigger_count ?? 0,
    lastTriggeredAt: api.last_triggered_at ?? null,
    createdAt: api.created_at,
  };
}

export function mapApiThresholdEvent(api: ApiThresholdEvent): AlertEvent {
  return {
    id: api.id,
    ruleId: api.rule_id,
    ruleName: api.rule_name,
    severity: severityFromApi(api.severity),
    message: api.message,
    teamName: api.team_name ?? null,
    triggeredAt: api.triggered_at,
    acknowledgedAt: api.acknowledged_at ?? null,
    acknowledgedBy: api.acknowledged_by ?? null,
  };
}

export function toThresholdCreateBody(body: CreateAlertRuleRequest): Record<string, unknown> {
  const channel = channelToApi(body.channel);
  return {
    name: body.name,
    threshold_type: THRESHOLD_TYPE_TO_API[body.thresholdType],
    scope: body.scope,
    team_id: body.scope === "organization" ? null : body.teamId,
    user_id: body.scope === "user" ? null : null,
    limit_value: body.thresholdValue,
    severity: body.severity,
    notify_email: channel.notify_email,
    notify_in_app: channel.notify_in_app,
    webhook_url: null,
    email_recipients: body.emailRecipients,
    active: true,
  };
}

export function toThresholdUpdateBody(
  body: UpdateAlertRuleRequest,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};

  if (body.name !== undefined) {
    payload.name = body.name;
  }
  if (body.thresholdType !== undefined) {
    payload.threshold_type = THRESHOLD_TYPE_TO_API[body.thresholdType];
  }
  if (body.thresholdValue !== undefined) {
    payload.limit_value = body.thresholdValue;
  }
  if (body.scope !== undefined) {
    payload.scope = body.scope;
    if (body.scope === "organization") {
      payload.team_id = null;
    }
  }
  if (body.teamId !== undefined) {
    payload.team_id = body.teamId;
  }
  if (body.severity !== undefined) {
    payload.severity = body.severity;
  }
  if (body.channel !== undefined) {
    const channel = channelToApi(body.channel);
    payload.notify_email = channel.notify_email;
    payload.notify_in_app = channel.notify_in_app;
    payload.webhook_url = null;
  }
  if (body.emailRecipients !== undefined) {
    payload.email_recipients = body.emailRecipients;
  }
  if (body.status !== undefined) {
    payload.active = body.status === "active";
  }

  return payload;
}

export { THRESHOLD_TYPE_FROM_API, THRESHOLD_TYPE_TO_API };

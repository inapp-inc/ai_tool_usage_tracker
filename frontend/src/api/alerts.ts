const MOCK_LATENCY_MS = 400;

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), ms);
  });
}

export type AlertSeverity = "critical" | "warning" | "info";
export type ThresholdType = "token_count" | "cost_usd" | "budget_percent";
export type ThresholdScope = "organization" | "team" | "user";
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
  channel: AlertChannel;
  webhookUrl: string | null;
  emailRecipients: string[];
}

export type UpdateAlertRuleRequest = Partial<CreateAlertRuleRequest> & {
  status?: "active" | "inactive";
};

const TEAM_NAMES: Record<string, string> = {
  team_1: "Engineering",
  team_2: "Data Science",
  team_3: "Design",
  team_4: "Marketing",
  team_5: "Support",
  team_6: "Operations",
};

function resolveTeamName(teamId: string | null): string | null {
  if (!teamId) {
    return null;
  }
  return TEAM_NAMES[teamId] ?? null;
}

let mockAlertRules: AlertRule[] = [
  {
    id: "alert_1",
    name: "Org Token Spike",
    severity: "critical",
    thresholdType: "token_count",
    thresholdValue: 10_000_000,
    scope: "organization",
    teamId: null,
    teamName: null,
    channel: "email",
    webhookUrl: null,
    emailRecipients: ["ops@acme.com", "admin@acme.com"],
    status: "active",
    triggerCount: 5,
    lastTriggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 90).toISOString(),
  },
  {
    id: "alert_2",
    name: "Engineering Budget Threshold",
    severity: "warning",
    thresholdType: "budget_percent",
    thresholdValue: 80,
    scope: "team",
    teamId: "team_1",
    teamName: "Engineering",
    channel: "both",
    webhookUrl: "https://hooks.acme.com/alerts/engineering",
    emailRecipients: ["eng-leads@acme.com"],
    status: "active",
    triggerCount: 12,
    lastTriggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString(),
  },
  {
    id: "alert_3",
    name: "Data Science Cost Limit",
    severity: "info",
    thresholdType: "cost_usd",
    thresholdValue: 200,
    scope: "team",
    teamId: "team_2",
    teamName: "Data Science",
    channel: "webhook",
    webhookUrl: "https://hooks.acme.com/alerts/data-science",
    emailRecipients: [],
    status: "active",
    triggerCount: 3,
    lastTriggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 45).toISOString(),
  },
  {
    id: "alert_4",
    name: "Design User Overage",
    severity: "warning",
    thresholdType: "token_count",
    thresholdValue: 500_000,
    scope: "user",
    teamId: "team_3",
    teamName: "Design",
    channel: "email",
    webhookUrl: null,
    emailRecipients: ["design-admin@acme.com"],
    status: "inactive",
    triggerCount: 0,
    lastTriggeredAt: null,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
  },
  {
    id: "alert_5",
    name: "Monthly Org Cost Cap",
    severity: "critical",
    thresholdType: "cost_usd",
    thresholdValue: 5000,
    scope: "organization",
    teamId: null,
    teamName: null,
    channel: "both",
    webhookUrl: "https://hooks.acme.com/alerts/org-cost",
    emailRecipients: ["finance@acme.com", "cfo@acme.com"],
    status: "active",
    triggerCount: 2,
    lastTriggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 120).toISOString(),
  },
  {
    id: "alert_6",
    name: "Marketing Budget Alert",
    severity: "warning",
    thresholdType: "budget_percent",
    thresholdValue: 90,
    scope: "team",
    teamId: "team_4",
    teamName: "Marketing",
    channel: "email",
    webhookUrl: null,
    emailRecipients: ["marketing-leads@acme.com"],
    status: "active",
    triggerCount: 1,
    lastTriggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14).toISOString(),
  },
];

let mockAlertHistory: AlertEvent[] = [
  {
    id: "event_1",
    ruleId: "alert_2",
    ruleName: "Engineering Budget Threshold",
    severity: "warning",
    message: "Engineering team exceeded 80% of token budget",
    teamName: "Engineering",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    acknowledgedAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    acknowledgedBy: "Alan Chen",
  },
  {
    id: "event_2",
    ruleId: "alert_1",
    ruleName: "Org Token Spike",
    severity: "critical",
    message: "Organization token usage exceeded 10M tokens in 24 hours",
    teamName: null,
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    acknowledgedAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
    acknowledgedBy: "Jordan Lee",
  },
  {
    id: "event_3",
    ruleId: "alert_3",
    ruleName: "Data Science Cost Limit",
    severity: "info",
    message: "Data Science team cost reached $200 this month",
    teamName: "Data Science",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    acknowledgedAt: null,
    acknowledgedBy: null,
  },
  {
    id: "event_4",
    ruleId: "alert_5",
    ruleName: "Monthly Org Cost Cap",
    severity: "critical",
    message: "Organization monthly cost exceeded $5,000",
    teamName: null,
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
    acknowledgedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 6).toISOString(),
    acknowledgedBy: "Morgan Patel",
  },
  {
    id: "event_5",
    ruleId: "alert_6",
    ruleName: "Marketing Budget Alert",
    severity: "warning",
    message: "Marketing team exceeded 90% of monthly budget",
    teamName: "Marketing",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
    acknowledgedAt: null,
    acknowledgedBy: null,
  },
  {
    id: "event_6",
    ruleId: "alert_2",
    ruleName: "Engineering Budget Threshold",
    severity: "warning",
    message: "Engineering team exceeded 80% of token budget",
    teamName: "Engineering",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
    acknowledgedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 4).toISOString(),
    acknowledgedBy: "Sam Rivera",
  },
  {
    id: "event_7",
    ruleId: "alert_1",
    ruleName: "Org Token Spike",
    severity: "critical",
    message: "Organization token usage exceeded 10M tokens in 24 hours",
    teamName: null,
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(),
    acknowledgedAt: null,
    acknowledgedBy: null,
  },
  {
    id: "event_8",
    ruleId: "alert_3",
    ruleName: "Data Science Cost Limit",
    severity: "info",
    message: "Data Science team cost reached $200 this month",
    teamName: "Data Science",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 12).toISOString(),
    acknowledgedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 11).toISOString(),
    acknowledgedBy: "Taylor Kim",
  },
  {
    id: "event_9",
    ruleId: "alert_5",
    ruleName: "Monthly Org Cost Cap",
    severity: "critical",
    message: "Organization monthly cost exceeded $5,000",
    teamName: null,
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 20).toISOString(),
    acknowledgedAt: null,
    acknowledgedBy: null,
  },
  {
    id: "event_10",
    ruleId: "alert_2",
    ruleName: "Engineering Budget Threshold",
    severity: "warning",
    message: "Engineering team exceeded 80% of token budget",
    teamName: "Engineering",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14).toISOString(),
    acknowledgedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 13).toISOString(),
    acknowledgedBy: "Alan Chen",
  },
];

export async function fetchAlertRules(): Promise<AlertRule[]> {
  return delay([...mockAlertRules]);
}

export async function createAlertRule(
  body: CreateAlertRuleRequest,
): Promise<AlertRule> {
  const rule: AlertRule = {
    id: `alert_${Date.now()}`,
    name: body.name,
    severity: body.severity,
    thresholdType: body.thresholdType,
    thresholdValue: body.thresholdValue,
    scope: body.scope,
    teamId: body.teamId,
    teamName: resolveTeamName(body.teamId),
    channel: body.channel,
    webhookUrl: body.webhookUrl,
    emailRecipients: body.emailRecipients,
    status: "active",
    triggerCount: 0,
    lastTriggeredAt: null,
    createdAt: new Date().toISOString(),
  };

  mockAlertRules = [rule, ...mockAlertRules];
  return delay(rule);
}

export async function updateAlertRule(
  id: string,
  body: UpdateAlertRuleRequest,
): Promise<AlertRule> {
  const index = mockAlertRules.findIndex((rule) => rule.id === id);
  if (index === -1) {
    throw new Error("Alert rule not found");
  }

  const existing = mockAlertRules[index];
  const teamId =
    body.teamId !== undefined ? body.teamId : existing.teamId;
  const updated: AlertRule = {
    ...existing,
    ...body,
    teamId,
    teamName: resolveTeamName(teamId),
  };

  mockAlertRules = [
    ...mockAlertRules.slice(0, index),
    updated,
    ...mockAlertRules.slice(index + 1),
  ];
  return delay(updated);
}

export async function deleteAlertRule(id: string): Promise<void> {
  mockAlertRules = mockAlertRules.filter((rule) => rule.id !== id);
  await delay(undefined);
}

export async function fetchAlertHistory(): Promise<AlertEvent[]> {
  return delay([...mockAlertHistory]);
}

export async function acknowledgeAlert(id: string): Promise<AlertEvent> {
  const index = mockAlertHistory.findIndex((event) => event.id === id);
  if (index === -1) {
    throw new Error("Alert event not found");
  }

  const updated: AlertEvent = {
    ...mockAlertHistory[index],
    acknowledgedAt: new Date().toISOString(),
    acknowledgedBy: "Alan Chen",
  };

  mockAlertHistory = [
    ...mockAlertHistory.slice(0, index),
    updated,
    ...mockAlertHistory.slice(index + 1),
  ];
  return delay(updated);
}

export const alertsApi = {
  fetchAlertRules,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  fetchAlertHistory,
  acknowledgeAlert,
};

/** Maps OpenAPI report job responses to frontend Report types. */

import type {
  CreateReportRequest,
  CreateSubscriptionRequest,
  Report,
  ReportFormat,
  ReportStatus,
  ReportSubscription,
  ReportType,
} from "../reports";

export interface ApiReportJob {
  job_id: string;
  name: string;
  report_type: string;
  status: string;
  format: string;
  from: string;
  to: string;
  schedule: string;
  team_ids: string[];
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  file_size_kb?: number | null;
  created_by_name?: string | null;
  subscription_count?: number;
}

export interface ApiReportSubscription {
  id: string;
  report_id: string;
  channel: string;
  cadence: string;
  email_recipients: string[];
  created_at: string;
  created_by_name?: string | null;
}

const REPORT_TYPE_FROM_API: Record<string, ReportType> = {
  tool_usage_summary: "usage_summary",
  cost: "cost_breakdown",
  team_usage: "team_comparison",
  user_usage: "user_activity",
  alert_history: "usage_summary",
  api_key_activity: "usage_summary",
};

const REPORT_TYPE_TO_API: Record<ReportType, string> = {
  usage_summary: "tool_usage_summary",
  cost_breakdown: "cost",
  team_comparison: "team_usage",
  user_activity: "user_usage",
  budget_variance: "team_usage",
};

function statusFromApi(status: string): ReportStatus {
  if (status === "failed") {
    return "error";
  }
  if (
    status === "pending" ||
    status === "processing" ||
    status === "completed" ||
    status === "error"
  ) {
    return status;
  }
  return "pending";
}

function formatFromApi(format: string): ReportFormat {
  if (format === "csv" || format === "pdf" || format === "xlsx") {
    return format;
  }
  return "csv";
}

export function mapApiReportJob(api: ApiReportJob): Report {
  return {
    id: api.job_id,
    name: api.name,
    type: REPORT_TYPE_FROM_API[api.report_type] ?? "usage_summary",
    format: formatFromApi(api.format),
    status: statusFromApi(api.status),
    schedule: (api.schedule as Report["schedule"]) || "once",
    periodFrom: api.from,
    periodTo: api.to,
    teamIds: api.team_ids ?? [],
    generatedAt: api.completed_at ?? null,
    fileSizeKb: api.file_size_kb ?? null,
    createdByName: api.created_by_name ?? "Unknown",
    createdAt: api.created_at,
    errorMessage: api.error_message ?? null,
    subscriptionCount: api.subscription_count ?? 0,
  };
}

export function mapApiSubscription(api: ApiReportSubscription): ReportSubscription {
  return {
    id: api.id,
    reportId: api.report_id,
    channel: api.channel as ReportSubscription["channel"],
    cadence: api.cadence as ReportSubscription["cadence"],
    emailRecipients: api.email_recipients ?? [],
    createdAt: api.created_at,
    createdByName: api.created_by_name ?? "Unknown",
  };
}

export function toReportGenerateBody(body: CreateReportRequest): Record<string, unknown> {
  const format = body.format === "xlsx" || body.format === "pdf" ? "csv" : body.format;
  return {
    name: body.name,
    report_type: REPORT_TYPE_TO_API[body.type],
    from: body.periodFrom,
    to: body.periodTo,
    format,
    schedule: body.schedule,
    team_ids: body.teamIds,
    async: false,
  };
}

export function toSubscriptionCreateBody(
  body: CreateSubscriptionRequest,
): Record<string, unknown> {
  return {
    channel: body.channel,
    cadence: body.cadence,
    email_recipients: body.emailRecipients,
  };
}

export { REPORT_TYPE_FROM_API, REPORT_TYPE_TO_API };

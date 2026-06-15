import { apiRequest } from "./client";

export type ReportType =
  | "usage_summary"
  | "cost_breakdown"
  | "team_comparison"
  | "user_activity"
  | "budget_variance";

export type ReportFormat = "pdf" | "csv" | "xlsx";
export type ReportStatus = "pending" | "processing" | "completed" | "error";
export type ReportSchedule = "once" | "daily" | "weekly" | "monthly";

export interface Report {
  id: string;
  name: string;
  type: ReportType;
  format: ReportFormat;
  status: ReportStatus;
  schedule: ReportSchedule;
  periodFrom: string;
  periodTo: string;
  teamIds: string[];
  generatedAt: string | null;
  fileSizeKb: number | null;
  createdByName: string;
  createdAt: string;
  errorMessage: string | null;
  subscriptionCount: number;
}

export type SubscriptionChannel = "email" | "in_app" | "both";
export type SubscriptionCadence = "daily" | "weekly" | "monthly";

export interface ReportSubscription {
  id: string;
  reportId: string;
  channel: SubscriptionChannel;
  cadence: SubscriptionCadence;
  emailRecipients: string[];
  createdAt: string;
  createdByName: string;
}

export interface CreateReportRequest {
  name: string;
  type: ReportType;
  format: ReportFormat;
  schedule: ReportSchedule;
  periodFrom: string;
  periodTo: string;
  teamIds: string[];
}

export interface CreateSubscriptionRequest {
  channel: SubscriptionChannel;
  cadence: SubscriptionCadence;
  emailRecipients: string[];
}

interface BackendReport {
  id: string;
  name: string;
  type: ReportType;
  format: ReportFormat;
  status: ReportStatus;
  schedule: ReportSchedule;
  period_from: string;
  period_to: string;
  team_ids: string[];
  generated_at: string | null;
  file_size_kb: number | null;
  created_by_name: string;
  created_at: string;
  error_message: string | null;
  subscription_count: number;
}

interface BackendSubscription {
  id: string;
  report_id: string;
  channel: SubscriptionChannel;
  cadence: SubscriptionCadence;
  email_recipients: string[];
  created_at: string;
  created_by_name: string;
}

function mapReport(row: BackendReport): Report {
  return {
    id: row.id,
    name: row.name,
    type: row.type,
    format: row.format,
    status: row.status,
    schedule: row.schedule,
    periodFrom: row.period_from,
    periodTo: row.period_to,
    teamIds: row.team_ids ?? [],
    generatedAt: row.generated_at,
    fileSizeKb: row.file_size_kb,
    createdByName: row.created_by_name,
    createdAt: row.created_at,
    errorMessage: row.error_message,
    subscriptionCount: row.subscription_count ?? 0,
  };
}

function mapSubscription(row: BackendSubscription): ReportSubscription {
  return {
    id: row.id,
    reportId: row.report_id,
    channel: row.channel,
    cadence: row.cadence,
    emailRecipients: row.email_recipients ?? [],
    createdAt: row.created_at,
    createdByName: row.created_by_name,
  };
}

export async function fetchReports(): Promise<Report[]> {
  const rows = await apiRequest<BackendReport[]>("/reports");
  return rows.map(mapReport);
}

export async function createReport(body: CreateReportRequest): Promise<Report> {
  const created = await apiRequest<BackendReport>("/reports", {
    method: "POST",
    body: JSON.stringify({
      name: body.name,
      type: body.type,
      format: body.format,
      schedule: body.schedule,
      period_from: body.periodFrom,
      period_to: body.periodTo,
      team_ids: body.teamIds,
    }),
  });
  return mapReport(created);
}

export async function deleteReport(id: string): Promise<void> {
  await apiRequest<void>(`/reports/${id}`, { method: "DELETE" });
}

export async function downloadReport(id: string): Promise<void> {
  const report = (await fetchReports()).find((item) => item.id === id);
  if (!report || report.status !== "completed") {
    throw new Error("Report not available for download");
  }
}

export async function fetchSubscriptions(
  reportId: string,
): Promise<ReportSubscription[]> {
  const rows = await apiRequest<BackendSubscription[]>(
    `/reports/${reportId}/subscriptions`,
  );
  return rows.map(mapSubscription);
}

export async function createSubscription(
  reportId: string,
  body: CreateSubscriptionRequest,
): Promise<ReportSubscription> {
  const created = await apiRequest<BackendSubscription>(
    `/reports/${reportId}/subscriptions`,
    {
      method: "POST",
      body: JSON.stringify({
        channel: body.channel,
        cadence: body.cadence,
        email_recipients: body.emailRecipients,
      }),
    },
  );
  return mapSubscription(created);
}

export async function deleteSubscription(
  reportId: string,
  subscriptionId: string,
): Promise<void> {
  await apiRequest<void>(
    `/reports/${reportId}/subscriptions/${subscriptionId}`,
    { method: "DELETE" },
  );
}

export const reportsApi = {
  fetchReports,
  createReport,
  deleteReport,
  downloadReport,
  fetchSubscriptions,
  createSubscription,
  deleteSubscription,
};

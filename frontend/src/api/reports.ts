import { apiFetch, apiRequest } from "./client";
import {
  mapApiReportJob,
  mapApiSubscription,
  toReportGenerateBody,
  toSubscriptionCreateBody,
  type ApiReportJob,
  type ApiReportSubscription,
} from "./adapters/reports";

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

export async function fetchReports(): Promise<Report[]> {
  const rows = await apiRequest<ApiReportJob[]>("/reports");
  return rows.map(mapApiReportJob);
}

export async function createReport(body: CreateReportRequest): Promise<Report> {
  const created = await apiRequest<ApiReportJob>("/reports/generate", {
    method: "POST",
    body: JSON.stringify(toReportGenerateBody(body)),
  });
  return mapApiReportJob(created);
}

export async function deleteReport(id: string): Promise<void> {
  await apiRequest<void>(`/reports/${id}`, { method: "DELETE" });
}

export async function downloadReport(id: string): Promise<void> {
  const { apiFetch, ApiClientError, parseApiError } = await import("./client");
  const response = await apiFetch(`/reports/jobs/${id}/download`);
  if (!response.ok) {
    throw new ApiClientError(await parseApiError(response));
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match?.[1] ?? `report-${id}.csv`;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function fetchSubscriptions(
  reportId: string,
): Promise<ReportSubscription[]> {
  const rows = await apiRequest<ApiReportSubscription[]>(
    `/reports/${reportId}/subscriptions`,
  );
  return rows.map(mapApiSubscription);
}

export async function createSubscription(
  reportId: string,
  body: CreateSubscriptionRequest,
): Promise<ReportSubscription> {
  const created = await apiRequest<ApiReportSubscription>(
    `/reports/${reportId}/subscriptions`,
    {
      method: "POST",
      body: JSON.stringify(toSubscriptionCreateBody(body)),
    },
  );
  return mapApiSubscription(created);
}

export async function deleteSubscription(
  reportId: string,
  subscriptionId: string,
): Promise<void> {
  await apiRequest<void>(`/reports/${reportId}/subscriptions/${subscriptionId}`, {
    method: "DELETE",
  });
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

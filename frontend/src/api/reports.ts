const MOCK_LATENCY_MS = 400;
const DOWNLOAD_LATENCY_MS = 300;

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), ms);
  });
}

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

let mockReports: Report[] = [
  {
    id: "report_1",
    name: "June Usage Summary",
    type: "usage_summary",
    format: "pdf",
    status: "completed",
    schedule: "once",
    periodFrom: new Date("2026-06-01T00:00:00Z").toISOString(),
    periodTo: new Date("2026-06-30T23:59:59Z").toISOString(),
    teamIds: [],
    generatedAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
    fileSizeKb: 842,
    createdByName: "Alan Chen",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    errorMessage: null,
    subscriptionCount: 1,
  },
  {
    id: "report_2",
    name: "Weekly Cost Breakdown",
    type: "cost_breakdown",
    format: "csv",
    status: "completed",
    schedule: "weekly",
    periodFrom: new Date("2026-05-01T00:00:00Z").toISOString(),
    periodTo: new Date("2026-05-31T23:59:59Z").toISOString(),
    teamIds: ["team_1", "team_2"],
    generatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
    fileSizeKb: 128,
    createdByName: "Jordan Lee",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    errorMessage: null,
    subscriptionCount: 2,
  },
  {
    id: "report_3",
    name: "Team Comparison Q2",
    type: "team_comparison",
    format: "xlsx",
    status: "processing",
    schedule: "once",
    periodFrom: new Date("2026-04-01T00:00:00Z").toISOString(),
    periodTo: new Date("2026-06-30T23:59:59Z").toISOString(),
    teamIds: [],
    generatedAt: null,
    fileSizeKb: null,
    createdByName: "Sam Rivera",
    createdAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    errorMessage: null,
    subscriptionCount: 0,
  },
  {
    id: "report_4",
    name: "User Activity Export",
    type: "user_activity",
    format: "csv",
    status: "pending",
    schedule: "daily",
    periodFrom: new Date("2026-06-01T00:00:00Z").toISOString(),
    periodTo: new Date("2026-06-11T23:59:59Z").toISOString(),
    teamIds: ["team_3"],
    generatedAt: null,
    fileSizeKb: null,
    createdByName: "Taylor Kim",
    createdAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    errorMessage: null,
    subscriptionCount: 0,
  },
  {
    id: "report_5",
    name: "Budget Variance May",
    type: "budget_variance",
    format: "pdf",
    status: "error",
    schedule: "monthly",
    periodFrom: new Date("2026-05-01T00:00:00Z").toISOString(),
    periodTo: new Date("2026-05-31T23:59:59Z").toISOString(),
    teamIds: ["team_1", "team_5"],
    generatedAt: null,
    fileSizeKb: null,
    createdByName: "Morgan Patel",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
    errorMessage: "Failed to aggregate budget data",
    subscriptionCount: 0,
  },
  {
    id: "report_6",
    name: "Engineering Usage CSV",
    type: "usage_summary",
    format: "csv",
    status: "completed",
    schedule: "weekly",
    periodFrom: new Date("2026-06-01T00:00:00Z").toISOString(),
    periodTo: new Date("2026-06-07T23:59:59Z").toISOString(),
    teamIds: ["team_1"],
    generatedAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
    fileSizeKb: 96,
    createdByName: "Alan Chen",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 50).toISOString(),
    errorMessage: null,
    subscriptionCount: 1,
  },
  {
    id: "report_7",
    name: "All Teams Cost XLSX",
    type: "cost_breakdown",
    format: "xlsx",
    status: "completed",
    schedule: "monthly",
    periodFrom: new Date("2026-01-01T00:00:00Z").toISOString(),
    periodTo: new Date("2026-06-30T23:59:59Z").toISOString(),
    teamIds: [],
    generatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
    fileSizeKb: 2048,
    createdByName: "Dana Wolfe",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 8).toISOString(),
    errorMessage: null,
    subscriptionCount: 0,
  },
  {
    id: "report_8",
    name: "Support Team Activity",
    type: "user_activity",
    format: "pdf",
    status: "completed",
    schedule: "once",
    periodFrom: new Date("2026-05-15T00:00:00Z").toISOString(),
    periodTo: new Date("2026-06-11T23:59:59Z").toISOString(),
    teamIds: ["team_6"],
    generatedAt: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(),
    fileSizeKb: 512,
    createdByName: "Riley Brooks",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 73).toISOString(),
    errorMessage: null,
    subscriptionCount: 0,
  },
];

let mockSubscriptions: ReportSubscription[] = [
  {
    id: "sub_1",
    reportId: "report_1",
    channel: "email",
    cadence: "weekly",
    emailRecipients: ["alice@co.com"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14).toISOString(),
    createdByName: "Alan Chen",
  },
  {
    id: "sub_2",
    reportId: "report_2",
    channel: "both",
    cadence: "daily",
    emailRecipients: ["alice@co.com", "bob@co.com"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(),
    createdByName: "Jordan Lee",
  },
  {
    id: "sub_3",
    reportId: "report_2",
    channel: "in_app",
    cadence: "monthly",
    emailRecipients: [],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
    createdByName: "Jordan Lee",
  },
  {
    id: "sub_4",
    reportId: "report_6",
    channel: "email",
    cadence: "weekly",
    emailRecipients: ["eng-team@co.com"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    createdByName: "Alan Chen",
  },
];

export async function fetchReports(): Promise<Report[]> {
  return delay([...mockReports]);
}

export async function createReport(body: CreateReportRequest): Promise<Report> {
  const report: Report = {
    id: `report_${Date.now()}`,
    name: body.name,
    type: body.type,
    format: body.format,
    status: "pending",
    schedule: body.schedule,
    periodFrom: body.periodFrom,
    periodTo: body.periodTo,
    teamIds: body.teamIds,
    generatedAt: null,
    fileSizeKb: null,
    createdByName: "Alan Chen",
    createdAt: new Date().toISOString(),
    errorMessage: null,
    subscriptionCount: 0,
  };

  mockReports = [report, ...mockReports];
  return delay(report);
}

export async function deleteReport(id: string): Promise<void> {
  mockReports = mockReports.filter((report) => report.id !== id);
  await delay(undefined);
}

export async function downloadReport(id: string): Promise<void> {
  const report = mockReports.find((item) => item.id === id);
  if (!report || report.status !== "completed") {
    throw new Error("Report not available for download");
  }
  await delay(undefined, DOWNLOAD_LATENCY_MS);
}

export async function fetchSubscriptions(
  reportId: string,
): Promise<ReportSubscription[]> {
  const subscriptions = mockSubscriptions.filter(
    (subscription) => subscription.reportId === reportId,
  );
  return delay([...subscriptions]);
}

export async function createSubscription(
  reportId: string,
  body: CreateSubscriptionRequest,
): Promise<ReportSubscription> {
  const subscription: ReportSubscription = {
    id: `sub_${Date.now()}`,
    reportId,
    channel: body.channel,
    cadence: body.cadence,
    emailRecipients: body.emailRecipients,
    createdAt: new Date().toISOString(),
    createdByName: "Alan Chen",
  };

  mockSubscriptions = [...mockSubscriptions, subscription];
  mockReports = mockReports.map((report) =>
    report.id === reportId
      ? { ...report, subscriptionCount: report.subscriptionCount + 1 }
      : report,
  );

  return delay(subscription);
}

export async function deleteSubscription(
  reportId: string,
  subscriptionId: string,
): Promise<void> {
  const hadSubscription = mockSubscriptions.some(
    (subscription) =>
      subscription.id === subscriptionId && subscription.reportId === reportId,
  );

  mockSubscriptions = mockSubscriptions.filter(
    (subscription) => subscription.id !== subscriptionId,
  );

  if (hadSubscription) {
    mockReports = mockReports.map((report) =>
      report.id === reportId
        ? {
            ...report,
            subscriptionCount: Math.max(0, report.subscriptionCount - 1),
          }
        : report,
    );
  }

  await delay(undefined);
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

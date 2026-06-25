/** Maps OpenAPI Upload responses to frontend UploadRecord / UploadPreview. */

import type {
  CopilotImportSummary,
  FigmaImportSummary,
  UploadColumnMapping,
  UploadFormat,
  UploadMapping,
  UploadPreview,
  UploadPreviewRow,
  UploadRecord,
} from "../uploads";

export interface ApiUpload {
  id: string;
  team_id?: string | null;
  tool_id?: string | null;
  team_name?: string | null;
  tool_name?: string | null;
  billing_period_start?: string | null;
  billing_period_end?: string | null;
  filename: string;
  detected_format?: string | null;
  size_bytes: number;
  status: string;
  total_rows?: number | null;
  matched_rows?: number | null;
  unmatched_rows?: number | null;
  error_message?: string | null;
  uploaded_by_name?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface ApiUploadCreateResponse {
  upload_id: string;
  status: string;
  filename: string;
  size_bytes: number;
  upload: ApiUpload;
}

export interface ApiParsedUsageRow {
  row_number: number;
  user_email?: string | null;
  matched_user_id?: string | null;
  user_name?: string | null;
  input_tokens: number;
  output_tokens: number;
  occurred_at?: string | null;
  model?: string | null;
  cost?: number;
  status: "valid" | "error";
  error_reason?: string | null;
  raw_data?: Record<string, unknown>;
  mapped_data?: Record<string, unknown>;
}

export interface ApiCopilotImportSummary {
  monthly_cost_limit: number;
  additional_cost: number;
  credits_cost?: number;
  total_cost: number;
  period_conflicts?: Array<{
    billing_period_start: string;
    billing_period_end: string;
    existing_filename: string;
    existing_upload_id: string;
  }>;
  sku_breakdown?: Array<{
    sku: string;
    billing_period_start: string | null;
    billing_period_end: string | null;
    monthly_cost_limit: number;
    additional_cost: number;
    total_cost: number;
    seat_count: number;
    row_count: number;
  }>;
}

export interface ApiFigmaImportSummary {
  total_seat_cost: number;
  total_paid_cost: number;
  total_cost: number;
  full_seat_count: number;
  view_seat_count: number;
  user_count: number;
  period_count: number;
  credits_per_usd?: number | null;
  period_conflicts?: Array<{
    usage_period_start: string;
    usage_period_end: string;
    existing_filename: string;
    existing_upload_id: string;
  }>;
}

export interface ApiUploadPreview {
  upload_id: string;
  filename: string;
  team_id?: string | null;
  team_name?: string | null;
  tool_id?: string | null;
  total_rows: number;
  matched_rows: number;
  unmatched_rows: number;
  rows: ApiParsedUsageRow[];
  copilot_summary?: ApiCopilotImportSummary | null;
  figma_summary?: ApiFigmaImportSummary | null;
}

export interface ApiUploadMappingField {
  key: string;
  label: string;
  required: boolean;
}

export interface ApiUploadMapping {
  upload_id: string;
  filename: string;
  headers: string[];
  fields: ApiUploadMappingField[];
  suggested_mapping: Record<string, string | null>;
  column_mapping?: Record<string, string | null> | null;
  sample_row?: Record<string, unknown>;
}

function mapUploadStatus(status: string): UploadRecord["status"] {
  switch (status) {
    case "completed":
      return "completed";
    case "failed":
      return "error";
    case "pending_mapping":
      return "mapping";
    case "parsing":
    case "committing":
      return "processing";
    case "preview_ready":
    case "pending":
    default:
      return "pending";
  }
}

function inferFormat(filename: string, detected?: string | null): UploadFormat {
  if (detected === "json" || filename.toLowerCase().endsWith(".json")) {
    return "json";
  }
  return "csv";
}

export function mapApiUpload(api: ApiUpload): UploadRecord {
  const rowCount =
    api.total_rows ??
    (api.matched_rows != null && api.unmatched_rows != null
      ? api.matched_rows + api.unmatched_rows
      : null);

  return {
    id: api.id,
    fileName: api.filename,
    format: inferFormat(api.filename, api.detected_format),
    status: mapUploadStatus(api.status),
    rowCount,
    errorCount: api.unmatched_rows ?? null,
    errorMessage: api.error_message ?? null,
    uploadedByName: api.uploaded_by_name ?? "—",
    teamId: api.team_id ?? null,
    teamName: api.team_name ?? null,
    toolId: api.tool_id ?? null,
    toolName: api.tool_name ?? null,
    billingPeriodStart: api.billing_period_start ?? null,
    billingPeriodEnd: api.billing_period_end ?? null,
    fileSizeKb: Math.max(1, Math.round(api.size_bytes / 1024)),
    createdAt: api.created_at,
    processedAt: api.completed_at ?? null,
  };
}

function mapCopilotSummary(
  summary: ApiCopilotImportSummary | null | undefined,
): CopilotImportSummary | null {
  if (!summary) {
    return null;
  }
  return {
    monthlyCostLimit: summary.monthly_cost_limit,
    additionalCost: summary.additional_cost,
    creditsCost: summary.credits_cost ?? 0,
    totalCost: summary.total_cost,
    periodConflicts: (summary.period_conflicts ?? []).map((row) => ({
      billingPeriodStart: row.billing_period_start,
      billingPeriodEnd: row.billing_period_end,
      existingFilename: row.existing_filename,
      existingUploadId: row.existing_upload_id,
    })),
    skuBreakdown: (summary.sku_breakdown ?? []).map((row) => ({
      sku: row.sku,
      billingPeriodStart: row.billing_period_start,
      billingPeriodEnd: row.billing_period_end,
      monthlyCostLimit: row.monthly_cost_limit,
      additionalCost: row.additional_cost,
      totalCost: row.total_cost,
      seatCount: row.seat_count,
      rowCount: row.row_count,
    })),
  };
}

function mapFigmaSummary(
  summary: ApiFigmaImportSummary | null | undefined,
): FigmaImportSummary | null {
  if (!summary) {
    return null;
  }
  return {
    totalSeatCost: summary.total_seat_cost,
    totalPaidCost: summary.total_paid_cost,
    totalCost: summary.total_cost,
    fullSeatCount: summary.full_seat_count,
    viewSeatCount: summary.view_seat_count,
    userCount: summary.user_count,
    periodCount: summary.period_count,
    creditsPerUsd: summary.credits_per_usd ?? null,
    periodConflicts: (summary.period_conflicts ?? []).map((row) => ({
      usagePeriodStart: row.usage_period_start,
      usagePeriodEnd: row.usage_period_end,
      existingFilename: row.existing_filename,
      existingUploadId: row.existing_upload_id,
    })),
  };
}

export function mapApiUploadPreview(api: ApiUploadPreview): UploadPreview {
  return {
    uploadId: api.upload_id,
    fileName: api.filename,
    teamId: api.team_id ?? null,
    teamName: api.team_name ?? null,
    toolId: api.tool_id ?? null,
    totalRows: api.total_rows,
    validRows: api.matched_rows,
    errorRows: api.unmatched_rows,
    rows: api.rows.map(mapApiPreviewRow),
    copilotSummary: mapCopilotSummary(api.copilot_summary),
    figmaSummary: mapFigmaSummary(api.figma_summary),
  };
}

export function mapApiUploadMapping(api: ApiUploadMapping): UploadMapping {
  return {
    uploadId: api.upload_id,
    fileName: api.filename,
    headers: api.headers,
    fields: api.fields.map((field) => ({
      key: field.key,
      label: field.label,
      required: field.required,
    })),
    suggestedMapping: api.suggested_mapping as UploadColumnMapping,
    columnMapping: (api.column_mapping ?? null) as UploadColumnMapping | null,
    sampleRow: api.sample_row ?? {},
  };
}

export function mapApiPreviewRow(api: ApiParsedUsageRow): UploadPreviewRow {
  const mapped = api.mapped_data ?? {};
  return {
    rowIndex: api.row_number,
    userId: api.matched_user_id ?? api.user_email ?? "",
    userName: api.user_name ?? api.user_email ?? "Unknown",
    model: api.model ?? String(mapped.model ?? ""),
    tokens: api.input_tokens + api.output_tokens,
    cost: api.cost ?? Number(mapped.estimated_cost ?? 0),
    timestamp: api.occurred_at ?? new Date(0).toISOString(),
    status: api.status,
    errorReason: api.error_reason ?? null,
    rawData: api.raw_data ?? {},
    mappedData: api.mapped_data ?? {},
  };
}

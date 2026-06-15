import { apiFormRequest, apiRequest } from "./client";
import {
  appendCsvMappingToFormData,
  mapCsvMappingFromBackend,
  type ToolCsvColumnMapping,
  type ToolCsvFormatHint,
} from "./tools";

export type UploadFormat = "csv" | "json";

export interface UploadRecord {
  id: string;
  fileName: string;
  format: UploadFormat;
  status: "pending" | "processing" | "completed" | "error" | "preview_ready";
  rowCount: number | null;
  errorCount: number | null;
  errorMessage: string | null;
  uploadedByName: string;
  teamId: string | null;
  teamName: string | null;
  fileSizeKb: number;
  createdAt: string;
  processedAt: string | null;
}

export interface UploadPreviewRow {
  rowIndex: number;
  userId: string;
  userName: string;
  model: string;
  tokens: number;
  cost: number;
  timestamp: string;
  status: "valid" | "error";
  errorReason: string | null;
}

export interface UploadInspectResult {
  headers: string[];
  rowCount: number;
  formatHint: ToolCsvFormatHint;
  suggestedMapping: ToolCsvColumnMapping;
}

export interface UploadPreview {
  uploadId: string;
  fileName: string;
  totalRows: number;
  validRows: number;
  errorRows: number;
  rows: UploadPreviewRow[];
  tokenCount: number;
  costTotal: number;
  dateFrom: string | null;
  dateTo: string | null;
  sourceRowCount: number;
  parseError: string | null;
  needsMapping: boolean;
}

export interface SubmitUploadRequest {
  teamId: string | null;
}

interface BackendUpload {
  id: string;
  file_name: string;
  format: UploadFormat;
  status: UploadRecord["status"];
  row_count: number | null;
  error_count: number | null;
  error_message: string | null;
  uploaded_by_name: string;
  team_id: string | null;
  team_name: string | null;
  file_size_kb: number;
  created_at: string;
  processed_at: string | null;
}

interface BackendUploadInspect {
  headers: string[];
  row_count: number;
  format_hint: ToolCsvFormatHint;
  suggested_mapping: {
    token_column?: string | null;
    cost_column?: string | null;
    date_column?: string | null;
    date_from_column?: string | null;
    date_to_column?: string | null;
  };
}

interface BackendUploadPreview {
  upload_id: string;
  file_name: string;
  total_rows: number;
  valid_rows: number;
  error_rows: number;
  rows: Array<{
    row_index: number;
    user_id: string;
    user_name: string;
    model: string;
    tokens: number;
    cost: number;
    timestamp: string;
    status: "valid" | "error";
    error_reason: string | null;
  }>;
  token_count?: number;
  cost_total?: number;
  date_from?: string | null;
  date_to?: string | null;
  source_row_count?: number;
  parse_error?: string | null;
  needs_mapping?: boolean;
}

function mapUpload(row: BackendUpload): UploadRecord {
  return {
    id: row.id,
    fileName: row.file_name,
    format: row.format,
    status: row.status,
    rowCount: row.row_count,
    errorCount: row.error_count,
    errorMessage: row.error_message,
    uploadedByName: row.uploaded_by_name,
    teamId: row.team_id,
    teamName: row.team_name,
    fileSizeKb: row.file_size_kb,
    createdAt: row.created_at,
    processedAt: row.processed_at,
  };
}

function mapUploadPreview(preview: BackendUploadPreview): UploadPreview {
  return {
    uploadId: preview.upload_id,
    fileName: preview.file_name,
    totalRows: preview.total_rows,
    validRows: preview.valid_rows,
    errorRows: preview.error_rows,
    rows: preview.rows.map((row) => ({
      rowIndex: row.row_index,
      userId: row.user_id,
      userName: row.user_name,
      model: row.model,
      tokens: row.tokens,
      cost: row.cost,
      timestamp: row.timestamp,
      status: row.status,
      errorReason: row.error_reason,
    })),
    tokenCount: preview.token_count ?? 0,
    costTotal: preview.cost_total ?? 0,
    dateFrom: preview.date_from ?? null,
    dateTo: preview.date_to ?? null,
    sourceRowCount: preview.source_row_count ?? 0,
    parseError: preview.parse_error ?? null,
    needsMapping: preview.needs_mapping ?? false,
  };
}

export async function fetchUploads(): Promise<UploadRecord[]> {
  const rows = await apiRequest<BackendUpload[]>("/uploads");
  return rows.map(mapUpload);
}

export async function uploadFile(
  file: File,
  teamId: string | null,
): Promise<UploadRecord> {
  const formData = new FormData();
  formData.append("file", file);
  if (teamId) {
    formData.append("team_id", teamId);
  }
  const created = await apiFormRequest<BackendUpload>("/uploads", formData);
  return mapUpload(created);
}

export async function inspectUpload(id: string): Promise<UploadInspectResult> {
  const response = await apiRequest<BackendUploadInspect>(`/uploads/${id}/inspect`);
  return {
    headers: response.headers,
    rowCount: response.row_count,
    formatHint: response.format_hint,
    suggestedMapping: mapCsvMappingFromBackend(response.suggested_mapping),
  };
}

export async function fetchUploadPreview(id: string): Promise<UploadPreview> {
  const preview = await apiRequest<BackendUploadPreview>(`/uploads/${id}/preview`);
  return mapUploadPreview(preview);
}

export async function previewUploadWithMapping(
  id: string,
  mapping: ToolCsvColumnMapping,
): Promise<UploadPreview> {
  const formData = new FormData();
  appendCsvMappingToFormData(formData, mapping);
  const preview = await apiFormRequest<BackendUploadPreview>(
    `/uploads/${id}/preview`,
    formData,
  );
  return mapUploadPreview(preview);
}

export async function submitUpload(
  id: string,
  body: SubmitUploadRequest,
): Promise<UploadRecord> {
  const formData = new FormData();
  if (body.teamId) {
    formData.append("team_id", body.teamId);
  }
  const updated = await apiFormRequest<BackendUpload>(
    `/uploads/${id}/submit`,
    formData,
  );
  return mapUpload(updated);
}

export async function deleteUpload(id: string): Promise<void> {
  await apiRequest<void>(`/uploads/${id}`, { method: "DELETE" });
}

export const uploadsApi = {
  fetchUploads,
  uploadFile,
  inspectUpload,
  fetchUploadPreview,
  previewUploadWithMapping,
  submitUpload,
  deleteUpload,
};

import { apiFetch, apiRequest, ApiClientError, parseApiError } from "./client";
import {
  mapApiUpload,
  mapApiUploadMapping,
  mapApiUploadPreview,
  type ApiUpload,
  type ApiUploadCreateResponse,
  type ApiUploadMapping,
  type ApiUploadPreview,
} from "./adapters/uploads";

export type UploadFormat = "csv" | "json";

export type UploadStatus =
  | "pending"
  | "mapping"
  | "processing"
  | "completed"
  | "error";

export interface UploadRecord {
  id: string;
  fileName: string;
  format: UploadFormat;
  status: UploadStatus;
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
  /** Original CSV/JSON columns as extracted from the file. */
  rawData?: Record<string, unknown>;
  /** Normalized usage mapped to tool/user fields. */
  mappedData?: Record<string, unknown>;
}

export interface UploadPreview {
  uploadId: string;
  fileName: string;
  teamId: string | null;
  teamName: string | null;
  totalRows: number;
  validRows: number;
  errorRows: number;
  rows: UploadPreviewRow[];
}

export interface SubmitUploadRequest {
  teamId: string | null;
  rowNumbers?: number[];
}

export interface UploadMappingField {
  key: string;
  label: string;
  required: boolean;
}

export interface UploadColumnMapping {
  email?: string | null;
  cost?: string | null;
  model?: string | null;
  input_tokens?: string | null;
  output_tokens?: string | null;
  tokens?: string | null;
  timestamp?: string | null;
  tool?: string | null;
}

export interface UploadMapping {
  uploadId: string;
  fileName: string;
  headers: string[];
  fields: UploadMappingField[];
  suggestedMapping: UploadColumnMapping;
  columnMapping: UploadColumnMapping | null;
  sampleRow: Record<string, unknown>;
}

export type { ApiUpload, ApiUploadPreview, ApiUploadMapping } from "./adapters/uploads";

export async function fetchUploads(): Promise<UploadRecord[]> {
  const rows = await apiRequest<ApiUpload[]>("/uploads");
  return rows.map(mapApiUpload);
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

  const response = await apiFetch("/uploads", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new ApiClientError(await parseApiError(response));
  }

  const payload = (await response.json()) as ApiUploadCreateResponse | ApiUpload;
  const upload =
    "upload" in payload && payload.upload ? payload.upload : (payload as ApiUpload);
  return mapApiUpload(upload);
}

export async function fetchUploadMapping(id: string): Promise<UploadMapping> {
  const mapping = await apiRequest<ApiUploadMapping>(`/uploads/${id}/mapping`);
  return mapApiUploadMapping(mapping);
}

export async function applyUploadMapping(
  id: string,
  mapping: UploadColumnMapping,
): Promise<UploadRecord> {
  const updated = await apiRequest<ApiUpload>(`/uploads/${id}/mapping`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(mapping),
  });
  return mapApiUpload(updated);
}

export async function fetchUploadPreview(id: string): Promise<UploadPreview> {
  const preview = await apiRequest<ApiUploadPreview>(`/uploads/${id}/preview`);
  return mapApiUploadPreview(preview);
}

export async function submitUpload(
  id: string,
  body: SubmitUploadRequest,
): Promise<UploadRecord> {
  const updated = await apiRequest<ApiUpload>(`/uploads/${id}/commit`, {
    method: "POST",
    headers: {
      "Idempotency-Key": crypto.randomUUID(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      team_id: body.teamId,
      row_numbers: body.rowNumbers,
    }),
  });
  return mapApiUpload(updated);
}

export async function deleteUpload(id: string): Promise<void> {
  await apiRequest<void>(`/uploads/${id}`, { method: "DELETE" });
}

export const uploadsApi = {
  fetchUploads,
  uploadFile,
  fetchUploadMapping,
  applyUploadMapping,
  fetchUploadPreview,
  submitUpload,
  deleteUpload,
};

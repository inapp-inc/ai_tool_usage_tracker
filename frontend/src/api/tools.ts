import { apiFormRequest, apiRequest, fetchAllPages } from "./client";
import {
  mapToolCreateToBackend,
  mapToolFromBackend,
  mapToolUpdateToBackend,
  type BackendTool,
} from "./adapters/admin";

export type ToolProvider = string;

export type CollectionSchedule = "hourly" | "daily";

export type PricingModel = "per_token" | "per_seat" | "flat_fee" | "hybrid";

export interface ToolPricing {
  model: PricingModel;
  inputCostPer1K: number | null;
  outputCostPer1K: number | null;
  costPerSeat: number | null;
  seatCount: number | null;
  flatMonthlyCost: number | null;
  planName: string | null;
  includedTokens: number | null;
  overageRate: number | null;
}

export type IngestionSource = "api" | "csv";

export interface AiTool {
  id: string;
  name: string;
  provider: ToolProvider;
  description: string;
  pricing: ToolPricing;
  status: "active" | "inactive" | "error";
  apiKeyMasked: string;
  ingestionSource: IngestionSource;
  lastSyncAt: string | null;
  lastCsvImportAt: string | null;
  collectionSchedule: CollectionSchedule;
  tokenCount: number;
  costTotal: number;
  createdAt: string;
}

export function isCsvImportedTool(tool: AiTool): boolean {
  return tool.ingestionSource === "csv";
}

export interface CreateToolRequest {
  name: string;
  provider: ToolProvider;
  apiKey: string;
  description: string;
  pricing: ToolPricing;
  collectionSchedule: CollectionSchedule;
}

export type UpdateToolRequest = Partial<CreateToolRequest>;

export type ToolCsvImportMode = "create" | "update";

export type ToolCsvFormatHint = "daily" | "summary";

export interface ToolCsvColumnMapping {
  tokenColumn: string;
  costColumn: string;
  dateColumn: string;
  dateFromColumn: string;
  dateToColumn: string;
}

export interface ToolCsvInspectResult {
  headers: string[];
  rowCount: number;
  formatHint: ToolCsvFormatHint;
  suggestedMapping: ToolCsvColumnMapping;
}

export interface ToolCsvDailyUsageRow {
  date: string;
  tokens: number;
  cost: number;
}

export interface ToolCsvImportPreview {
  fileName: string;
  rowCount: number;
  tokenCount: number;
  costTotal: number;
  dateFrom: string | null;
  dateTo: string | null;
  dailyUsage: ToolCsvDailyUsageRow[];
}

export interface ToolCsvImportResult {
  message: string;
  tool: AiTool;
  preview: ToolCsvImportPreview;
}

interface BackendToolCsvPreview {
  file_name: string;
  row_count: number;
  token_count: number;
  cost_total: number;
  date_from: string | null;
  date_to: string | null;
  daily_usage: Array<{ date: string; tokens: number; cost: number }>;
}

function mapCsvPreviewFromBackend(preview: BackendToolCsvPreview): ToolCsvImportPreview {
  return {
    fileName: preview.file_name,
    rowCount: preview.row_count,
    tokenCount: preview.token_count,
    costTotal: preview.cost_total,
    dateFrom: preview.date_from,
    dateTo: preview.date_to,
    dailyUsage: preview.daily_usage.map((row) => ({
      date: row.date,
      tokens: row.tokens,
      cost: row.cost,
    })),
  };
}

interface BackendToolCsvMapping {
  token_column?: string | null;
  cost_column?: string | null;
  date_column?: string | null;
  date_from_column?: string | null;
  date_to_column?: string | null;
}

interface BackendToolCsvInspect {
  headers: string[];
  row_count: number;
  format_hint: ToolCsvFormatHint;
  suggested_mapping: BackendToolCsvMapping;
}

export function mapCsvMappingFromBackend(
  mapping: BackendToolCsvMapping,
): ToolCsvColumnMapping {
  return {
    tokenColumn: mapping.token_column ?? "",
    costColumn: mapping.cost_column ?? "",
    dateColumn: mapping.date_column ?? "",
    dateFromColumn: mapping.date_from_column ?? "",
    dateToColumn: mapping.date_to_column ?? "",
  };
}

export function appendCsvMappingToFormData(
  formData: FormData,
  mapping: ToolCsvColumnMapping,
): void {
  if (mapping.tokenColumn) formData.append("token_column", mapping.tokenColumn);
  if (mapping.costColumn) formData.append("cost_column", mapping.costColumn);
  if (mapping.dateColumn) formData.append("date_column", mapping.dateColumn);
  if (mapping.dateFromColumn) {
    formData.append("date_from_column", mapping.dateFromColumn);
  }
  if (mapping.dateToColumn) formData.append("date_to_column", mapping.dateToColumn);
}

export const EMPTY_CSV_COLUMN_MAPPING: ToolCsvColumnMapping = {
  tokenColumn: "",
  costColumn: "",
  dateColumn: "",
  dateFromColumn: "",
  dateToColumn: "",
};

export async function fetchTools(): Promise<AiTool[]> {
  const rows = await fetchAllPages<BackendTool>("/tools", { limit: 100 });
  return rows.map(mapToolFromBackend);
}

export async function createTool(body: CreateToolRequest): Promise<AiTool> {
  const created = await apiRequest<BackendTool>("/tools", {
    method: "POST",
    body: JSON.stringify(mapToolCreateToBackend(body)),
  });

  if (body.apiKey.trim()) {
    await apiRequest("/credentials", {
      method: "POST",
      body: JSON.stringify({
        tool_id: created.id,
        team_id: null,
        environment: "production",
        secret_value: body.apiKey,
        label: `${body.name} default key`,
        description: body.description,
      }),
    });

    const synced = await syncTool(created.id);
    return synced.tool;
  }

  return mapToolFromBackend(created);
}

export async function updateTool(
  id: string,
  body: UpdateToolRequest,
): Promise<AiTool> {
  const updated = await apiRequest<BackendTool>(`/tools/${id}`, {
    method: "PATCH",
    body: JSON.stringify(mapToolUpdateToBackend(body)),
  });
  return mapToolFromBackend(updated);
}

export async function deleteTool(id: string): Promise<void> {
  await apiRequest<void>(`/tools/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ active: false }),
  });
}

export function mergeSyncedToolIntoList(
  tools: AiTool[],
  synced: AiTool,
): AiTool[] {
  const index = tools.findIndex((tool) => tool.id === synced.id);
  if (index === -1) {
    return [...tools, synced];
  }
  return tools.map((tool) => (tool.id === synced.id ? synced : tool));
}

export async function syncTool(id: string): Promise<{
  valid: boolean;
  message: string;
  tool: AiTool;
}> {
  const response = await apiRequest<{
    valid: boolean;
    message: string;
    tool: BackendTool;
  }>(`/tools/${id}/sync`, { method: "POST" });
  return {
    valid: response.valid,
    message: response.message,
    tool: mapToolFromBackend(response.tool),
  };
}

export async function inspectToolCsvImport(file: File): Promise<ToolCsvInspectResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiFormRequest<BackendToolCsvInspect>(
    "/tools/import-csv/inspect",
    formData,
  );
  return {
    headers: response.headers,
    rowCount: response.row_count,
    formatHint: response.format_hint,
    suggestedMapping: mapCsvMappingFromBackend(response.suggested_mapping),
  };
}

export async function previewToolCsvImport(
  file: File,
  mapping: ToolCsvColumnMapping,
): Promise<ToolCsvImportPreview> {
  const formData = new FormData();
  formData.append("file", file);
  appendCsvMappingToFormData(formData, mapping);
  const preview = await apiFormRequest<BackendToolCsvPreview>(
    "/tools/import-csv/preview",
    formData,
  );
  return mapCsvPreviewFromBackend(preview);
}

export interface ImportToolCsvRequest {
  file: File;
  name: string;
  provider: string;
  mode: ToolCsvImportMode;
  toolId?: string;
  replaceExisting: boolean;
  columnMapping: ToolCsvColumnMapping;
}

export async function importToolCsv(
  body: ImportToolCsvRequest,
): Promise<ToolCsvImportResult> {
  const formData = new FormData();
  formData.append("file", body.file);
  formData.append("name", body.name);
  formData.append("provider", body.provider);
  formData.append("mode", body.mode);
  formData.append("replace_existing", String(body.replaceExisting));
  appendCsvMappingToFormData(formData, body.columnMapping);
  if (body.toolId) {
    formData.append("tool_id", body.toolId);
  }

  const response = await apiFormRequest<{
    message: string;
    tool: BackendTool;
    preview: BackendToolCsvPreview;
  }>("/tools/import-csv", formData);

  return {
    message: response.message,
    tool: mapToolFromBackend(response.tool),
    preview: mapCsvPreviewFromBackend(response.preview),
  };
}

export const toolsApi = {
  fetchTools,
  createTool,
  updateTool,
  deleteTool,
  syncTool,
  inspectToolCsvImport,
  previewToolCsvImport,
  importToolCsv,
};

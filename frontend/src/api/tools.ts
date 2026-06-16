import { apiRequest } from "./client";
import {
  mapApiTool,
  mapApiToolMember,
  toToolFormWriteBody,
  toToolUpdateBodyFromPartial,
  type AiTool,
  type ApiTool,
  type ApiToolMember,
  type ApiToolWriteBody,
  type CreateToolRequest,
  type ToolMember,
  type UpdateToolRequest,
} from "./adapters/tools";

export type {
  AiTool,
  ApiPricingConfig,
  ApiPricingModel,
  ApiTool,
  ApiToolMember,
  ApiToolWriteBody,
  CreateToolRequest,
  PricingModel,
  ToolMember,
  ToolPricing,
  ToolProvider,
  UpdateToolRequest,
} from "./adapters/tools";

export {
  emptyToolPricing,
  normalizePricing,
  toToolFormWriteBody,
  toToolUpdateBodyFromPartial,
} from "./adapters/tools";

export async function fetchTools(): Promise<AiTool[]> {
  const rows = await apiRequest<ApiTool[]>("/tools");
  return rows.map(mapApiTool);
}

export async function createTool(body: CreateToolRequest): Promise<AiTool> {
  const payload = toToolFormWriteBody(body);
  const created = await apiRequest<ApiTool>("/tools", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return mapApiTool(created);
}

export async function updateTool(
  id: string,
  body: UpdateToolRequest,
): Promise<AiTool> {
  const payload = toToolUpdateBodyFromPartial(body);
  const updated = await apiRequest<ApiTool>(`/tools/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return mapApiTool(updated);
}

export async function deleteTool(id: string): Promise<void> {
  await apiRequest<void>(`/tools/${id}`, { method: "DELETE" });
}

export async function syncTool(id: string): Promise<AiTool> {
  const synced = await apiRequest<ApiTool>(`/tools/${id}/sync`, {
    method: "POST",
  });
  return mapApiTool(synced);
}

export async function fetchToolMembers(id: string): Promise<ToolMember[]> {
  const rows = await apiRequest<ApiToolMember[]>(`/tools/${id}/members`);
  return rows.map(mapApiToolMember);
}

export const toolsApi = {
  fetchTools,
  createTool,
  updateTool,
  deleteTool,
  syncTool,
  fetchToolMembers,
};

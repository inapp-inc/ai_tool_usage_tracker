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

export async function fetchToolOptions(): Promise<
  Array<{ id: string; name: string; provider: string }>
> {
  const rows = await apiRequest<
    Array<{ id: string; name: string; vendor: string }>
  >("/tools?active=true&catalogue_only=true");
  return rows.map((row) => ({
    id: row.id,
    name: row.name,
    provider: row.vendor,
  }));
}

/** @deprecated Use fetchToolOptions — catalogue and tool options are the same list. */
export async function fetchCatalogueToolOptions(): Promise<
  Array<{ id: string; name: string; provider: string }>
> {
  return fetchToolOptions();
}

export async function fetchTools(options?: { catalogueOnly?: boolean }): Promise<AiTool[]> {
  const params = new URLSearchParams();
  const catalogueOnly = options?.catalogueOnly ?? true;
  if (catalogueOnly) {
    params.set("catalogue_only", "true");
  } else {
    params.set("catalogue_only", "false");
  }
  const qs = params.toString();
  const rows = await apiRequest<ApiTool[]>(`/tools?${qs}`);
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

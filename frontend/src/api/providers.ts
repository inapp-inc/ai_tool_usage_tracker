import { apiRequest, fetchAllPages } from "./client";

export interface Provider {
  id: string;
  slug: string;
  name: string;
  usageApiUrl: string;
  description: string;
  isSystem: boolean;
  active: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateProviderRequest {
  slug: string;
  name: string;
  usageApiUrl: string;
  description?: string;
}

export interface UpdateProviderRequest {
  name?: string;
  usageApiUrl?: string;
  description?: string;
  active?: boolean;
}

interface BackendProvider {
  id: string;
  slug: string;
  name: string;
  usage_api_url: string;
  description?: string | null;
  is_system: boolean;
  active: boolean;
  created_at: string;
  updated_at: string;
}

function mapProvider(row: BackendProvider): Provider {
  return {
    id: row.id,
    slug: row.slug,
    name: row.name,
    usageApiUrl: row.usage_api_url,
    description: row.description ?? "",
    isSystem: row.is_system,
    active: row.active,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export async function fetchProviders(options?: {
  active?: boolean;
}): Promise<Provider[]> {
  const params: Record<string, string | boolean> = { limit: 100 };
  if (options?.active !== undefined) {
    params.active = options.active;
  }
  const rows = await fetchAllPages<BackendProvider>("/providers", params);
  return rows.map(mapProvider);
}

export async function createProvider(
  body: CreateProviderRequest,
): Promise<Provider> {
  const created = await apiRequest<BackendProvider>("/providers", {
    method: "POST",
    body: JSON.stringify({
      slug: body.slug,
      name: body.name,
      usage_api_url: body.usageApiUrl,
      description: body.description,
    }),
  });
  return mapProvider(created);
}

export async function updateProvider(
  id: string,
  body: UpdateProviderRequest,
): Promise<Provider> {
  const updated = await apiRequest<BackendProvider>(`/providers/${id}`, {
    method: "PATCH",
    body: JSON.stringify({
      name: body.name,
      usage_api_url: body.usageApiUrl,
      description: body.description,
      active: body.active,
    }),
  });
  return mapProvider(updated);
}

export async function deleteProvider(id: string): Promise<void> {
  await apiRequest<void>(`/providers/${id}`, { method: "DELETE" });
}

export interface ValidateProviderResult {
  valid: boolean;
  message: string;
  statusCode?: number | null;
}

export async function validateProviderToken(
  providerSlug: string,
  apiToken: string,
): Promise<ValidateProviderResult> {
  const result = await apiRequest<{
    valid: boolean;
    message: string;
    status_code?: number | null;
  }>("/providers/validate", {
    method: "POST",
    body: JSON.stringify({
      provider_slug: providerSlug,
      api_token: apiToken,
    }),
  });
  return {
    valid: result.valid,
    message: result.message,
    statusCode: result.status_code,
  };
}

export const providersApi = {
  fetchProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  validateProviderToken,
};

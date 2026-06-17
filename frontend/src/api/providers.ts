import { apiRequest } from "./client";

export interface Provider {
  slug: string;
  label: string;
  description?: string | null;
  logo_url?: string | null;
  built_in: boolean;
  active: boolean;
  sort_order: number;
}

export interface CreateProviderRequest {
  slug: string;
  label: string;
  description?: string | null;
  logo_url?: string | null;
  sort_order?: number;
}

export type UpdateProviderRequest = Partial<
  Omit<CreateProviderRequest, "slug"> & { active: boolean }
>;

/** Built-in fallback used when the settings/providers endpoint is unavailable. */
export const BUILT_IN_PROVIDERS: Provider[] = [
  { slug: "openai", label: "OpenAI", built_in: true, active: true, sort_order: 10 },
  { slug: "anthropic", label: "Anthropic", built_in: true, active: true, sort_order: 20 },
  { slug: "google", label: "Google", built_in: true, active: true, sort_order: 30 },
  { slug: "azure_openai", label: "Azure OpenAI", built_in: true, active: true, sort_order: 40 },
  { slug: "cohere", label: "Cohere", built_in: true, active: true, sort_order: 50 },
  { slug: "mistral", label: "Mistral", built_in: true, active: true, sort_order: 60 },
  { slug: "cursor", label: "Cursor", built_in: true, active: true, sort_order: 70 },
  { slug: "mabl", label: "Mabl", built_in: true, active: true, sort_order: 80 },
  { slug: "windsurf", label: "Windsurf", built_in: true, active: true, sort_order: 90 },
  { slug: "figma", label: "Figma", built_in: true, active: true, sort_order: 100 },
  { slug: "custom", label: "Custom", built_in: true, active: true, sort_order: 110 },
];

function unwrapProviderList(
  data: { data: Provider[] } | Provider[],
): Provider[] {
  return Array.isArray(data) ? data : data.data;
}

export async function fetchProviders(activeOnly = true): Promise<Provider[]> {
  const params = activeOnly ? "?active=true" : "";
  const data = await apiRequest<{ data: Provider[] } | Provider[]>(
    `/settings/providers${params}`,
  );
  return unwrapProviderList(data);
}

export async function createProvider(body: CreateProviderRequest): Promise<Provider> {
  return apiRequest<Provider>("/settings/providers", {
    method: "POST",
    body: JSON.stringify({
      slug: body.slug,
      label: body.label,
      description: body.description ?? null,
      logo_url: body.logo_url ?? null,
      sort_order: body.sort_order ?? 0,
    }),
  });
}

export async function updateProvider(
  slug: string,
  body: UpdateProviderRequest,
): Promise<Provider> {
  return apiRequest<Provider>(`/settings/providers/${slug}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deleteProvider(slug: string): Promise<void> {
  await apiRequest<void>(`/settings/providers/${slug}`, { method: "DELETE" });
}

export function providerRequiresApiEndpoint(
  slug: string,
  providers: Provider[],
): boolean {
  if (slug === "custom") {
    return true;
  }
  const provider = providers.find((row) => row.slug === slug);
  if (!provider) {
    return false;
  }
  return !provider.built_in;
}

export const providersApi = {
  fetchProviders,
  createProvider,
  updateProvider,
  deleteProvider,
};

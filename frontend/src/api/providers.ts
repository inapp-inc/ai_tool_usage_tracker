import { apiRequest } from "./client";

export interface ProviderParent {
  slug: string;
  label: string;
  sort_order: number;
}

export const BUILT_IN_PROVIDER_PARENTS: ProviderParent[] = [
  { slug: "openai", label: "OpenAI", sort_order: 10 },
  { slug: "anthropic", label: "Anthropic", sort_order: 20 },
  { slug: "google", label: "Google", sort_order: 30 },
  { slug: "microsoft", label: "Microsoft", sort_order: 40 },
  { slug: "amazon", label: "Amazon", sort_order: 50 },
  { slug: "cursor", label: "Cursor", sort_order: 60 },
  { slug: "figma", label: "Figma", sort_order: 70 },
];

export async function fetchProviderParents(): Promise<ProviderParent[]> {
  const data = await apiRequest<{ data: ProviderParent[] } | ProviderParent[]>(
    "/settings/provider-parents",
  );
  return Array.isArray(data) ? data : data.data;
}

export interface Provider {
  slug: string;
  label: string;
  description?: string | null;
  logo_url?: string | null;
  parent_slug?: string | null;
  parent_label?: string | null;
  adapter_key?: string | null;
  requires_api_endpoint: boolean;
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

/** Built-in fallback when GET /settings/providers is unavailable. */
export const BUILT_IN_PROVIDERS: Provider[] = [
  {
    slug: "openai",
    label: "OpenAI",
    parent_slug: "openai",
    parent_label: "OpenAI",
    adapter_key: "openai",
    requires_api_endpoint: false,
    built_in: true,
    active: true,
    sort_order: 10,
  },
  {
    slug: "anthropic",
    label: "Anthropic Claude",
    parent_slug: "anthropic",
    parent_label: "Anthropic",
    adapter_key: "anthropic",
    requires_api_endpoint: false,
    built_in: true,
    active: true,
    sort_order: 20,
  },
  {
    slug: "google",
    label: "Google Gemini",
    parent_slug: "google",
    parent_label: "Google",
    adapter_key: "google",
    requires_api_endpoint: false,
    built_in: true,
    active: true,
    sort_order: 30,
  },
  {
    slug: "azure_openai",
    label: "Azure OpenAI Platform",
    parent_slug: "microsoft",
    parent_label: "Microsoft",
    adapter_key: "azure_openai",
    requires_api_endpoint: true,
    built_in: true,
    active: true,
    sort_order: 40,
  },
  {
    slug: "copilot",
    label: "Microsoft Copilot",
    parent_slug: "microsoft",
    parent_label: "Microsoft",
    adapter_key: "copilot",
    requires_api_endpoint: false,
    built_in: true,
    active: true,
    sort_order: 50,
  },
  {
    slug: "bedrock",
    label: "Amazon Bedrock",
    parent_slug: "amazon",
    parent_label: "Amazon",
    adapter_key: "bedrock",
    requires_api_endpoint: true,
    built_in: true,
    active: true,
    sort_order: 60,
  },
  {
    slug: "cursor",
    label: "Cursor",
    parent_slug: "cursor",
    parent_label: "Cursor",
    adapter_key: "cursor",
    requires_api_endpoint: false,
    built_in: true,
    active: true,
    sort_order: 70,
  },
  {
    slug: "figma",
    label: "Figma",
    parent_slug: "figma",
    parent_label: "Figma",
    adapter_key: "figma",
    requires_api_endpoint: false,
    built_in: true,
    active: true,
    sort_order: 80,
  },
  {
    slug: "custom",
    label: "Custom Integration",
    adapter_key: "custom",
    requires_api_endpoint: true,
    built_in: true,
    active: true,
    sort_order: 200,
  },
];

export interface ProviderOptionGroup {
  parentLabel: string;
  providers: Provider[];
}

export function groupProvidersByParent(providers: Provider[]): ProviderOptionGroup[] {
  const sorted = [...providers].sort((a, b) => a.sort_order - b.sort_order);
  const groups = new Map<string, Provider[]>();

  for (const provider of sorted) {
    const key = provider.parent_label ?? provider.label;
    const bucket = groups.get(key);
    if (bucket) {
      bucket.push(provider);
    } else {
      groups.set(key, [provider]);
    }
  }

  return Array.from(groups.entries()).map(([parentLabel, items]) => ({
    parentLabel,
    providers: items,
  }));
}

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

export function providerRequiresOrganizationId(slug: string): boolean {
  return slug === "copilot";
}

export function providerRequiresOpenAiAdminKey(slug: string): boolean {
  return slug === "openai";
}

export function providerRequiresAnthropicAdminKey(slug: string): boolean {
  return slug === "anthropic";
}

export function providerRequiresGcpMonitoring(slug: string): boolean {
  return slug === "google";
}

export function providerRequiresApiEndpoint(
  slug: string,
  providers: Provider[],
): boolean {
  const provider = providers.find((row) => row.slug === slug);
  if (provider) {
    return provider.requires_api_endpoint;
  }
  const fallback = BUILT_IN_PROVIDERS.find((row) => row.slug === slug);
  return fallback?.requires_api_endpoint ?? slug === "custom";
}

export const providersApi = {
  fetchProviders,
  fetchProviderParents,
  createProvider,
  updateProvider,
  deleteProvider,
};

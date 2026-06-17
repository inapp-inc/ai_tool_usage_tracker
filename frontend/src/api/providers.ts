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

/** Built-in fallback used when the settings/providers endpoint is unavailable. */
export const BUILT_IN_PROVIDERS: Provider[] = [
  { slug: "openai",       label: "OpenAI",       built_in: true, active: true, sort_order: 10 },
  { slug: "anthropic",    label: "Anthropic",    built_in: true, active: true, sort_order: 20 },
  { slug: "google",       label: "Google",       built_in: true, active: true, sort_order: 30 },
  { slug: "azure_openai", label: "Azure OpenAI", built_in: true, active: true, sort_order: 40 },
  { slug: "cohere",       label: "Cohere",       built_in: true, active: true, sort_order: 50 },
  { slug: "mistral",      label: "Mistral",      built_in: true, active: true, sort_order: 60 },
  { slug: "cursor",       label: "Cursor",       built_in: true, active: true, sort_order: 70 },
  { slug: "mabl",         label: "Mabl",         built_in: true, active: true, sort_order: 80 },
  { slug: "windsurf",     label: "Windsurf",     built_in: true, active: true, sort_order: 90 },
  { slug: "figma",        label: "Figma",        built_in: true, active: true, sort_order: 100 },
  { slug: "custom",       label: "Custom",       built_in: true, active: true, sort_order: 110 },
];

export async function fetchProviders(activeOnly = true): Promise<Provider[]> {
  const params = activeOnly ? "?active=true" : "";
  const data = await apiRequest<{ data: Provider[] } | Provider[]>(
    `/settings/providers${params}`,
  );
  const rows = Array.isArray(data) ? data : data.data;
  return rows;
}

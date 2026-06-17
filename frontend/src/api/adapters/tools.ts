/** Maps OpenAPI Tool responses to frontend AiTool shape (mirrors teams adapter). */

export type ToolProvider =
  | "openai"
  | "anthropic"
  | "google"
  | "azure_openai"
  | "cohere"
  | "mistral"
  | "custom"
  | "mabl"
  | "windsurf"
  | "cursor"
  | "figma";

export type PricingModel = "per_token" | "per_seat" | "flat_fee" | "hybrid";

/** OpenAPI pricing_model enum */
export type ApiPricingModel = "flat_token" | "package_with_overage" | "custom";

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

export interface AiTool {
  id: string;
  name: string;
  provider: ToolProvider;
  description: string;
  apiEndpoint: string | null;
  pricing: ToolPricing;
  status: "active" | "inactive" | "error";
  apiKeyMasked: string;
  lastSyncAt: string | null;
  tokenCount: number;
  costTotal: number;
  balanceTokens: number | null;
  memberCount: number;
  createdAt: string;
}

export interface ToolMember {
  email: string;
  name: string | null;
}

/** Frontend form / page payload (camelCase). */
export interface CreateToolRequest {
  name: string;
  provider: ToolProvider;
  description: string;
  apiEndpoint?: string | null;
  pricing: ToolPricing;
}

export type UpdateToolRequest = Partial<CreateToolRequest>;

/** OpenAPI pricing_config JSON (snake_case). */
export interface ApiPricingConfig {
  model?: PricingModel | string;
  provider_slug?: string;
  input_cost_per_1k?: number | null;
  output_cost_per_1k?: number | null;
  cost_per_seat?: number | null;
  seat_count?: number | null;
  flat_monthly_cost?: number | null;
  plan_name?: string | null;
  included_tokens?: number | null;
  overage_rate?: number | null;
}

/** OpenAPI POST/PATCH /tools body (snake_case, flat pricing fields). */
export interface ApiToolWriteBody {
  name: string;
  vendor: string;
  description: string;
  api_endpoint?: string | null;
  pricing_model: ApiPricingModel;
  token_price: number;
  package_allowance: number | null;
  overage_price: number | null;
  pricing_config: ApiPricingConfig;
}

export interface ApiToolPricingFields {
  pricing_model: ApiPricingModel;
  token_price: number;
  package_allowance: number | null;
  overage_price: number | null;
  pricing_config: ApiPricingConfig;
}

/** OpenAPI GET /tools response item (snake_case). */
export interface ApiTool {
  id: string;
  organization_id: string;
  name: string;
  vendor: string;
  description?: string | null;
  api_endpoint?: string | null;
  pricing_model: ApiPricingModel | string;
  token_price: number | string;
  package_allowance?: number | null;
  overage_price?: number | string | null;
  pricing_config?: ApiPricingConfig;
  active: boolean;
  api_token_masked: string;
  token_count: number;
  cost_total: number | string;
  balance_tokens?: number | null;
  member_count?: number;
  sync_status: "active" | "inactive" | "error";
  last_sync_at?: string | null;
  last_sync_error?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface ApiToolMember {
  email: string;
  name?: string | null;
}

const VENDOR_TO_PROVIDER: Record<string, ToolProvider> = {
  openai: "openai",
  anthropic: "anthropic",
  google: "google",
  azure_openai: "azure_openai",
  cohere: "cohere",
  mistral: "mistral",
  custom: "custom",
  mabl: "mabl",
  windsurf: "windsurf",
  cursor: "cursor",
  figma: "figma",
};

export function emptyToolPricing(): ToolPricing {
  return {
    model: "per_token",
    inputCostPer1K: null,
    outputCostPer1K: null,
    costPerSeat: null,
    seatCount: null,
    flatMonthlyCost: null,
    planName: null,
    includedTokens: null,
    overageRate: null,
  };
}

function toNumber(value: number | string | null | undefined): number {
  if (value == null || value === "") {
    return 0;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function providerFromVendor(vendor: string, config?: ApiPricingConfig): ToolProvider {
  const slug = config?.provider_slug ?? vendor;
  const normalized = slug.trim().toLowerCase().replace(/\s+/g, "_");
  return VENDOR_TO_PROVIDER[normalized] ?? "custom";
}

function pricingFromApi(tool: ApiTool): ToolPricing {
  const config = tool.pricing_config ?? {};
  const frontendModel =
    (config.model as PricingModel | undefined) ?? inferPricingModel(tool.pricing_model);

  return {
    model: frontendModel,
    inputCostPer1K: toNullableNumber(config.input_cost_per_1k ?? tool.token_price),
    outputCostPer1K: toNullableNumber(config.output_cost_per_1k),
    costPerSeat: toNullableNumber(config.cost_per_seat),
    seatCount: toNullableNumber(config.seat_count),
    flatMonthlyCost: toNullableNumber(config.flat_monthly_cost),
    planName: normalizePlanName(
      config.plan_name == null ? null : String(config.plan_name),
    ),
    includedTokens: toNullableNumber(tool.package_allowance ?? config.included_tokens),
    overageRate: toNullableNumber(tool.overage_price ?? config.overage_rate),
  };
}

function inferPricingModel(apiModel: string): PricingModel {
  if (apiModel === "flat_token") {
    return "per_token";
  }
  if (apiModel === "package_with_overage") {
    return "flat_fee";
  }
  return "per_token";
}

export function toNullableNumber(value: unknown): number | null {
  if (value == null || value === "") {
    return null;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function normalizePlanName(value: string | null | undefined): string | null {
  if (value == null) {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

/** Normalize form pricing before mapping to OpenAPI fields. */
export function normalizePricing(pricing: ToolPricing): ToolPricing {
  return {
    ...pricing,
    inputCostPer1K: toNullableNumber(pricing.inputCostPer1K),
    outputCostPer1K: toNullableNumber(pricing.outputCostPer1K),
    costPerSeat: toNullableNumber(pricing.costPerSeat),
    seatCount: toNullableNumber(pricing.seatCount),
    flatMonthlyCost: toNullableNumber(pricing.flatMonthlyCost),
    planName: normalizePlanName(
      pricing.planName == null ? null : String(pricing.planName),
    ),
    includedTokens: toNullableNumber(pricing.includedTokens),
    overageRate: toNullableNumber(pricing.overageRate),
  };
}

function hasPackageInput(pricing: ToolPricing): boolean {
  return (
    pricing.planName != null ||
    pricing.includedTokens != null ||
    pricing.overageRate != null ||
    pricing.flatMonthlyCost != null
  );
}

function packagePricingConfig(
  pricing: ToolPricing,
  providerSlug: ToolProvider,
  model: PricingModel,
): ApiPricingConfig {
  return {
    model,
    provider_slug: providerSlug,
    flat_monthly_cost: pricing.flatMonthlyCost,
    plan_name: pricing.planName,
    included_tokens: pricing.includedTokens,
    overage_rate: pricing.overageRate,
    input_cost_per_1k: pricing.inputCostPer1K,
    output_cost_per_1k: pricing.outputCostPer1K,
    cost_per_seat: pricing.costPerSeat,
    seat_count: pricing.seatCount,
  };
}

function withExplicitPackageFields(
  fields: ApiToolPricingFields,
  pricing: ToolPricing,
): ApiToolPricingFields {
  const config: ApiPricingConfig = {
    ...fields.pricing_config,
    plan_name: pricing.planName,
    included_tokens: pricing.includedTokens,
    overage_rate: pricing.overageRate,
    flat_monthly_cost: pricing.flatMonthlyCost ?? fields.pricing_config.flat_monthly_cost ?? null,
  };

  return {
    ...fields,
    package_allowance: pricing.includedTokens,
    overage_price: pricing.overageRate,
    pricing_config: config,
  };
}

function statusFromApi(tool: ApiTool): AiTool["status"] {
  if (!tool.active) {
    return "inactive";
  }
  if (tool.sync_status === "error") {
    return "error";
  }
  return "active";
}

export function mapApiTool(api: ApiTool): AiTool {
  return {
    id: api.id,
    name: api.name,
    provider: providerFromVendor(api.vendor, api.pricing_config),
    description: api.description ?? "",
    apiEndpoint: api.api_endpoint ?? null,
    pricing: pricingFromApi(api),
    status: statusFromApi(api),
    apiKeyMasked: api.api_token_masked,
    lastSyncAt: api.last_sync_at ?? null,
    tokenCount: api.token_count,
    costTotal: toNumber(api.cost_total),
    balanceTokens: api.balance_tokens ?? null,
    memberCount: api.member_count ?? 0,
    createdAt: api.created_at,
  };
}

export function mapApiToolMember(api: ApiToolMember): ToolMember {
  return {
    email: api.email,
    name: api.name ?? null,
  };
}

/** Map frontend pricing → OpenAPI flat pricing fields. */
export function pricingToApiFields(
  pricing: ToolPricing,
  providerSlug: ToolProvider,
): ApiToolPricingFields {
  const normalized = normalizePricing(pricing);
  const usePackagePricing =
    normalized.model === "flat_fee" ||
    normalized.model === "hybrid" ||
    (hasPackageInput(normalized) &&
      normalized.includedTokens != null &&
      normalized.overageRate != null);

  if (usePackagePricing) {
    const model =
      normalized.model === "hybrid"
        ? "hybrid"
        : normalized.model === "flat_fee"
          ? "flat_fee"
          : "flat_fee";

    return withExplicitPackageFields(
      {
        pricing_model: "package_with_overage",
        token_price: normalized.overageRate ?? normalized.inputCostPer1K ?? 0,
        package_allowance: normalized.includedTokens,
        overage_price: normalized.overageRate,
        pricing_config: packagePricingConfig(normalized, providerSlug, model),
      },
      normalized,
    );
  }

  if (normalized.model === "per_token") {
    const fields: ApiToolPricingFields = {
      pricing_model: "flat_token",
      token_price: normalized.inputCostPer1K ?? 0,
      package_allowance: null,
      overage_price: null,
      pricing_config: {
        model: "per_token",
        provider_slug: providerSlug,
        input_cost_per_1k: normalized.inputCostPer1K,
        output_cost_per_1k: normalized.outputCostPer1K,
        plan_name: null,
        included_tokens: null,
        overage_rate: null,
      },
    };

    if (hasPackageInput(normalized)) {
      return withExplicitPackageFields(fields, normalized);
    }

    return fields;
  }

  return withExplicitPackageFields(
    {
      pricing_model: "custom",
      token_price: 0,
      package_allowance: normalized.includedTokens,
      overage_price: normalized.overageRate,
      pricing_config: packagePricingConfig(normalized, providerSlug, normalized.model),
    },
    normalized,
  );
}

/** Ensure PATCH/POST JSON always includes package columns (null when unset). */
export function finalizeWriteBody(body: ApiToolWriteBody): ApiToolWriteBody {
  return {
    ...body,
    package_allowance: body.package_allowance ?? null,
    overage_price: body.overage_price ?? null,
    pricing_config: {
      ...body.pricing_config,
      plan_name: body.pricing_config.plan_name ?? null,
      included_tokens: body.pricing_config.included_tokens ?? null,
      overage_rate: body.pricing_config.overage_rate ?? null,
    },
  };
}

/** Full OpenAPI write body for create (and update). */
export function toToolWriteBody(body: CreateToolRequest): ApiToolWriteBody {
  const pricing = pricingToApiFields(normalizePricing(body.pricing), body.provider);

  return finalizeWriteBody({
    name: body.name,
    vendor: body.provider,
    description: body.description,
    api_endpoint: body.apiEndpoint ?? null,
    pricing_model: pricing.pricing_model,
    token_price: pricing.token_price,
    package_allowance: pricing.package_allowance,
    overage_price: pricing.overage_price,
    pricing_config: pricing.pricing_config,
  });
}

export const toToolCreateBody = toToolWriteBody;

/** Full OpenAPI write body for update. */
export function toToolUpdateBody(body: CreateToolRequest): ApiToolWriteBody {
  return toToolWriteBody(body);
}

/** Build update body from partial form state (mirrors teams adapter). */
export function toToolUpdateBodyFromPartial(body: UpdateToolRequest): ApiToolWriteBody {
  return toToolUpdateBody({
    name: body.name ?? "",
    provider: body.provider ?? "custom",
    description: body.description ?? "",
    apiEndpoint: body.apiEndpoint ?? null,
    pricing: normalizePricing(body.pricing ?? emptyToolPricing()),
  });
}

/** Full write payload for create/update forms (explicit, like teams). */
export function toToolFormWriteBody(body: CreateToolRequest): ApiToolWriteBody {
  return toToolWriteBody(body);
}

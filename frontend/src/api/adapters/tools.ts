/** Maps OpenAPI Tool responses to frontend AiTool shape (mirrors teams adapter). */

export type ToolProvider =
  | "openai"
  | "anthropic"
  | "google"
  | "azure_openai"
  | "copilot"
  | "bedrock"
  | "cursor"
  | "figma"
  | "custom";

export type PricingModel = "per_token" | "per_seat" | "flat_fee" | "hybrid" | "per_team";

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
  organizationId: string | null;
  parentSlug: string | null;
  /** Figma: monthly view/collab seat cost (USD). */
  viewSeatCostUsd?: number | null;
  /** Figma: USD per paid credit (e.g. 0.03 from $30 per 1000 credits). Stored as credits_per_usd. */
  creditsPerUsd?: number | null;
  /** Figma: AI credits included per paid seat in the subscription package. */
  includedCreditsPerSeat?: number | null;
}

import type { ToolIntegrationConfig } from "@/types/integrationConfig";

export type BillingType =
  | "TOKEN_BASED"
  | "REQUEST_BASED"
  | "CREDIT_BASED"
  | "SEAT_BASED"
  | "LICENSE_BASED";

export interface AiTool {
  id: string;
  organizationId: string;
  name: string;
  provider: ToolProvider;
  billingType: BillingType;
  parentSlug: string | null;
  parentLabel: string | null;
  productLabel: string | null;
  description: string;
  apiEndpoint: string | null;
  integrationConfig: ToolIntegrationConfig | null;
  pricing: ToolPricing;
  status: "active" | "inactive" | "error";
  builtIn: boolean;
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
  integrationConfig?: ToolIntegrationConfig | null;
  pricing: ToolPricing;
}

export type UpdateToolRequest = Partial<CreateToolRequest>;

/** OpenAPI pricing_config JSON (snake_case). */
export interface ApiPricingConfig {
  model?: PricingModel | string;
  provider_slug?: string;
  organization_id?: string | null;
  parent_slug?: string | null;
  input_cost_per_1k?: number | null;
  output_cost_per_1k?: number | null;
  cost_per_seat?: number | null;
  seat_count?: number | null;
  flat_monthly_cost?: number | null;
  cost_per_team?: number | null;
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
  integration_config?: ApiToolIntegrationConfig;
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
export interface ApiToolIntegrationConfig {
  version?: number;
  auth?: {
    type?: string;
    header?: string;
    prefix?: string;
  };
  headers?: Record<string, string>;
  usage?: {
    method?: string;
    url?: string;
    query?: Record<string, string>;
    response?: {
      type?: string;
      records_path?: string;
      fields?: Record<string, string>;
    };
  };
}

/** OpenAPI GET /tools response item (snake_case). */
export interface ApiTool {
  id: string;
  organization_id: string;
  name: string;
  vendor: string;
  billing_type?: BillingType | string;
  description?: string | null;
  api_endpoint?: string | null;
  integration_config?: ApiToolIntegrationConfig;
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
  built_in?: boolean;
  parent_slug?: string | null;
  parent_label?: string | null;
  product_label?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface ApiToolMember {
  email: string;
  name?: string | null;
}

export interface ApiToolPackage {
  id: string;
  tool_id: string;
  package_name: string;
  billing_type: BillingType | string;
  monthly_price: number | string | null;
  yearly_price: number | string | null;
  seat_limit: number | null;
  token_limit: number | null;
  request_limit: number | null;
  credit_limit: number | string | null;
  currency: string;
  is_active: boolean;
}

export interface ToolPackage {
  id: string;
  toolId: string;
  packageName: string;
  billingType: BillingType;
  monthlyPrice: number | null;
  yearlyPrice: number | null;
  seatLimit: number | null;
  tokenLimit: number | null;
  requestLimit: number | null;
  creditLimit: number | null;
  currency: string;
  isActive: boolean;
}

function billingTypeFromApi(value: string | undefined): BillingType {
  const normalized = (value ?? "TOKEN_BASED").toUpperCase();
  if (
    normalized === "TOKEN_BASED" ||
    normalized === "REQUEST_BASED" ||
    normalized === "CREDIT_BASED" ||
    normalized === "SEAT_BASED" ||
    normalized === "LICENSE_BASED"
  ) {
    return normalized;
  }
  return "TOKEN_BASED";
}

export function mapApiToolPackage(api: ApiToolPackage): ToolPackage {
  return {
    id: api.id,
    toolId: api.tool_id,
    packageName: api.package_name,
    billingType: billingTypeFromApi(api.billing_type),
    monthlyPrice: toNullableNumber(api.monthly_price),
    yearlyPrice: toNullableNumber(api.yearly_price),
    seatLimit: api.seat_limit,
    tokenLimit: api.token_limit,
    requestLimit: api.request_limit,
    creditLimit: toNullableNumber(api.credit_limit),
    currency: api.currency,
    isActive: api.is_active,
  };
}

export function packageAllowanceFromPackage(pkg: ToolPackage): number | null {
  if (pkg.billingType === "TOKEN_BASED") {
    return pkg.tokenLimit;
  }
  if (pkg.billingType === "REQUEST_BASED") {
    return pkg.requestLimit;
  }
  if (pkg.billingType === "CREDIT_BASED") {
    return pkg.creditLimit == null ? null : Math.trunc(pkg.creditLimit);
  }
  return null;
}

export function defaultCopilotPricingModel(pkg: ToolPackage): PricingModel {
  const name = pkg.packageName.toLowerCase();
  if (name.includes("credit")) {
    return "per_seat";
  }
  if (name.includes("business")) {
    return "per_seat";
  }
  if (pkg.billingType === "LICENSE_BASED") {
    return "per_team";
  }
  if (name.includes("enterprise")) {
    return "per_team";
  }
  if (pkg.billingType === "SEAT_BASED") {
    return "per_seat";
  }
  if (pkg.billingType === "CREDIT_BASED") {
    return "per_seat";
  }
  return "per_team";
}

export function pricingFromPackage(
  pkg: ToolPackage,
  vendor?: ToolProvider,
): Partial<ToolPricing> {
  if (vendor === "copilot" && pkg.billingType === "CREDIT_BASED") {
    return {
      planName: pkg.packageName,
      model: "per_seat",
      costPerSeat: null,
      seatCount: 1,
      flatMonthlyCost: null,
      includedTokens: null,
      overageRate: null,
    };
  }
  if (vendor === "copilot" && pkg.billingType !== "CREDIT_BASED") {
    const model = defaultCopilotPricingModel(pkg);
    if (model === "per_team") {
      return {
        planName: pkg.packageName,
        model: "per_team",
        flatMonthlyCost: pkg.monthlyPrice,
        seatCount: pkg.seatLimit ?? 1,
        costPerSeat: null,
        includedTokens: null,
        overageRate: null,
      };
    }
    return {
      planName: pkg.packageName,
      model: "per_seat",
      costPerSeat: pkg.monthlyPrice,
      seatCount: pkg.seatLimit ?? 1,
      flatMonthlyCost: null,
      includedTokens: null,
      overageRate: null,
    };
  }
  if (pkg.billingType === "SEAT_BASED") {
    return {
      planName: pkg.packageName,
      model: "per_seat",
      costPerSeat: pkg.monthlyPrice,
      seatCount: pkg.seatLimit ?? 1,
      flatMonthlyCost: null,
      includedTokens: null,
      overageRate: null,
    };
  }
  if (pkg.billingType === "CREDIT_BASED") {
    return {
      planName: pkg.packageName,
      model: "flat_fee",
      flatMonthlyCost: null,
      includedTokens: null,
      overageRate: null,
    };
  }
  const patch: Partial<ToolPricing> = {
    planName: pkg.packageName,
    flatMonthlyCost: pkg.monthlyPrice,
  };
  const allowance = packageAllowanceFromPackage(pkg);
  return {
    ...patch,
    model: allowance != null ? "flat_fee" : "per_token",
    includedTokens: allowance,
  };
}

const VENDOR_TO_PROVIDER: Record<string, ToolProvider> = {
  openai: "openai",
  anthropic: "anthropic",
  google: "google",
  azure_openai: "azure_openai",
  copilot: "copilot",
  github_copilot: "copilot",
  github: "copilot",
  bedrock: "bedrock",
  custom: "custom",
  cursor: "cursor",
  figma: "figma",
};

export function isCopilotProvider(provider: ToolProvider | string | null | undefined): boolean {
  if (!provider) {
    return false;
  }
  const normalized = provider.trim().toLowerCase().replace(/\s+/g, "_");
  return normalized === "copilot" || normalized === "github_copilot" || normalized === "github";
}

export function isFigmaProvider(provider: ToolProvider | string | null | undefined): boolean {
  if (!provider) {
    return false;
  }
  return provider.trim().toLowerCase().replace(/\s+/g, "_") === "figma";
}

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
    organizationId: null,
    parentSlug: null,
    viewSeatCostUsd: null,
    creditsPerUsd: null,
    includedCreditsPerSeat: null,
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
    organizationId:
      typeof config.organization_id === "string" && config.organization_id.trim()
        ? config.organization_id.trim()
        : null,
    parentSlug:
      typeof config.parent_slug === "string" && config.parent_slug.trim()
        ? config.parent_slug.trim()
        : null,
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
    organizationId:
      typeof pricing.organizationId === "string" && pricing.organizationId.trim()
        ? pricing.organizationId.trim()
        : null,
    parentSlug:
      typeof pricing.parentSlug === "string" && pricing.parentSlug.trim()
        ? pricing.parentSlug.trim()
        : null,
    viewSeatCostUsd: toNullableNumber(pricing.viewSeatCostUsd),
    creditsPerUsd: toNullableNumber(pricing.creditsPerUsd),
    includedCreditsPerSeat: toNullableNumber(pricing.includedCreditsPerSeat),
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
    cost_per_team:
      model === "per_team" ? pricing.flatMonthlyCost : null,
    plan_name: pricing.planName,
    included_tokens: pricing.includedTokens,
    overage_rate: pricing.overageRate,
    input_cost_per_1k: pricing.inputCostPer1K,
    output_cost_per_1k: pricing.outputCostPer1K,
    cost_per_seat: pricing.costPerSeat,
    seat_count: pricing.seatCount,
    organization_id: pricing.organizationId,
    parent_slug: pricing.parentSlug,
    view_seat_cost_usd: pricing.viewSeatCostUsd,
    credits_per_usd: pricing.creditsPerUsd,
    credit_amount: pricing.creditsPerUsd,
    included_credits_per_seat: pricing.includedCreditsPerSeat,
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

function mapIntegrationConfig(
  raw: ApiToolIntegrationConfig | undefined,
): ToolIntegrationConfig | null {
  if (!raw?.usage?.url) {
    return null;
  }
  return raw as ToolIntegrationConfig;
}

export function mapApiTool(api: ApiTool): AiTool {
  return {
    id: api.id,
    organizationId: api.organization_id,
    name: api.name,
    provider: providerFromVendor(api.vendor, api.pricing_config),
    billingType: billingTypeFromApi(api.billing_type),
    parentSlug: api.parent_slug ?? null,
    parentLabel: api.parent_label ?? null,
    productLabel: api.product_label ?? null,
    description: api.description ?? "",
    apiEndpoint: api.api_endpoint ?? null,
    integrationConfig: mapIntegrationConfig(api.integration_config),
    pricing: pricingFromApi(api),
    status: statusFromApi(api),
    builtIn: Boolean(api.built_in),
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

  if (normalized.model === "per_seat") {
    return withExplicitPackageFields(
      {
        pricing_model: "custom",
        token_price: 0,
        package_allowance: null,
        overage_price: null,
        pricing_config: packagePricingConfig(normalized, providerSlug, "per_seat"),
      },
      { ...normalized, includedTokens: null, overageRate: null },
    );
  }

  if (normalized.model === "per_team") {
    return withExplicitPackageFields(
      {
        pricing_model: "custom",
        token_price: 0,
        package_allowance: null,
        overage_price: null,
        pricing_config: packagePricingConfig(normalized, providerSlug, "per_team"),
      },
      { ...normalized, costPerSeat: null, includedTokens: null, overageRate: null },
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
        organization_id: normalized.organizationId,
        parent_slug: normalized.parentSlug,
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
    integration_config: body.integrationConfig ?? {},
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
    integrationConfig: body.integrationConfig ?? null,
    pricing: normalizePricing(body.pricing ?? emptyToolPricing()),
  });
}

/** Full write payload for create/update forms (explicit, like teams). */
export function toToolFormWriteBody(body: CreateToolRequest): ApiToolWriteBody {
  return toToolWriteBody(body);
}

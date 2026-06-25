import {
  emptyToolPricing,
  normalizePricing,
  pricingToApiFields,
  toNullableNumber,
  type ApiPricingConfig,
  type ApiPricingModel,
  type PricingModel,
  type ToolPricing,
  type ToolProvider,
} from "./tools";

export interface TeamToolPackageBinding {
  packageId: string | null;
  subscriptionStart: string | null;
  subscriptionEnd: string | null;
  monthlyBudget: number | null;
  alertThreshold: number | null;
  alertThresholdUsd: number | null;
  billingType: string | null;
}

export interface ApiTeamToolAssignment {
  id: string;
  team_id: string;
  tool_id: string;
  tool_name: string;
  pricing_model: ApiPricingModel | string | null;
  token_price: number | string | null;
  output_token_price: number | string | null;
  cost_per_seat: number | string | null;
  seat_count: number | null;
  package_allowance: number | null;
  overage_price: number | string | null;
  plan_name: string | null;
  pricing_config?: ApiPricingConfig;
  package_id?: string | null;
  subscription_start?: string | null;
  subscription_end?: string | null;
  monthly_budget?: number | string | null;
  alert_threshold?: number | string | null;
  alert_threshold_usd?: number | string | null;
  created_at: string;
  updated_at: string;
}

export interface TeamToolAssignment {
  id: string;
  teamId: string;
  toolId: string;
  toolName: string;
  pricing: ToolPricing;
  package: TeamToolPackageBinding;
  createdAt: string;
  updatedAt: string;
}

export interface TeamToolAssignBody {
  toolId: string;
  pricing: ToolPricing;
  provider?: ToolProvider;
  package?: TeamToolPackageBinding;
}

export function emptyTeamToolPackageBinding(): TeamToolPackageBinding {
  return {
    packageId: null,
    subscriptionStart: null,
    subscriptionEnd: null,
    monthlyBudget: null,
    alertThreshold: null,
    alertThresholdUsd: null,
    billingType: null,
  };
}

function isCopilotCreditPlan(planName: string | null | undefined): boolean {
  return (planName ?? "").toLowerCase().includes("credit");
}

function packageFromApi(
  api: ApiTeamToolAssignment,
  provider?: ToolProvider,
): TeamToolPackageBinding {
  const pricing = pricingFromTeamToolAssignment(api, provider);
  let billingType: string | null = null;
  if (provider === "copilot") {
    billingType = isCopilotCreditPlan(api.plan_name) ? "CREDIT_BASED" : "SEAT_BASED";
  } else if (pricing.model === "per_seat") {
    billingType = "SEAT_BASED";
  } else if (
    api.package_id &&
    pricing.includedTokens == null &&
    pricing.model === "flat_fee"
  ) {
    billingType = "CREDIT_BASED";
  }
  return {
    packageId: api.package_id ?? null,
    subscriptionStart: api.subscription_start ?? null,
    subscriptionEnd: api.subscription_end ?? null,
    monthlyBudget: toNullableNumber(api.monthly_budget),
    alertThreshold: toNullableNumber(api.alert_threshold),
    alertThresholdUsd: toNullableNumber(api.alert_threshold_usd),
    billingType,
  };
}

function packageToApiFields(
  binding: TeamToolPackageBinding | undefined,
): Record<string, unknown> {
  const pkg = binding ?? emptyTeamToolPackageBinding();
  return {
    package_id: pkg.packageId,
    subscription_start: pkg.subscriptionStart || null,
    subscription_end: pkg.subscriptionEnd || null,
    monthly_budget: pkg.monthlyBudget,
    alert_threshold: pkg.alertThreshold,
    alert_threshold_usd: pkg.alertThresholdUsd,
  };
}

function inferPricingModel(apiModel: string | null): PricingModel {
  if (apiModel === "flat_token") {
    return "per_token";
  }
  if (apiModel === "package_with_overage") {
    return "flat_fee";
  }
  if (apiModel === "custom") {
    return "per_seat";
  }
  return "per_token";
}

export function pricingFromTeamToolAssignment(
  api: ApiTeamToolAssignment,
  provider?: ToolProvider,
): ToolPricing {
  const config = api.pricing_config ?? {};
  const frontendModel =
    (config.model as PricingModel | undefined) ??
    inferPricingModel(api.pricing_model);

  let pricing = normalizePricing({
    model: frontendModel,
    inputCostPer1K: toNullableNumber(config.input_cost_per_1k ?? api.token_price),
    outputCostPer1K: toNullableNumber(config.output_cost_per_1k ?? api.output_token_price),
    costPerSeat: toNullableNumber(config.cost_per_seat ?? api.cost_per_seat),
    seatCount: toNullableNumber(config.seat_count ?? api.seat_count),
    flatMonthlyCost: toNullableNumber(
      config.cost_per_team ?? config.flat_monthly_cost,
    ),
    planName: api.plan_name ?? (config.plan_name == null ? null : String(config.plan_name)),
    includedTokens: toNullableNumber(api.package_allowance ?? config.included_tokens),
    overageRate: toNullableNumber(api.overage_price ?? config.overage_rate),
    viewSeatCostUsd: toNullableNumber(config.view_seat_cost_usd),
    creditsPerUsd: toNullableNumber(config.credits_per_usd ?? config.credit_amount),
    includedCreditsPerSeat: toNullableNumber(config.included_credits_per_seat),
  });

  if (
    provider === "copilot" &&
    !isCopilotCreditPlan(pricing.planName) &&
    pricing.model === "per_team" &&
    pricing.flatMonthlyCost == null &&
    pricing.costPerSeat != null
  ) {
    pricing = normalizePricing({
      ...pricing,
      flatMonthlyCost: pricing.costPerSeat,
      costPerSeat: null,
    });
  }

  if (
    provider === "copilot" &&
    !isCopilotCreditPlan(pricing.planName) &&
    pricing.model === "per_seat" &&
    pricing.costPerSeat == null &&
    pricing.flatMonthlyCost != null
  ) {
    pricing = normalizePricing({
      ...pricing,
      costPerSeat: pricing.flatMonthlyCost,
      flatMonthlyCost: null,
    });
  }

  if (
    provider === "copilot" &&
    isCopilotCreditPlan(pricing.planName) &&
    pricing.model === "flat_fee"
  ) {
    pricing = normalizePricing({
      ...pricing,
      model: "per_seat",
      seatCount: pricing.seatCount ?? 1,
    });
  }

  if (
    provider === "copilot" &&
    pricing.seatCount == null
  ) {
    pricing = normalizePricing({ ...pricing, seatCount: 1 });
  }

  return pricing;
}

export function mapApiTeamToolAssignment(
  api: ApiTeamToolAssignment,
  provider?: ToolProvider,
): TeamToolAssignment {
  return {
    id: api.id,
    teamId: api.team_id,
    toolId: api.tool_id,
    toolName: api.tool_name,
    pricing: pricingFromTeamToolAssignment(api, provider),
    package: packageFromApi(api, provider),
    createdAt: api.created_at,
    updatedAt: api.updated_at,
  };
}

export function toTeamToolAssignApiBody(
  body: TeamToolAssignBody,
): Record<string, unknown> {
  const pricing = normalizePricing(body.pricing);
  const provider = body.provider ?? "custom";
  const fields = pricingToApiFields(pricing, provider);
  const config = fields.pricing_config;

  return {
    tool_id: body.toolId,
    pricing_model: fields.pricing_model,
    token_price: fields.token_price,
    output_token_price: config.output_cost_per_1k ?? null,
    cost_per_seat: config.cost_per_seat ?? null,
    seat_count: config.seat_count ?? null,
    package_allowance: fields.package_allowance,
    overage_price: fields.overage_price,
    plan_name: config.plan_name ?? null,
    pricing_config: config,
    ...packageToApiFields(body.package),
  };
}

export function toTeamToolUpdateApiBody(
  body: Omit<TeamToolAssignBody, "toolId">,
): Record<string, unknown> {
  const { tool_id: _ignored, ...rest } = toTeamToolAssignApiBody({
    toolId: "00000000-0000-0000-0000-000000000000",
    ...body,
  });
  return rest;
}

export function emptyTeamToolPricing(): ToolPricing {
  return emptyToolPricing();
}

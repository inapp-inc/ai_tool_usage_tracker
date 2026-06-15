/**
 * Maps backend OpenAPI shapes to frontend admin UI types.
 */

import type {
  AiTool,
  CreateToolRequest,
  PricingModel,
  ToolPricing,
  UpdateToolRequest,
} from "@/api/tools";
import type {
  CreateCredentialRequest,
  Credential,
  UpdateCredentialRequest,
} from "@/api/credentials";
import type { CreateTeamRequest, Team, UpdateTeamRequest } from "@/api/teams";

interface BackendTool {
  id: string;
  name: string;
  vendor: string;
  pricing_model: string;
  token_price: number | string;
  package_allowance?: number | null;
  overage_price?: number | string | null;
  active: boolean;
  created_at: string;
  updated_at?: string | null;
  pricing_config?: Record<string, unknown>;
}

interface BackendTeam {
  id: string;
  name: string;
  description?: string | null;
  active: boolean;
  member_count?: number;
  created_at: string;
  settings?: Record<string, unknown>;
}

interface BackendCredential {
  id: string;
  tool_id: string;
  team_id?: string | null;
  environment: "production" | "sandbox";
  masked_secret: string;
  label?: string;
  description?: string;
  status?: "active" | "inactive";
  rotation_reminder_days?: number | null;
  expires_at?: string | null;
  last_rotated_at?: string | null;
  created_at: string;
}

const DEFAULT_PRICING: ToolPricing = {
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

function asNumber(value: unknown): number | null {
  if (value == null || value === "") return null;
  return Number(value);
}

function mapPricingFromBackend(tool: BackendTool): ToolPricing {
  const cfg = tool.pricing_config ?? {};
  if (cfg.ui_pricing && typeof cfg.ui_pricing === "object") {
    return cfg.ui_pricing as ToolPricing;
  }
  const tokenPrice = asNumber(tool.token_price) ?? 0;
  if (tool.pricing_model === "package_with_overage") {
    return {
      ...DEFAULT_PRICING,
      model: "hybrid",
      flatMonthlyCost: tokenPrice,
      includedTokens: tool.package_allowance ?? null,
      overageRate: asNumber(tool.overage_price),
    };
  }
  return {
    ...DEFAULT_PRICING,
    model: "per_token",
    inputCostPer1K: tokenPrice,
    outputCostPer1K: asNumber(tool.overage_price) ?? tokenPrice,
  };
}

export function mapToolFromBackend(tool: BackendTool): AiTool {
  const cfg = tool.pricing_config ?? {};
  const provider = (cfg.provider as string | undefined) ?? tool.vendor;
  const status = !tool.active
    ? "inactive"
    : ((cfg.status as AiTool["status"] | undefined) ?? "active");

  const apiKeyMasked = String(cfg.api_key_masked ?? "sk-...****");
  const ingestionSource: AiTool["ingestionSource"] =
    cfg.ingestion_source === "csv" || apiKeyMasked === "csv-import" ? "csv" : "api";

  return {
    id: tool.id,
    name: tool.name,
    provider,
    description: String(cfg.description ?? ""),
    pricing: mapPricingFromBackend(tool),
    status,
    apiKeyMasked,
    ingestionSource,
    lastSyncAt: (cfg.last_sync_at as string | null | undefined) ?? null,
    lastCsvImportAt: (cfg.last_csv_import_at as string | null | undefined) ?? null,
    collectionSchedule:
      (cfg.collection_schedule as AiTool["collectionSchedule"] | undefined) ??
      "daily",
    tokenCount: Number(cfg.token_count ?? 0),
    costTotal: Number(cfg.cost_total ?? 0),
    createdAt: tool.created_at,
  };
}

function mapPricingModelToBackend(model: PricingModel): string {
  switch (model) {
    case "per_token":
      return "flat_token";
    case "hybrid":
      return "package_with_overage";
    default:
      return "custom";
  }
}

export function mapToolCreateToBackend(body: CreateToolRequest): Record<string, unknown> {
  const tokenPrice =
    body.pricing.inputCostPer1K ??
    body.pricing.flatMonthlyCost ??
    body.pricing.costPerSeat ??
    0;

  return {
    name: body.name,
    vendor: body.provider,
    pricing_model: mapPricingModelToBackend(body.pricing.model),
    token_price: tokenPrice,
    package_allowance: body.pricing.includedTokens ?? undefined,
    overage_price: body.pricing.overageRate ?? body.pricing.outputCostPer1K ?? undefined,
    pricing_config: {
      provider: body.provider,
      description: body.description,
      ui_pricing: body.pricing,
      collection_schedule: body.collectionSchedule,
      api_key_masked: body.apiKey ? `sk-...${body.apiKey.slice(-4)}` : undefined,
      token_count: 0,
      cost_total: 0,
      connection_valid: true,
    },
  };
}

export function mapToolUpdateToBackend(
  body: UpdateToolRequest,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  if (body.name !== undefined) payload.name = body.name;
  if (body.provider !== undefined) payload.vendor = body.provider;
  if (body.pricing !== undefined) {
    payload.pricing_model = mapPricingModelToBackend(body.pricing.model);
    payload.token_price =
      body.pricing.inputCostPer1K ??
      body.pricing.flatMonthlyCost ??
      body.pricing.costPerSeat ??
      0;
    payload.package_allowance = body.pricing.includedTokens ?? undefined;
    payload.overage_price =
      body.pricing.overageRate ?? body.pricing.outputCostPer1K ?? undefined;
  }

  const pricingConfig: Record<string, unknown> = {};
  if (body.provider !== undefined) pricingConfig.provider = body.provider;
  if (body.description !== undefined) pricingConfig.description = body.description;
  if (body.pricing !== undefined) pricingConfig.ui_pricing = body.pricing;
  if (body.collectionSchedule !== undefined) {
    pricingConfig.collection_schedule = body.collectionSchedule;
  }
  if (body.apiKey) pricingConfig.api_key_masked = `sk-...${body.apiKey.slice(-4)}`;
  if (Object.keys(pricingConfig).length > 0) payload.pricing_config = pricingConfig;

  return payload;
}

export function mapTeamFromBackend(team: BackendTeam): Team {
  const settings = team.settings ?? {};
  return {
    id: team.id,
    name: team.name,
    description: team.description ?? "",
    memberCount: team.member_count ?? 0,
    tokenBudget: (settings.tokenBudget as number | null | undefined) ?? null,
    costBudget: (settings.costBudget as number | null | undefined) ?? null,
    tokenUsedThisMonth: Number(settings.tokenUsedThisMonth ?? 0),
    costUsedThisMonth: Number(settings.costUsedThisMonth ?? 0),
    status: team.active ? "active" : "inactive",
    toolIds: (settings.toolIds as string[] | undefined) ?? [],
    createdAt: team.created_at,
  };
}

export function mapTeamCreateToBackend(body: CreateTeamRequest): Record<string, unknown> {
  return {
    name: body.name,
    description: body.description,
    settings: {
      toolIds: body.toolIds,
      tokenBudget: body.tokenBudget,
      costBudget: body.costBudget,
      tokenUsedThisMonth: 0,
      costUsedThisMonth: 0,
    },
  };
}

export function mapTeamUpdateToBackend(body: UpdateTeamRequest): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  if (body.name !== undefined) payload.name = body.name;
  if (body.description !== undefined) payload.description = body.description;

  const settings: Record<string, unknown> = {};
  if (body.toolIds !== undefined) settings.toolIds = body.toolIds;
  if (body.tokenBudget !== undefined) settings.tokenBudget = body.tokenBudget;
  if (body.costBudget !== undefined) settings.costBudget = body.costBudget;
  if (Object.keys(settings).length > 0) payload.settings = settings;

  return payload;
}

export function mapCredentialFromBackend(
  row: BackendCredential,
  toolNameById: Map<string, string>,
  teamNameById: Map<string, string>,
): Credential {
  const teamId = row.team_id ?? "";
  return {
    id: row.id,
    label: row.label ?? "",
    description: row.description ?? "",
    toolId: row.tool_id,
    toolName: toolNameById.get(row.tool_id) ?? row.tool_id,
    teamId,
    teamName: teamId ? (teamNameById.get(teamId) ?? teamId) : "Organization",
    environment: row.environment,
    keyMasked: row.masked_secret.replace("****", "sk-..."),
    status: row.status ?? "active",
    rotationReminderDays: row.rotation_reminder_days ?? null,
    expiresAt: row.expires_at ?? null,
    lastUsedAt: row.last_rotated_at ?? null,
    createdAt: row.created_at,
    createdByName: "Admin",
  };
}

export function mapCredentialCreateToBackend(
  body: CreateCredentialRequest,
): Record<string, unknown> {
  return {
    tool_id: body.toolId,
    team_id: body.teamId || null,
    environment: body.environment,
    secret_value: body.apiKey,
    label: body.label,
    description: body.description,
    rotation_reminder_days: body.rotationReminderDays,
    expires_at: body.expiresAt,
  };
}

export function mapCredentialUpdateToBackend(
  body: UpdateCredentialRequest,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  if (body.label !== undefined) payload.label = body.label;
  if (body.description !== undefined) payload.description = body.description;
  if (body.teamId !== undefined) payload.team_id = body.teamId || null;
  if (body.environment !== undefined) payload.environment = body.environment;
  if (body.rotationReminderDays !== undefined) {
    payload.rotation_reminder_days = body.rotationReminderDays;
  }
  if (body.expiresAt !== undefined) payload.expires_at = body.expiresAt;
  return payload;
}

export type { BackendTool, BackendTeam, BackendCredential };

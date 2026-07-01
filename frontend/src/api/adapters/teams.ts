/** Maps OpenAPI Team responses to frontend Team shape. */

export interface ApiTeam {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  active: boolean;
  member_count: number;
  token_budget?: number | null;
  cost_budget?: number | string | null;
  tool_ids?: string[];
  tokens_used?: number;
  pricing_total?: number | string;
  total_cost?: number | string;
  last_synced_at?: string | null;
  created_at: string;
}

export interface Team {
  id: string;
  organizationId: string;
  name: string;
  description: string;
  memberCount: number;
  tokenBudget: number | null;
  costBudget: number | null;
  tokensUsed: number;
  pricingTotal: number;
  totalCost: number;
  lastSyncedAt: string | null;
  status: "active" | "inactive";
  toolIds: string[];
  createdAt: string;
}

export interface CreateTeamRequest {
  name: string;
  description: string;
  tokenBudget: number | null;
  costBudget: number | null;
  toolIds: string[];
}

export type UpdateTeamRequest = Partial<CreateTeamRequest> & {
  status?: "active" | "inactive";
};

function parseCostBudget(value: number | string | null | undefined): number | null {
  if (value == null || value === "") {
    return null;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function parseMoney(value: number | string | null | undefined): number {
  if (value == null || value === "") {
    return 0;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

export function mapApiTeam(api: ApiTeam): Team {
  return {
    id: api.id,
    organizationId: api.organization_id,
    name: api.name,
    description: api.description ?? "",
    memberCount: api.member_count,
    tokenBudget: api.token_budget ?? null,
    costBudget: parseCostBudget(api.cost_budget),
    tokensUsed: api.tokens_used ?? 0,
    pricingTotal: parseMoney(api.pricing_total),
    totalCost: parseMoney(api.total_cost),
    lastSyncedAt: api.last_synced_at ?? null,
    status: api.active ? "active" : "inactive",
    toolIds: api.tool_ids ?? [],
    createdAt: api.created_at,
  };
}

/** Full form payload for create and update (edit form always submits all fields). */
export function toTeamWriteBody(body: CreateTeamRequest): {
  name: string;
  description: string;
  token_budget: number | null;
  cost_budget: number | null;
  tool_ids: string[];
} {
  return {
    name: body.name,
    description: body.description,
    token_budget: body.tokenBudget,
    cost_budget: body.costBudget,
    tool_ids: body.toolIds,
  };
}

export const toTeamCreateBody = toTeamWriteBody;
export const toTeamUpdateBody = toTeamWriteBody;

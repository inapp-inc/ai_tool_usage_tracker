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
  created_at: string;
}

export interface Team {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  tokenBudget: number | null;
  costBudget: number | null;
  tokenUsedThisMonth: number;
  costUsedThisMonth: number;
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

export function mapApiTeam(api: ApiTeam): Team {
  return {
    id: api.id,
    name: api.name,
    description: api.description ?? "",
    memberCount: api.member_count,
    tokenBudget: api.token_budget ?? null,
    costBudget: parseCostBudget(api.cost_budget),
    tokenUsedThisMonth: 0,
    costUsedThisMonth: 0,
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

const MOCK_LATENCY_MS = 400;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), MOCK_LATENCY_MS);
  });
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

export type UpdateTeamRequest = Partial<CreateTeamRequest>;

let mockTeams: Team[] = [
  {
    id: "team_1",
    name: "Engineering",
    description: "Platform and product engineering teams building core infrastructure.",
    memberCount: 24,
    tokenBudget: 5_000_000,
    costBudget: 500,
    tokenUsedThisMonth: 4_250_000,
    costUsedThisMonth: 412.5,
    status: "active",
    toolIds: ["tool_1", "tool_2"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 180).toISOString(),
  },
  {
    id: "team_2",
    name: "Data Science",
    description: "ML research, model training, and analytics pipelines.",
    memberCount: 12,
    tokenBudget: 2_000_000,
    costBudget: 250,
    tokenUsedThisMonth: 1_920_000,
    costUsedThisMonth: 231.4,
    status: "active",
    toolIds: ["tool_1", "tool_3"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 120).toISOString(),
  },
  {
    id: "team_3",
    name: "Design",
    description: "Product design, UX research, and brand creative workflows.",
    memberCount: 8,
    tokenBudget: null,
    costBudget: null,
    tokenUsedThisMonth: 680_000,
    costUsedThisMonth: 44.2,
    status: "active",
    toolIds: ["tool_3"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 90).toISOString(),
  },
  {
    id: "team_4",
    name: "Marketing",
    description: "Campaign content, copywriting, and social media automation.",
    memberCount: 6,
    tokenBudget: 1_500_000,
    costBudget: 120,
    tokenUsedThisMonth: 420_000,
    costUsedThisMonth: 38.6,
    status: "inactive",
    toolIds: ["tool_1", "tool_2", "tool_4"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString(),
  },
  {
    id: "team_5",
    name: "Sales",
    description: "Outbound messaging, proposal drafting, and CRM enrichment.",
    memberCount: 10,
    tokenBudget: 800_000,
    costBudget: 200,
    tokenUsedThisMonth: 520_000,
    costUsedThisMonth: 152.8,
    status: "active",
    toolIds: ["tool_5"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 45).toISOString(),
  },
  {
    id: "team_6",
    name: "Support",
    description: "Customer support triage and knowledge base assistance.",
    memberCount: 5,
    tokenBudget: null,
    costBudget: 75,
    tokenUsedThisMonth: 310_000,
    costUsedThisMonth: 28.4,
    status: "active",
    toolIds: ["tool_1"],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
  },
];

export async function fetchTeams(): Promise<Team[]> {
  return delay([...mockTeams]);
}

export async function createTeam(body: CreateTeamRequest): Promise<Team> {
  const team: Team = {
    id: `team_${Date.now()}`,
    name: body.name,
    description: body.description,
    memberCount: 0,
    tokenBudget: body.tokenBudget,
    costBudget: body.costBudget,
    tokenUsedThisMonth: 0,
    costUsedThisMonth: 0,
    status: "active",
    toolIds: body.toolIds,
    createdAt: new Date().toISOString(),
  };
  mockTeams = [...mockTeams, team];
  return delay(team);
}

export async function updateTeam(
  id: string,
  body: UpdateTeamRequest,
): Promise<Team> {
  const index = mockTeams.findIndex((team) => team.id === id);
  if (index === -1) {
    throw new Error("Team not found");
  }

  const existing = mockTeams[index];
  const updated: Team = {
    ...existing,
    ...(body.name !== undefined ? { name: body.name } : {}),
    ...(body.description !== undefined ? { description: body.description } : {}),
    ...(body.tokenBudget !== undefined ? { tokenBudget: body.tokenBudget } : {}),
    ...(body.costBudget !== undefined ? { costBudget: body.costBudget } : {}),
    ...(body.toolIds !== undefined ? { toolIds: body.toolIds } : {}),
  };

  mockTeams = mockTeams.map((team) => (team.id === id ? updated : team));
  return delay(updated);
}

export async function deleteTeam(id: string): Promise<void> {
  mockTeams = mockTeams.filter((team) => team.id !== id);
  await delay(undefined);
}

export const teamsApi = {
  fetchTeams,
  createTeam,
  updateTeam,
  deleteTeam,
};

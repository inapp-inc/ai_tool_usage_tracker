const MOCK_LATENCY_MS = 400;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), MOCK_LATENCY_MS);
  });
}

// Scope-based credentials reserved for future ingestion API use.
// export type CredentialScope = "ingest" | "read" | "ingest_read";
//
// export interface LegacyCredential {
//   id: string;
//   name: string;
//   scope: CredentialScope;
//   keyMasked: string;
//   teamId: string | null;
//   teamName: string | null;
//   status: "active" | "inactive";
//   lastUsedAt: string | null;
//   expiresAt: string | null;
//   createdAt: string;
//   createdByName: string;
// }

export type CredentialEnvironment = "production" | "sandbox";

export interface Credential {
  id: string;
  label: string;
  description: string;
  toolId: string;
  toolName: string;
  teamId: string;
  teamName: string;
  environment: CredentialEnvironment;
  keyMasked: string;
  status: "active" | "inactive";
  rotationReminderDays: number | null;
  expiresAt: string | null;
  lastUsedAt: string | null;
  createdAt: string;
  createdByName: string;
}

export interface CreateCredentialRequest {
  label: string;
  description: string;
  toolId: string;
  teamId: string;
  environment: CredentialEnvironment;
  apiKey: string;
  rotationReminderDays: number | null;
  expiresAt: string | null;
}

export interface CreateCredentialResponse {
  credential: Credential;
  plainKey: string;
}

export type UpdateCredentialRequest = Omit<
  Partial<CreateCredentialRequest>,
  "apiKey"
>;

const TEAM_NAMES: Record<string, string> = {
  team_1: "Engineering",
  team_2: "Data Science",
  team_3: "Design",
  team_4: "Marketing",
  team_5: "Sales",
  team_6: "Support",
};

const TOOL_NAMES: Record<string, string> = {
  tool_1: "Production OpenAI",
  tool_2: "Claude Enterprise",
  tool_3: "Gemini Workspace",
  tool_4: "Azure OpenAI EU",
  tool_5: "Internal LLM Gateway",
};

function maskKey(plainKey: string): string {
  return `sk-...${plainKey.slice(-4)}`;
}

function resolveTeamName(teamId: string): string {
  return TEAM_NAMES[teamId] ?? teamId;
}

function resolveToolName(toolId: string): string {
  return TOOL_NAMES[toolId] ?? toolId;
}

let mockCredentials: Credential[] = [
  {
    id: "cred_1",
    label: "GPT-4o Production – Engineering",
    description: "Primary OpenAI key for engineering workloads.",
    toolId: "tool_1",
    toolName: "Production OpenAI",
    teamId: "team_1",
    teamName: "Engineering",
    environment: "production",
    keyMasked: "sk-...a3Fb",
    status: "active",
    rotationReminderDays: 14,
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 7).toISOString(),
    lastUsedAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString(),
    createdByName: "Alan Chen",
  },
  {
    id: "cred_2",
    label: "Claude Sandbox – Data Science",
    description: "Sandbox Anthropic key for model evaluation.",
    toolId: "tool_2",
    toolName: "Claude Enterprise",
    teamId: "team_2",
    teamName: "Data Science",
    environment: "sandbox",
    keyMasked: "sk-...9kL2",
    status: "active",
    rotationReminderDays: null,
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 30).toISOString(),
    lastUsedAt: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
    createdByName: "Jordan Lee",
  },
  {
    id: "cred_3",
    label: "Gemini Design Workspace",
    description: "Google Gemini key for design team creative workflows.",
    toolId: "tool_3",
    toolName: "Gemini Workspace",
    teamId: "team_3",
    teamName: "Design",
    environment: "production",
    keyMasked: "sk-...pQ7x",
    status: "active",
    rotationReminderDays: 30,
    expiresAt: null,
    lastUsedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 45).toISOString(),
    createdByName: "Sam Rivera",
  },
  {
    id: "cred_4",
    label: "Azure OpenAI EU – Marketing",
    description: "Enterprise Azure deployment for campaign automation.",
    toolId: "tool_4",
    toolName: "Azure OpenAI EU",
    teamId: "team_4",
    teamName: "Marketing",
    environment: "production",
    keyMasked: "sk-...mN4z",
    status: "active",
    rotationReminderDays: 7,
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 10).toISOString(),
    lastUsedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 90).toISOString(),
    createdByName: "Taylor Kim",
  },
  {
    id: "cred_5",
    label: "Internal Gateway – Sales",
    description: "Custom LLM gateway for sales outreach tooling.",
    toolId: "tool_5",
    toolName: "Internal LLM Gateway",
    teamId: "team_5",
    teamName: "Sales",
    environment: "production",
    keyMasked: "sk-...rT8w",
    status: "inactive",
    rotationReminderDays: null,
    expiresAt: null,
    lastUsedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 40).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 120).toISOString(),
    createdByName: "Morgan Patel",
  },
  {
    id: "cred_6",
    label: "OpenAI Support Assist",
    description: "Production key for customer support triage bots.",
    toolId: "tool_1",
    toolName: "Production OpenAI",
    teamId: "team_6",
    teamName: "Support",
    environment: "production",
    keyMasked: "sk-...1P6n",
    status: "active",
    rotationReminderDays: 14,
    expiresAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    lastUsedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 200).toISOString(),
    createdByName: "Alan Chen",
  },
];

export async function fetchCredentials(): Promise<Credential[]> {
  return delay([...mockCredentials]);
}

export async function createCredential(
  body: CreateCredentialRequest,
): Promise<CreateCredentialResponse> {
  const plainKey = `sk-${crypto.randomUUID()}`;
  const credential: Credential = {
    id: `cred_${Date.now()}`,
    label: body.label,
    description: body.description,
    toolId: body.toolId,
    toolName: resolveToolName(body.toolId),
    teamId: body.teamId,
    teamName: resolveTeamName(body.teamId),
    environment: body.environment,
    keyMasked: maskKey(plainKey),
    status: "active",
    rotationReminderDays: body.rotationReminderDays,
    expiresAt: body.expiresAt,
    lastUsedAt: null,
    createdAt: new Date().toISOString(),
    createdByName: "Alan Chen",
  };

  mockCredentials = [...mockCredentials, credential];
  return delay({ credential, plainKey });
}

export async function updateCredential(
  id: string,
  body: UpdateCredentialRequest,
): Promise<Credential> {
  const index = mockCredentials.findIndex((credential) => credential.id === id);
  if (index === -1) {
    throw new Error("Credential not found");
  }

  const existing = mockCredentials[index];
  const teamId = body.teamId ?? existing.teamId;
  const toolId = body.toolId ?? existing.toolId;

  const updated: Credential = {
    ...existing,
    ...(body.label !== undefined ? { label: body.label } : {}),
    ...(body.description !== undefined ? { description: body.description } : {}),
    ...(body.environment !== undefined ? { environment: body.environment } : {}),
    ...(body.rotationReminderDays !== undefined
      ? { rotationReminderDays: body.rotationReminderDays }
      : {}),
    ...(body.expiresAt !== undefined ? { expiresAt: body.expiresAt } : {}),
    teamId,
    teamName: resolveTeamName(teamId),
    toolId,
    toolName: resolveToolName(toolId),
  };

  mockCredentials = mockCredentials.map((credential) =>
    credential.id === id ? updated : credential,
  );
  return delay(updated);
}

export async function revokeCredential(id: string): Promise<void> {
  mockCredentials = mockCredentials.map((credential) =>
    credential.id === id ? { ...credential, status: "inactive" } : credential,
  );
  await delay(undefined);
}

export const credentialsApi = {
  fetchCredentials,
  createCredential,
  updateCredential,
  revokeCredential,
};

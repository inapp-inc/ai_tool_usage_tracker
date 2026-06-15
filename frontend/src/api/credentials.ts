import { apiRequest, fetchAllPages } from "./client";
import {
  mapCredentialCreateToBackend,
  mapCredentialFromBackend,
  mapCredentialUpdateToBackend,
  type BackendCredential,
} from "./adapters/admin";
import { fetchTeams } from "./teams";
import { fetchTools } from "./tools";

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

async function buildLookupMaps(): Promise<{
  toolNameById: Map<string, string>;
  teamNameById: Map<string, string>;
}> {
  const [tools, teams] = await Promise.all([fetchTools(), fetchTeams()]);
  return {
    toolNameById: new Map(tools.map((tool) => [tool.id, tool.name])),
    teamNameById: new Map(teams.map((team) => [team.id, team.name])),
  };
}

export async function fetchCredentials(): Promise<Credential[]> {
  const rows = await fetchAllPages<BackendCredential>("/credentials", {
    limit: 100,
  });
  const { toolNameById, teamNameById } = await buildLookupMaps();
  return rows.map((row) => mapCredentialFromBackend(row, toolNameById, teamNameById));
}

export async function createCredential(
  body: CreateCredentialRequest,
): Promise<CreateCredentialResponse> {
  const created = await apiRequest<BackendCredential>("/credentials", {
    method: "POST",
    body: JSON.stringify(mapCredentialCreateToBackend(body)),
  });
  const { toolNameById, teamNameById } = await buildLookupMaps();
  const credential = mapCredentialFromBackend(created, toolNameById, teamNameById);
  return { credential, plainKey: body.apiKey };
}

export async function updateCredential(
  id: string,
  body: UpdateCredentialRequest,
): Promise<Credential> {
  const updated = await apiRequest<BackendCredential>(`/credentials/${id}`, {
    method: "PATCH",
    body: JSON.stringify(mapCredentialUpdateToBackend(body)),
  });
  const { toolNameById, teamNameById } = await buildLookupMaps();
  return mapCredentialFromBackend(updated, toolNameById, teamNameById);
}

export async function revokeCredential(id: string): Promise<void> {
  await apiRequest<void>(`/credentials/${id}/revoke`, { method: "POST" });
}

export const credentialsApi = {
  fetchCredentials,
  createCredential,
  updateCredential,
  revokeCredential,
};

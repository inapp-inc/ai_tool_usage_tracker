import { apiRequest, fetchAllPages } from "./client";
import {
  mapTeamCreateToBackend,
  mapTeamFromBackend,
  mapTeamUpdateToBackend,
  type BackendTeam,
} from "./adapters/admin";

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

export async function fetchTeams(): Promise<Team[]> {
  const rows = await fetchAllPages<BackendTeam>("/teams", { limit: 100 });
  return rows.map(mapTeamFromBackend);
}

export async function createTeam(body: CreateTeamRequest): Promise<Team> {
  const created = await apiRequest<BackendTeam>("/teams", {
    method: "POST",
    body: JSON.stringify(mapTeamCreateToBackend(body)),
  });
  return mapTeamFromBackend(created);
}

export async function updateTeam(
  id: string,
  body: UpdateTeamRequest,
): Promise<Team> {
  const updated = await apiRequest<BackendTeam>(`/teams/${id}`, {
    method: "PATCH",
    body: JSON.stringify(mapTeamUpdateToBackend(body)),
  });
  return mapTeamFromBackend(updated);
}

export async function deleteTeam(id: string): Promise<void> {
  await apiRequest<void>(`/teams/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ active: false }),
  });
}

export const teamsApi = {
  fetchTeams,
  createTeam,
  updateTeam,
  deleteTeam,
};

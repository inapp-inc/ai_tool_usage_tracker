import { apiRequest } from "./client";
import {
  mapApiTeam,
  toTeamCreateBody,
  toTeamUpdateBody,
  type ApiTeam,
  type CreateTeamRequest,
  type Team,
  type UpdateTeamRequest,
} from "./adapters/teams";

export type { CreateTeamRequest, Team, UpdateTeamRequest };

export async function fetchTeams(): Promise<Team[]> {
  const rows = await apiRequest<ApiTeam[]>("/teams");
  return rows.map(mapApiTeam);
}

export async function createTeam(body: CreateTeamRequest): Promise<Team> {
  const created = await apiRequest<ApiTeam>("/teams", {
    method: "POST",
    body: JSON.stringify(toTeamCreateBody(body)),
  });
  return mapApiTeam(created);
}

export async function updateTeam(id: string, body: UpdateTeamRequest): Promise<Team> {
  const updated = await apiRequest<ApiTeam>(`/teams/${id}`, {
    method: "PATCH",
    body: JSON.stringify(
      toTeamUpdateBody({
        name: body.name ?? "",
        description: body.description ?? "",
        tokenBudget: body.tokenBudget ?? null,
        costBudget: body.costBudget ?? null,
        toolIds: body.toolIds ?? [],
      }),
    ),
  });
  return mapApiTeam(updated);
}

export async function deleteTeam(id: string): Promise<void> {
  await apiRequest<void>(`/teams/${id}`, { method: "DELETE" });
}

export const teamsApi = {
  fetchTeams,
  createTeam,
  updateTeam,
  deleteTeam,
};

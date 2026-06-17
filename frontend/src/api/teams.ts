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

export interface TeamToolSyncResult {
  toolId: string;
  toolName: string;
  status: "synced" | "skipped" | "failed";
  message: string | null;
}

export interface TeamSyncResponse {
  teamId: string;
  syncedCount: number;
  skippedCount: number;
  failedCount: number;
  results: TeamToolSyncResult[];
}

interface ApiTeamToolSyncResult {
  tool_id: string;
  tool_name: string;
  status: "synced" | "skipped" | "failed";
  message?: string | null;
}

interface ApiTeamSyncResponse {
  team_id: string;
  synced_count: number;
  skipped_count: number;
  failed_count: number;
  results: ApiTeamToolSyncResult[];
}

function mapTeamSyncResponse(api: ApiTeamSyncResponse): TeamSyncResponse {
  return {
    teamId: api.team_id,
    syncedCount: api.synced_count,
    skippedCount: api.skipped_count,
    failedCount: api.failed_count,
    results: api.results.map((row) => ({
      toolId: row.tool_id,
      toolName: row.tool_name,
      status: row.status,
      message: row.message ?? null,
    })),
  };
}

/** Sync usage/members from all credentialed tools assigned to this team. */
export async function refreshTeamData(teamId: string): Promise<TeamSyncResponse> {
  const response = await apiRequest<ApiTeamSyncResponse>(`/teams/${teamId}/sync`, {
    method: "POST",
  });
  return mapTeamSyncResponse(response);
}

export const teamsApi = {
  fetchTeams,
  createTeam,
  updateTeam,
  deleteTeam,
  refreshTeamData,
};

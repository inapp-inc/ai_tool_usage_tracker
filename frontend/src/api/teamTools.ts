import { apiRequest } from "./client";
import {
  mapApiTeamToolAssignment,
  toTeamToolAssignApiBody,
  toTeamToolUpdateApiBody,
  type ApiTeamToolAssignment,
  type TeamToolAssignBody,
  type TeamToolAssignment,
} from "./adapters/teamTools";

export type { TeamToolAssignBody, TeamToolAssignment, TeamToolPackageBinding };

export { emptyTeamToolPackageBinding } from "./adapters/teamTools";

export async function fetchTeamTools(teamId: string): Promise<TeamToolAssignment[]> {
  const rows = await apiRequest<ApiTeamToolAssignment[]>(`/teams/${teamId}/tools`);
  return rows.map(mapApiTeamToolAssignment);
}

export async function fetchTeamToolAssignment(
  teamId: string,
  toolId: string,
): Promise<TeamToolAssignment | null> {
  const rows = await fetchTeamTools(teamId);
  return rows.find((row) => row.toolId === toolId) ?? null;
}

export async function upsertTeamTool(
  teamId: string,
  body: TeamToolAssignBody,
  existing = false,
): Promise<TeamToolAssignment> {
  if (existing) {
    const updated = await apiRequest<ApiTeamToolAssignment>(
      `/teams/${teamId}/tools/${body.toolId}`,
      {
        method: "PATCH",
        body: JSON.stringify(toTeamToolUpdateApiBody(body)),
      },
    );
    return mapApiTeamToolAssignment(updated);
  }

  const created = await apiRequest<ApiTeamToolAssignment>(`/teams/${teamId}/tools`, {
    method: "POST",
    body: JSON.stringify(toTeamToolAssignApiBody(body)),
  });
  return mapApiTeamToolAssignment(created);
}

export async function removeTeamTool(teamId: string, toolId: string): Promise<void> {
  await apiRequest<void>(`/teams/${teamId}/tools/${toolId}`, { method: "DELETE" });
}

export async function syncTeamToolAssignments(
  teamId: string,
  assignments: TeamToolAssignBody[],
  previousToolIds: string[],
): Promise<void> {
  const nextToolIds = new Set(assignments.map((row) => row.toolId));
  const previousSet = new Set(previousToolIds);

  const removals = previousToolIds.filter((toolId) => !nextToolIds.has(toolId));
  await Promise.all(removals.map((toolId) => removeTeamTool(teamId, toolId)));

  await Promise.all(
    assignments.map((assignment) =>
      upsertTeamTool(teamId, assignment, previousSet.has(assignment.toolId)),
    ),
  );
}

export const teamToolsApi = {
  fetchTeamTools,
  fetchTeamToolAssignment,
  upsertTeamTool,
  removeTeamTool,
  syncTeamToolAssignments,
};

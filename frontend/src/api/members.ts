import { apiRequest } from "./client";
import {
  mapApiMember,
  mapApiTeamMember,
  mapApiUser,
  toUserCreateBody,
  toUserUpdateBody,
  type ApiMember,
  type ApiTeamMember,
  type ApiUser,
} from "./adapters/members";
import type { ApiTeam } from "./adapters/teams";
import { Role } from "@/types";

export interface Member {
  id: string;
  name: string;
  email: string;
  platformRole: Role;
  teams: { id: string; name: string }[];
  status: "active" | "inactive";
  lastActiveAt: string | null;
  createdAt: string;
  /** Platform user vs provider token email vs file upload import. */
  source?: "platform" | "tool" | "upload";
  toolId?: string | null;
  toolName?: string | null;
  label?: string;
}

export interface InviteMemberRequest {
  name: string;
  email: string;
  platformRole?: Role;
  roleId?: string;
  teamIds: string[];
}

export interface UpdateMemberRequest {
  name?: string;
  platformRole?: Role;
  roleId?: string;
  teamIds?: string[];
  status?: "active" | "inactive";
}

export type MembersView = "all" | "invited";

export type { ApiMember, ApiTeamMember, ApiUser } from "./adapters/members";

export async function fetchMembers(view: MembersView = "all"): Promise<Member[]> {
  const rows = await apiRequest<ApiMember[]>(`/members?view=${view}`);
  return rows.map(mapApiMember);
}

export async function fetchMembersByTeam(teamId: string): Promise<Member[]> {
  const [team, rows] = await Promise.all([
    apiRequest<ApiTeam>(`/teams/${teamId}`),
    apiRequest<ApiTeamMember[]>(`/teams/${teamId}/members`),
  ]);
  const teamInfo = { id: team.id, name: team.name };
  return rows.map((row) => mapApiTeamMember(row, teamInfo));
}

export async function inviteMember(body: InviteMemberRequest): Promise<Member> {
  const created = await apiRequest<ApiUser>("/users", {
    method: "POST",
    body: JSON.stringify(toUserCreateBody(body)),
  });
  return mapApiUser(created);
}

export async function updateMember(
  id: string,
  body: UpdateMemberRequest,
): Promise<Member> {
  const updated = await apiRequest<ApiUser>(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(toUserUpdateBody(body)),
  });
  return mapApiUser(updated);
}

export async function removeMember(id: string): Promise<void> {
  await apiRequest<void>(`/users/${id}`, { method: "DELETE" });
}

export const membersApi = {
  fetchMembers,
  fetchMembersByTeam,
  inviteMember,
  updateMember,
  removeMember,
};

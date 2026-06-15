import { Role } from "@/types";

import { apiFormRequest, apiRequest } from "./client";

export interface Member {
  id: string;
  name: string;
  email: string;
  platformRole: Role;
  teams: { id: string; name: string }[];
  status: "active" | "inactive";
  lastActiveAt: string | null;
  createdAt: string;
}

export interface InviteMemberRequest {
  name: string;
  email: string;
  platformRole: Role;
  teamIds: string[];
}

export interface UpdateMemberRequest {
  name?: string;
  platformRole?: Role;
  teamIds?: string[];
  status?: "active" | "inactive";
}

interface BackendMember {
  id: string;
  name: string;
  email: string;
  platform_role: string;
  teams: Array<{ id: string; name: string }>;
  status: string;
  last_active_at: string | null;
  created_at: string;
}

function mapMember(row: BackendMember): Member {
  return {
    id: row.id,
    name: row.name,
    email: row.email,
    platformRole: row.platform_role as Role,
    teams: row.teams,
    status: row.status === "inactive" ? "inactive" : "active",
    lastActiveAt: row.last_active_at,
    createdAt: row.created_at,
  };
}

export async function fetchMembers(): Promise<Member[]> {
  const rows = await apiRequest<BackendMember[]>("/members");
  return rows.map(mapMember);
}

export async function fetchMembersByTeam(teamId: string): Promise<Member[]> {
  const rows = await apiRequest<BackendMember[]>(
    `/members?${new URLSearchParams({ team_id: teamId })}`,
  );
  return rows.map(mapMember);
}

export async function inviteMember(body: InviteMemberRequest): Promise<Member> {
  const created = await apiRequest<BackendMember>("/members", {
    method: "POST",
    body: JSON.stringify({
      name: body.name,
      email: body.email,
      platform_role: body.platformRole,
      team_ids: body.teamIds,
    }),
  });
  return mapMember(created);
}

export async function updateMember(
  id: string,
  body: UpdateMemberRequest,
): Promise<Member> {
  const payload: Record<string, unknown> = {};
  if (body.name !== undefined) payload.name = body.name;
  if (body.platformRole !== undefined) payload.platform_role = body.platformRole;
  if (body.teamIds !== undefined) payload.team_ids = body.teamIds;
  if (body.status !== undefined) payload.status = body.status;

  const updated = await apiRequest<BackendMember>(`/members/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return mapMember(updated);
}

export async function removeMember(id: string): Promise<void> {
  await apiRequest<void>(`/members/${id}`, { method: "DELETE" });
}

export const membersApi = {
  fetchMembers,
  fetchMembersByTeam,
  inviteMember,
  updateMember,
  removeMember,
};

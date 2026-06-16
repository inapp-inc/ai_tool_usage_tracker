/** Maps OpenAPI User / TeamMember responses to frontend Member shape. */

import { Role } from "@/types";

import type { InviteMemberRequest, Member, UpdateMemberRequest } from "../members";

export interface ApiUserTeam {
  id: string;
  name: string;
  joined_at: string;
}

export interface ApiUser {
  id: string;
  organization_id: string;
  email: string;
  display_name?: string | null;
  role: string;
  active: boolean;
  last_login_at?: string | null;
  created_at: string;
  teams?: ApiUserTeam[];
}

export interface ApiTeamMember {
  user_id?: string | null;
  email: string;
  display_name?: string | null;
  joined_at?: string | null;
  source?: "platform" | "tool";
  tool_id?: string | null;
  tool_name?: string | null;
}

/** Unified member row from GET /members. */
export interface ApiMember {
  user_id?: string | null;
  email: string;
  display_name?: string | null;
  role?: string;
  active?: boolean | null;
  last_login_at?: string | null;
  created_at?: string | null;
  joined_at?: string | null;
  source?: "platform" | "tool";
  tool_id?: string | null;
  tool_name?: string | null;
  teams?: ApiUserTeam[];
}

const ROLE_FROM_API: Record<string, Role> = {
  super_admin: Role.SuperAdmin,
  team_admin: Role.TeamAdmin,
  finance_viewer: Role.FinanceViewer,
  team_member: Role.TeamMember,
  auditor: Role.Auditor,
};

const ROLE_TO_API: Record<Role, string> = {
  [Role.SuperAdmin]: "super_admin",
  [Role.TeamAdmin]: "team_admin",
  [Role.FinanceViewer]: "finance_viewer",
  [Role.TeamMember]: "team_member",
  [Role.Auditor]: "auditor",
};

function roleFromApi(role: string): Role {
  return ROLE_FROM_API[role] ?? Role.TeamMember;
}

export function mapApiUser(api: ApiUser): Member {
  return mapApiMember({
    user_id: api.id,
    email: api.email,
    display_name: api.display_name,
    role: api.role,
    active: api.active,
    last_login_at: api.last_login_at,
    created_at: api.created_at,
    source: "platform",
    teams: api.teams,
  });
}

export function mapApiMember(api: ApiMember): Member {
  const isToolMember = api.source === "tool" || !api.user_id;
  const teams = (api.teams ?? []).map((team) => ({
    id: team.id,
    name: team.name,
  }));
  const toolSuffix = api.tool_name ? ` · ${api.tool_name}` : "";

  if (isToolMember) {
    return {
      id: `tool:${api.tool_id ?? "unknown"}:${api.email.toLowerCase()}`,
      name: api.display_name?.trim() || api.email,
      email: api.email,
      platformRole: Role.TeamMember,
      teams,
      status: "active",
      lastActiveAt: null,
      createdAt: api.joined_at ?? new Date(0).toISOString(),
      source: "tool",
      toolId: api.tool_id ?? null,
      toolName: api.tool_name ?? null,
      label: `Tool member${toolSuffix}`,
    };
  }

  return {
    id: api.user_id!,
    name: api.display_name?.trim() || api.email,
    email: api.email,
    platformRole: roleFromApi(api.role ?? "team_member"),
    teams,
    status: api.active ? "active" : "inactive",
    lastActiveAt: api.last_login_at ?? null,
    createdAt: api.created_at ?? new Date(0).toISOString(),
    source: "platform",
  };
}

export function mapApiTeamMember(
  api: ApiTeamMember,
  team?: { id: string; name: string },
): Member {
  const isToolMember = api.source === "tool" || !api.user_id;
  const toolSuffix = api.tool_name ? ` · ${api.tool_name}` : "";
  return {
    id:
      api.user_id ??
      `tool:${api.tool_id ?? "unknown"}:${api.email.toLowerCase()}`,
    name: api.display_name?.trim() || api.email,
    email: api.email,
    platformRole: Role.TeamMember,
    teams: team ? [{ id: team.id, name: team.name }] : [],
    status: "active",
    lastActiveAt: null,
    createdAt: api.joined_at ?? new Date(0).toISOString(),
    source: isToolMember ? "tool" : "platform",
    toolId: api.tool_id ?? null,
    toolName: api.tool_name ?? null,
    label: isToolMember ? `Tool member${toolSuffix}` : undefined,
  };
}

export function toUserCreateBody(body: InviteMemberRequest): {
  email: string;
  display_name: string;
  role: string;
  team_ids: string[];
} {
  return {
    email: body.email,
    display_name: body.name,
    role: ROLE_TO_API[body.platformRole],
    team_ids: body.teamIds,
  };
}

export function toUserUpdateBody(body: UpdateMemberRequest): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  if (body.name !== undefined) {
    payload.display_name = body.name;
  }
  if (body.platformRole !== undefined) {
    payload.role = ROLE_TO_API[body.platformRole];
  }
  if (body.status !== undefined) {
    payload.active = body.status === "active";
  }
  if (body.teamIds !== undefined) {
    payload.team_ids = body.teamIds;
  }
  return payload;
}

export { ROLE_FROM_API, ROLE_TO_API };

import { Role } from "@/types";

const MOCK_LATENCY_MS = 400;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), MOCK_LATENCY_MS);
  });
}

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

const TEAM_NAMES: Record<string, string> = {
  team_1: "Engineering",
  team_2: "Data Science",
  team_3: "Design",
  team_4: "Marketing",
  team_5: "Sales",
  team_6: "Support",
};

function resolveTeams(teamIds: string[]): Array<{ id: string; name: string }> {
  return teamIds.map((id) => ({
    id,
    name: TEAM_NAMES[id] ?? id,
  }));
}

let mockMembers: Member[] = [
  {
    id: "member_1",
    name: "Alan Chen",
    email: "alan.chen@example.com",
    platformRole: Role.SuperAdmin,
    teams: [
      { id: "team_1", name: "Engineering" },
      { id: "team_2", name: "Data Science" },
    ],
    status: "active",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 365).toISOString(),
  },
  {
    id: "member_2",
    name: "Jordan Lee",
    email: "jordan.lee@example.com",
    platformRole: Role.TeamAdmin,
    teams: [{ id: "team_1", name: "Engineering" }],
    status: "active",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 200).toISOString(),
  },
  {
    id: "member_3",
    name: "Sam Rivera",
    email: "sam.rivera@example.com",
    platformRole: Role.FinanceViewer,
    teams: [
      { id: "team_2", name: "Data Science" },
      { id: "team_3", name: "Design" },
    ],
    status: "active",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 150).toISOString(),
  },
  {
    id: "member_4",
    name: "Taylor Kim",
    email: "taylor.kim@example.com",
    platformRole: Role.TeamMember,
    teams: [{ id: "team_3", name: "Design" }],
    status: "active",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 90).toISOString(),
  },
  {
    id: "member_5",
    name: "Morgan Patel",
    email: "morgan.patel@example.com",
    platformRole: Role.Auditor,
    teams: [{ id: "team_4", name: "Marketing" }],
    status: "active",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 120).toISOString(),
  },
  {
    id: "member_6",
    name: "Casey Nguyen",
    email: "casey.nguyen@example.com",
    platformRole: Role.TeamMember,
    teams: [
      { id: "team_1", name: "Engineering" },
      { id: "team_5", name: "Sales" },
    ],
    status: "inactive",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 80).toISOString(),
  },
  {
    id: "member_7",
    name: "Riley Brooks",
    email: "riley.brooks@example.com",
    platformRole: Role.TeamAdmin,
    teams: [{ id: "team_5", name: "Sales" }],
    status: "active",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString(),
  },
  {
    id: "member_8",
    name: "Jamie Ortiz",
    email: "jamie.ortiz@example.com",
    platformRole: Role.TeamMember,
    teams: [{ id: "team_6", name: "Support" }],
    status: "active",
    lastActiveAt: null,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14).toISOString(),
  },
  {
    id: "member_9",
    name: "Dana Wolfe",
    email: "dana.wolfe@example.com",
    platformRole: Role.FinanceViewer,
    teams: [
      { id: "team_2", name: "Data Science" },
      { id: "team_4", name: "Marketing" },
    ],
    status: "active",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 45).toISOString(),
  },
  {
    id: "member_10",
    name: "Chris Adams",
    email: "chris.adams@example.com",
    platformRole: Role.TeamMember,
    teams: [
      { id: "team_1", name: "Engineering" },
      { id: "team_2", name: "Data Science" },
      { id: "team_3", name: "Design" },
    ],
    status: "active",
    lastActiveAt: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
  },
];

export async function fetchMembers(): Promise<Member[]> {
  return delay([...mockMembers]);
}

export async function fetchMembersByTeam(teamId: string): Promise<Member[]> {
  const filtered = mockMembers.filter((member) =>
    member.teams.some((team) => team.id === teamId),
  );
  return delay([...filtered]);
}

export async function inviteMember(body: InviteMemberRequest): Promise<Member> {
  const member: Member = {
    id: `member_${Date.now()}`,
    name: body.name,
    email: body.email,
    platformRole: body.platformRole,
    teams: resolveTeams(body.teamIds),
    status: "active",
    lastActiveAt: null,
    createdAt: new Date().toISOString(),
  };
  mockMembers = [...mockMembers, member];
  return delay(member);
}

export async function updateMember(
  id: string,
  body: UpdateMemberRequest,
): Promise<Member> {
  const index = mockMembers.findIndex((member) => member.id === id);
  if (index === -1) {
    throw new Error("Member not found");
  }

  const existing = mockMembers[index];
  const updated: Member = {
    ...existing,
    ...(body.name !== undefined ? { name: body.name } : {}),
    ...(body.platformRole !== undefined
      ? { platformRole: body.platformRole }
      : {}),
    ...(body.teamIds !== undefined
      ? { teams: resolveTeams(body.teamIds) }
      : {}),
    ...(body.status !== undefined ? { status: body.status } : {}),
  };

  mockMembers = mockMembers.map((member) => (member.id === id ? updated : member));
  return delay(updated);
}

export async function removeMember(id: string): Promise<void> {
  mockMembers = mockMembers.filter((member) => member.id !== id);
  await delay(undefined);
}

export const membersApi = {
  fetchMembers,
  fetchMembersByTeam,
  inviteMember,
  updateMember,
  removeMember,
};

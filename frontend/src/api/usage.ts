import { differenceInCalendarDays, format, parseISO, subDays } from "date-fns";

const MOCK_LATENCY_MS = 400;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), MOCK_LATENCY_MS);
  });
}

export interface UsageSummary {
  totalTokens: number;
  totalCost: number;
  avgCostPerToken: number;
  periodDays: number;
}

export interface TeamUsageRow {
  teamId: string;
  teamName: string;
  tokens: number;
  cost: number;
  percentOfTotal: number;
  memberCount: number;
  tokenBudget: number | null;
  costBudget: number | null;
  budgetUtilization: number | null;
  trend: number;
}

export interface DailyUsagePoint {
  date: string;
  tokens: number;
  cost: number;
}

export interface UserUsageRow {
  userId: string;
  userName: string;
  userEmail: string;
  teamId: string;
  teamName: string;
  tokens: number;
  cost: number;
  percentOfTeamTotal: number;
  requestCount: number;
  avgTokensPerRequest: number;
}

const MOCK_TEAM_USAGE: Omit<
  TeamUsageRow,
  "percentOfTotal" | "budgetUtilization"
>[] = [
  {
    teamId: "team_1",
    teamName: "Engineering",
    tokens: 4_250_000,
    cost: 412.5,
    memberCount: 24,
    tokenBudget: 5_000_000,
    costBudget: 500,
    trend: 8.4,
  },
  {
    teamId: "team_2",
    teamName: "Data Science",
    tokens: 1_920_000,
    cost: 231.4,
    memberCount: 12,
    tokenBudget: 2_000_000,
    costBudget: 250,
    trend: 12.1,
  },
  {
    teamId: "team_3",
    teamName: "Design",
    tokens: 680_000,
    cost: 44.2,
    memberCount: 8,
    tokenBudget: null,
    costBudget: null,
    trend: -3.2,
  },
  {
    teamId: "team_4",
    teamName: "Marketing",
    tokens: 420_000,
    cost: 38.6,
    memberCount: 6,
    tokenBudget: 1_500_000,
    costBudget: 120,
    trend: -5.1,
  },
  {
    teamId: "team_5",
    teamName: "Sales",
    tokens: 520_000,
    cost: 152.8,
    memberCount: 10,
    tokenBudget: 800_000,
    costBudget: 200,
    trend: 6.7,
  },
  {
    teamId: "team_6",
    teamName: "Support",
    tokens: 310_000,
    cost: 28.4,
    memberCount: 5,
    tokenBudget: null,
    costBudget: 75,
    trend: 1.9,
  },
];

const MOCK_USERS_BY_TEAM: Record<string, UserUsageRow[]> = {
  team_1: [
    {
      userId: "u1",
      userName: "Alex Chen",
      userEmail: "alex.chen@example.com",
      teamId: "team_1",
      teamName: "Engineering",
      tokens: 892_400,
      cost: 86.7,
      percentOfTeamTotal: 0.21,
      requestCount: 1240,
      avgTokensPerRequest: 719,
    },
    {
      userId: "u3",
      userName: "Sam Rivera",
      userEmail: "sam.rivera@example.com",
      teamId: "team_1",
      teamName: "Engineering",
      tokens: 721_500,
      cost: 70.1,
      percentOfTeamTotal: 0.17,
      requestCount: 980,
      avgTokensPerRequest: 736,
    },
    {
      userId: "u6",
      userName: "Casey Nguyen",
      userEmail: "casey.nguyen@example.com",
      teamId: "team_1",
      teamName: "Engineering",
      tokens: 654_200,
      cost: 63.5,
      percentOfTeamTotal: 0.154,
      requestCount: 860,
      avgTokensPerRequest: 761,
    },
    {
      userId: "u10",
      userName: "Chris Adams",
      userEmail: "chris.adams@example.com",
      teamId: "team_1",
      teamName: "Engineering",
      tokens: 598_400,
      cost: 58.1,
      percentOfTeamTotal: 0.141,
      requestCount: 790,
      avgTokensPerRequest: 757,
    },
    {
      userId: "u11",
      userName: "Dana Wolfe",
      userEmail: "dana.wolfe@example.com",
      teamId: "team_1",
      teamName: "Engineering",
      tokens: 512_300,
      cost: 49.8,
      percentOfTeamTotal: 0.121,
      requestCount: 710,
      avgTokensPerRequest: 722,
    },
    {
      userId: "u12",
      userName: "Evan Brooks",
      userEmail: "evan.brooks@example.com",
      teamId: "team_1",
      teamName: "Engineering",
      tokens: 421_800,
      cost: 41.0,
      percentOfTeamTotal: 0.099,
      requestCount: 620,
      avgTokensPerRequest: 680,
    },
    {
      userId: "u13",
      userName: "Frank Ortiz",
      userEmail: "frank.ortiz@example.com",
      teamId: "team_1",
      teamName: "Engineering",
      tokens: 289_400,
      cost: 28.1,
      percentOfTeamTotal: 0.068,
      requestCount: 410,
      avgTokensPerRequest: 706,
    },
    {
      userId: "u14",
      userName: "Grace Kim",
      userEmail: "grace.kim@example.com",
      teamId: "team_1",
      teamName: "Engineering",
      tokens: 160_000,
      cost: 15.2,
      percentOfTeamTotal: 0.038,
      requestCount: 240,
      avgTokensPerRequest: 667,
    },
  ],
};

function buildTeamUsageRows(): TeamUsageRow[] {
  const totalTokens = MOCK_TEAM_USAGE.reduce((sum, row) => sum + row.tokens, 0);

  return MOCK_TEAM_USAGE.map((row) => ({
    ...row,
    percentOfTotal: row.tokens / totalTokens,
    budgetUtilization:
      row.tokenBudget == null
        ? null
        : Math.min((row.tokens / row.tokenBudget) * 100, 100),
  }));
}

function periodDays(from: string, to: string): number {
  return Math.max(
    1,
    differenceInCalendarDays(parseISO(to), parseISO(from)) + 1,
  );
}

function generateDailyUsage(from: string, to: string): DailyUsagePoint[] {
  const end = parseISO(to);
  const days = periodDays(from, to);

  return Array.from({ length: days }, (_, index) => {
    const date = subDays(end, days - 1 - index);
    const dayFactor = 1 + Math.sin(index / 3) * 0.12;
    const tokens = Math.round(285_000 * dayFactor + (index % 5) * 12_000);
    return {
      date: format(date, "MMM d"),
      tokens,
      cost: Number((tokens * 0.000097).toFixed(2)),
    };
  });
}

function buildSummary(from: string, to: string): UsageSummary {
  const teams = buildTeamUsageRows();
  const totalTokens = teams.reduce((sum, row) => sum + row.tokens, 0);
  const totalCost = teams.reduce((sum, row) => sum + row.cost, 0);

  return {
    totalTokens,
    totalCost,
    avgCostPerToken: totalTokens > 0 ? totalCost / totalTokens : 0,
    periodDays: periodDays(from, to),
  };
}

function buildGenericUsers(teamId: string, teamName: string): UserUsageRow[] {
  const base = MOCK_USERS_BY_TEAM.team_1.map((user, index) => ({
    ...user,
    userId: `${teamId}_u${index + 1}`,
    userEmail: user.userEmail.replace("@", `+${teamId}@`),
    teamId,
    teamName,
    tokens: Math.round(user.tokens * (0.6 + index * 0.04)),
    cost: Number((user.cost * (0.6 + index * 0.04)).toFixed(2)),
  }));

  const teamTotal = base.reduce((sum, user) => sum + user.tokens, 0);
  return base.map((user) => ({
    ...user,
    percentOfTeamTotal: user.tokens / teamTotal,
  }));
}

export async function fetchUsageSummary(
  from: string,
  to: string,
): Promise<UsageSummary> {
  return delay(buildSummary(from, to));
}

export async function fetchTeamUsage(
  from: string,
  to: string,
): Promise<TeamUsageRow[]> {
  void from;
  void to;
  return delay(buildTeamUsageRows());
}

export async function fetchDailyUsage(
  from: string,
  to: string,
): Promise<DailyUsagePoint[]> {
  return delay(generateDailyUsage(from, to));
}

export async function fetchUserUsage(
  teamId: string,
  from: string,
  to: string,
): Promise<UserUsageRow[]> {
  void from;
  void to;

  const team = MOCK_TEAM_USAGE.find((row) => row.teamId === teamId);
  const teamName = team?.teamName ?? "Team";

  if (MOCK_USERS_BY_TEAM[teamId]) {
    return delay([...MOCK_USERS_BY_TEAM[teamId]]);
  }

  return delay(buildGenericUsers(teamId, teamName));
}

export async function fetchTeamDrilldown(
  teamId: string,
  from: string,
  to: string,
  toolId: string | null,
): Promise<UserUsageRow[]> {
  void toolId;
  return fetchUserUsage(teamId, from, to);
}

export async function fetchToolOptions(): Promise<{ id: string; name: string }[]> {
  const { apiRequest } = await import("./client");
  const rows = await apiRequest<Array<{ id: string; name: string }>>("/tools?active=true");
  return rows.map((row) => ({ id: row.id, name: row.name }));
}

export interface DailyBreakdownTeam {
  teamId: string;
  teamName: string;
  tokens: number;
  cost: number;
  users: {
    userId: string;
    userName: string;
    tokens: number;
    cost: number;
  }[];
}

const DAILY_BREAKDOWN_USERS: Record<string, string[]> = {
  team_1: ["Alice Wang", "Bob Chen", "Carol Davis", "Alex Chen", "Dana Wolfe"],
  team_2: ["Jordan Lee", "Sam Rivera", "Taylor Kim"],
  team_3: ["Morgan Patel", "Riley Brooks", "Casey Nguyen", "Chris Adams"],
  team_4: ["Frank Ortiz", "Grace Kim", "Evan Brooks"],
  team_5: ["Priya Sharma", "Marcus Webb", "Nina Torres", "Leo Park"],
  team_6: ["Olivia Reed", "James Holt", "Sofia Mendez"],
};

function buildDailyBreakdownUsers(
  teamId: string,
  teamDailyTokens: number,
  teamDailyCost: number,
  userCount: number,
): DailyBreakdownTeam["users"] {
  const names =
    DAILY_BREAKDOWN_USERS[teamId] ??
    Array.from({ length: userCount }, (_, index) => `User ${index + 1}`);

  const selectedNames = names.slice(0, userCount);
  const weights = selectedNames.map((_, index) => 1 + (index % 3) * 0.15);
  const weightTotal = weights.reduce((sum, weight) => sum + weight, 0);

  return selectedNames.map((userName, index) => {
    const share = weights[index] / weightTotal;
    const tokens = Math.round(teamDailyTokens * share);
    const cost = Number((teamDailyCost * share).toFixed(2));
    return {
      userId: `${teamId}_${index + 1}`,
      userName,
      tokens,
      cost,
    };
  });
}

function buildDailyBreakdown(
  date: string,
  teamId: string | null,
  toolId: string | null,
): DailyBreakdownTeam[] {
  void toolId;

  const dayFactor = 0.028 + (date.length % 4) * 0.004;
  const teams = teamId
    ? MOCK_TEAM_USAGE.filter((team) => team.teamId === teamId)
    : MOCK_TEAM_USAGE.slice(0, 4);

  return teams
    .map((team) => {
      const teamDailyTokens = Math.round(team.tokens * dayFactor);
      const teamDailyCost = Number((team.cost * dayFactor).toFixed(2));
      const userCount = 3 + (team.teamId.charCodeAt(team.teamId.length - 1) % 3);

      return {
        teamId: team.teamId,
        teamName: team.teamName,
        tokens: teamDailyTokens,
        cost: teamDailyCost,
        users: buildDailyBreakdownUsers(
          team.teamId,
          teamDailyTokens,
          teamDailyCost,
          userCount,
        ),
      };
    })
    .sort((a, b) => b.tokens - a.tokens);
}

export async function fetchDailyBreakdown(
  date: string,
  teamId: string | null,
  toolId: string | null,
): Promise<DailyBreakdownTeam[]> {
  return delay(buildDailyBreakdown(date, teamId, toolId));
}

export const usageApi = {
  fetchUsageSummary,
  fetchTeamUsage,
  fetchDailyUsage,
  fetchUserUsage,
  fetchTeamDrilldown,
  fetchToolOptions,
  fetchDailyBreakdown,
};

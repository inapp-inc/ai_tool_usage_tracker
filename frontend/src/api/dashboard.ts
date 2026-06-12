import { format, subDays } from "date-fns";

const MOCK_LATENCY_MS = 400;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), MOCK_LATENCY_MS);
  });
}

export interface DashboardStats {
  totalTokens: number;
  totalCost: number;
  activeTools: number;
  activeTeams: number;
  tokensDelta: number;
  costDelta: number;
  toolsDelta: number;
  teamsDelta: number;
}

export interface TokenDataPoint {
  date: string;
  tokens: number;
  cost: number;
}

export interface TeamCostDataPoint {
  team: string;
  cost: number;
}

export interface TopUser {
  id: string;
  name: string;
  team: string;
  tokens: number;
  cost: number;
  percentOfTotal: number;
}

export interface RecentAlert {
  id: string;
  title: string;
  severity: "critical" | "warning" | "info";
  triggeredAt: string;
  team: string;
}

function generateTimeseries(): TokenDataPoint[] {
  const today = new Date();
  return Array.from({ length: 30 }, (_, index) => {
    const date = subDays(today, 29 - index);
    const dayFactor = 1 + Math.sin(index / 4) * 0.15;
    const tokens = Math.round(145_000 * dayFactor + (index % 7) * 8_500);
    return {
      date: format(date, "MMM d"),
      tokens,
      cost: Number((tokens * 0.000065).toFixed(2)),
    };
  });
}

const MOCK_STATS: DashboardStats = {
  totalTokens: 4_820_300,
  totalCost: 312.45,
  activeTools: 7,
  activeTeams: 12,
  tokensDelta: 8.4,
  costDelta: 5.2,
  toolsDelta: 0,
  teamsDelta: 2.1,
};

const MOCK_TIMESERIES = generateTimeseries();

const MOCK_TEAM_COSTS: TeamCostDataPoint[] = [
  { team: "Engineering", cost: 98.4 },
  { team: "Data Science", cost: 72.15 },
  { team: "Design", cost: 41.2 },
  { team: "Marketing", cost: 38.6 },
  { team: "Sales", cost: 35.1 },
  { team: "Support", cost: 27.0 },
];

const MOCK_TOP_USERS: TopUser[] = [
  {
    id: "u1",
    name: "Alex Chen",
    team: "Engineering",
    tokens: 892_400,
    cost: 58.02,
    percentOfTotal: 0.185,
  },
  {
    id: "u2",
    name: "Jordan Lee",
    team: "Data Science",
    tokens: 654_200,
    cost: 42.52,
    percentOfTotal: 0.136,
  },
  {
    id: "u3",
    name: "Sam Rivera",
    team: "Engineering",
    tokens: 521_800,
    cost: 33.92,
    percentOfTotal: 0.108,
  },
  {
    id: "u4",
    name: "Taylor Kim",
    team: "Design",
    tokens: 412_300,
    cost: 26.8,
    percentOfTotal: 0.086,
  },
  {
    id: "u5",
    name: "Morgan Patel",
    team: "Marketing",
    tokens: 387_600,
    cost: 25.19,
    percentOfTotal: 0.08,
  },
  {
    id: "u6",
    name: "Casey Nguyen",
    team: "Sales",
    tokens: 298_400,
    cost: 19.4,
    percentOfTotal: 0.062,
  },
  {
    id: "u7",
    name: "Riley Brooks",
    team: "Support",
    tokens: 245_100,
    cost: 15.93,
    percentOfTotal: 0.051,
  },
  {
    id: "u8",
    name: "Jamie Ortiz",
    team: "Engineering",
    tokens: 198_700,
    cost: 12.92,
    percentOfTotal: 0.041,
  },
];

const MOCK_RECENT_ALERTS: RecentAlert[] = [
  {
    id: "a1",
    title: "Token threshold exceeded",
    severity: "critical",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    team: "Engineering",
  },
  {
    id: "a2",
    title: "Monthly budget at 85%",
    severity: "warning",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
    team: "Data Science",
  },
  {
    id: "a3",
    title: "New tool integration active",
    severity: "info",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString(),
    team: "Design",
  },
  {
    id: "a4",
    title: "Unusual usage spike detected",
    severity: "warning",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 22).toISOString(),
    team: "Marketing",
  },
  {
    id: "a5",
    title: "Daily limit approaching",
    severity: "critical",
    triggeredAt: new Date(Date.now() - 1000 * 60 * 60 * 30).toISOString(),
    team: "Sales",
  },
];

export async function fetchDashboardStats(
  from: string,
  to: string,
): Promise<DashboardStats> {
  void from;
  void to;
  return delay(MOCK_STATS);
}

export async function fetchTokenTimeseries(
  from: string,
  to: string,
): Promise<TokenDataPoint[]> {
  void from;
  void to;
  return delay(MOCK_TIMESERIES);
}

export async function fetchTeamCost(
  from: string,
  to: string,
): Promise<TeamCostDataPoint[]> {
  void from;
  void to;
  return delay(MOCK_TEAM_COSTS);
}

export async function fetchTopUsers(
  from: string,
  to: string,
): Promise<TopUser[]> {
  void from;
  void to;
  return delay(MOCK_TOP_USERS);
}

export async function fetchRecentAlerts(): Promise<RecentAlert[]> {
  return delay(MOCK_RECENT_ALERTS);
}

export const dashboardApi = {
  fetchDashboardStats,
  fetchTokenTimeseries,
  fetchTeamCost,
  fetchTopUsers,
  fetchRecentAlerts,
};

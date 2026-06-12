import {
  IconActivity,
  IconArrowLeft,
  IconChartBar,
  IconCurrencyDollar,
  IconUsers,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  LinearProgress,
  Skeleton,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { endOfDay, startOfDay, subDays } from "date-fns";
import { useMemo, useState } from "react";
import {
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  fetchDailyUsage,
  fetchTeamUsage,
  fetchUserUsage,
  type UserUsageRow,
} from "@/api/usage";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { SkeletonCard } from "@/components/data-display/SkeletonCard";
import { StatCard } from "@/components/data-display/StatCard";
import { EmptyState } from "@/components/feedback/EmptyState";
import { PeriodSelector } from "@/components/inputs/PeriodSelector";
import type { DateRange } from "@/types";
import { tokens } from "@/theme/palette";
import { formatCost, formatPercent, formatTokens } from "@/utils/formatters";

type ChartMode = "tokens" | "cost";

function createDefaultPeriod(): DateRange {
  const today = new Date();
  return {
    from: startOfDay(subDays(today, 30)).toISOString(),
    to: endOfDay(today).toISOString(),
  };
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function SectionError() {
  return (
    <Alert severity="error">Failed to load data. Please refresh.</Alert>
  );
}

function resolvePeriod(searchParams: URLSearchParams): DateRange {
  const from = searchParams.get("from");
  const to = searchParams.get("to");
  if (from && to) {
    return { from, to };
  }
  return createDefaultPeriod();
}

export function UserUsagePage() {
  const navigate = useNavigate();
  const { teamId = "" } = useParams<{ teamId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const [chartMode, setChartMode] = useState<ChartMode>("tokens");

  const period = useMemo(
    () => resolvePeriod(searchParams),
    [searchParams],
  );

  const from = period.from;
  const to = period.to;

  const setPeriod = (range: DateRange) => {
    setSearchParams({ from: range.from, to: range.to });
  };

  const teamsQuery = useQuery({
    queryKey: ["usage", "teams", from, to],
    queryFn: () => fetchTeamUsage(from, to),
  });

  const usersQuery = useQuery({
    queryKey: ["usage", "users", teamId, from, to],
    queryFn: () => fetchUserUsage(teamId, from, to),
    enabled: Boolean(teamId),
  });

  const dailyQuery = useQuery({
    queryKey: ["usage", "daily", from, to],
    queryFn: () => fetchDailyUsage(from, to),
  });

  const team = useMemo(
    () => teamsQuery.data?.find((row) => row.teamId === teamId) ?? null,
    [teamId, teamsQuery.data],
  );

  const sortedUsers = useMemo(() => {
    const users = usersQuery.data ?? [];
    return [...users].sort((a, b) => b.tokens - a.tokens);
  }, [usersQuery.data]);

  const activeMemberCount = useMemo(
    () => sortedUsers.filter((user) => user.tokens > 0).length,
    [sortedUsers],
  );

  const columns: Column<UserUsageRow>[] = useMemo(
    () => [
      {
        key: "userName",
        header: "Member",
        sortable: true,
        render: (row) => (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.25 }}>
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                backgroundColor: "#1E3A5F",
                color: "#60A5FA",
                fontSize: 11,
                fontWeight: 500,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              {getInitials(row.userName)}
            </Box>
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {row.userName}
              </Typography>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {row.userEmail}
              </Typography>
            </Box>
          </Box>
        ),
      },
      {
        key: "tokens",
        header: "Tokens",
        sortable: true,
        align: "right",
        render: (row) => formatTokens(row.tokens),
      },
      {
        key: "cost",
        header: "Cost",
        sortable: true,
        align: "right",
        render: (row) => formatCost(row.cost),
      },
      {
        key: "percentOfTeamTotal",
        header: "% of team",
        sortable: true,
        align: "right",
        render: (row) => (
          <Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
            <LinearProgress
              variant="determinate"
              value={row.percentOfTeamTotal * 100}
              sx={{ width: 72, height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {formatPercent(row.percentOfTeamTotal)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "requestCount",
        header: "Requests",
        sortable: true,
        align: "right",
        render: (row) => row.requestCount.toLocaleString("en-US"),
      },
      {
        key: "avgTokensPerRequest",
        header: "Avg tokens/req",
        sortable: true,
        align: "right",
        render: (row) => formatTokens(row.avgTokensPerRequest),
      },
    ],
    [],
  );

  const teamNotFound =
    teamsQuery.isSuccess && team === null && Boolean(teamId);

  if (teamNotFound) {
    return (
      <EmptyState
        title="Team not found"
        description="This team may have been removed."
        action={{
          label: "Back to All Teams",
          onClick: () => navigate("/usage/teams"),
        }}
      />
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Button
        variant="text"
        size="small"
        startIcon={<IconArrowLeft size={14} />}
        onClick={() => navigate("/usage/teams")}
        sx={{ mb: 1, ml: -0.5, alignSelf: "flex-start" }}
      >
        All Teams
      </Button>

      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 2,
        }}
      >
        <Box>
          {teamsQuery.isPending ? (
            <Skeleton width={160} height={28} sx={{ mb: 0.5 }} />
          ) : (
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {team?.teamName ?? "Team Usage"}
            </Typography>
          )}
          <Typography variant="body2" sx={{ color: tokens.textMuted }}>
            Token and cost breakdown by user
          </Typography>
        </Box>
      </Box>

      <PeriodSelector value={period} onChange={setPeriod} />

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "16px",
        }}
      >
        {(teamsQuery.isPending || usersQuery.isPending) && (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        )}

        {(teamsQuery.isError || usersQuery.isError) && (
          <Box sx={{ gridColumn: "1 / -1" }}>
            <SectionError />
          </Box>
        )}

        {team && usersQuery.data && !teamsQuery.isPending && !usersQuery.isPending && (
          <>
            <StatCard
              label="Team Tokens"
              value={formatTokens(team.tokens)}
              icon={IconActivity}
              iconColor={tokens.primary}
            />
            <StatCard
              label="Team Cost"
              value={formatCost(team.cost)}
              icon={IconCurrencyDollar}
              iconColor={tokens.success}
            />
            <StatCard
              label="Active Members"
              value={activeMemberCount}
              icon={IconUsers}
              iconColor="#F59E0B"
            />
            <StatCard
              label="Avg per Member"
              value={formatTokens(
                activeMemberCount > 0 ? team.tokens / activeMemberCount : 0,
              )}
              icon={IconChartBar}
              iconColor="#8B5CF6"
            />
          </>
        )}
      </Box>

      <Card>
        <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              gap: 2,
              mb: 2,
            }}
          >
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Daily Usage
              </Typography>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {team?.teamName
                  ? `${team.teamName} token activity`
                  : "Team token activity"}
              </Typography>
            </Box>
            <ToggleButtonGroup
              size="small"
              exclusive
              value={chartMode}
              onChange={(_, value: ChartMode | null) => {
                if (value) {
                  setChartMode(value);
                }
              }}
            >
              <ToggleButton value="tokens">Tokens</ToggleButton>
              <ToggleButton value="cost">Cost</ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {dailyQuery.isError ? (
            <SectionError />
          ) : dailyQuery.isLoading ? (
            <Skeleton
              animation="wave"
              variant="rounded"
              width="100%"
              height={200}
              sx={{ borderRadius: "8px" }}
            />
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={dailyQuery.data ?? []}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={tokens.border}
                />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: tokens.textMuted }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tickFormatter={(value: number) =>
                    chartMode === "tokens"
                      ? formatTokens(value)
                      : `$${value.toFixed(2)}`
                  }
                  tick={{ fontSize: 11, fill: tokens.textMuted }}
                  width={65}
                />
                <Tooltip
                  formatter={(value) =>
                    chartMode === "tokens"
                      ? [formatTokens(value as number), "Tokens"]
                      : [formatCost(value as number), "Cost"]
                  }
                  contentStyle={{
                    fontSize: 12,
                    border: `0.5px solid ${tokens.border}`,
                    borderRadius: 8,
                  }}
                />
                {chartMode === "tokens" ? (
                  <Line
                    type="monotone"
                    dataKey="tokens"
                    stroke={tokens.primary}
                    strokeWidth={2}
                    dot={false}
                  />
                ) : (
                  <Line
                    type="monotone"
                    dataKey="cost"
                    stroke={tokens.success}
                    strokeWidth={2}
                    dot={false}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {usersQuery.isError ? (
        <SectionError />
      ) : (
        <Card>
          <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
              User Breakdown
            </Typography>
            <DataTable
              columns={columns}
              rows={sortedUsers}
              rowKey={(row) => row.userId}
              loading={usersQuery.isPending}
              emptyTitle="No usage data"
              emptyDescription="No usage recorded for this team in the selected period."
            />
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

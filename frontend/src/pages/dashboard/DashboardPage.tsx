import {
  IconActivity,
  IconCurrencyDollar,
  IconTool,
  IconUsers,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  LinearProgress,
  Skeleton,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { endOfDay, startOfDay, subDays } from "date-fns";
import { LIVE_DATA_POLL_MS } from "@/config/apiPolling";
import { useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  fetchDashboardStats,
  fetchRecentAlerts,
  fetchTeamCost,
  fetchTokenTimeseries,
  fetchTopUsers,
  type RecentAlert,
  type TeamCostDataPoint,
  type TokenDataPoint,
  type TopUser,
} from "@/api/dashboard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { SkeletonCard } from "@/components/data-display/SkeletonCard";
import { StatCard } from "@/components/data-display/StatCard";
import { EmptyState } from "@/components/feedback/EmptyState";
import { PeriodSelector } from "@/components/inputs/PeriodSelector";
import type { DateRange } from "@/types";
import { tokens } from "@/theme/palette";
import {
  formatCost,
  formatPercent,
  formatRelativeTime,
  formatTokens,
} from "@/utils/formatters";

function createDefaultPeriod(): DateRange {
  const today = new Date();
  return {
    from: startOfDay(subDays(today, 30)).toISOString(),
    to: endOfDay(today).toISOString(),
  };
}

function SectionError() {
  return (
    <Alert severity="error">Failed to load data. Please refresh.</Alert>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
        <Typography
          variant="body2"
          sx={{ fontWeight: 600, color: "text.primary", mb: 0.25 }}
        >
          {title}
        </Typography>
        <Typography variant="caption" sx={{ color: tokens.textMuted, mb: 2, display: "block" }}>
          {subtitle}
        </Typography>
        {children}
      </CardContent>
    </Card>
  );
}

function ChartSkeleton() {
  return (
    <Skeleton
      animation="wave"
      variant="rounded"
      width="100%"
      height={220}
      sx={{ borderRadius: "8px" }}
    />
  );
}

const TOP_USER_COLUMNS: Column<TopUser>[] = [
  { key: "name", header: "User" },
  { key: "team", header: "Team" },
  {
    key: "tokens",
    header: "Tokens",
    align: "right",
    render: (row) => formatTokens(row.tokens),
  },
  {
    key: "cost",
    header: "Cost",
    align: "right",
    render: (row) => formatCost(row.cost),
  },
  {
    key: "percentOfTotal",
    header: "% of total",
    align: "right",
    render: (row) => (
      <Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
        <LinearProgress
          variant="determinate"
          value={row.percentOfTotal * 100}
          sx={{ width: 60, height: 6, borderRadius: 3 }}
        />
        <Typography variant="caption" sx={{ color: tokens.textMuted, minWidth: 36 }}>
          {formatPercent(row.percentOfTotal)}
        </Typography>
      </Box>
    ),
  },
];

function alertDotColor(severity: RecentAlert["severity"]): string {
  switch (severity) {
    case "critical":
      return tokens.critical;
    case "warning":
      return tokens.warning;
    case "info":
      return "#3B82F6";
  }
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState<DateRange>(createDefaultPeriod);

  const statsQuery = useQuery({
    queryKey: ["dashboard", "stats", period.from, period.to],
    queryFn: () => fetchDashboardStats(period.from, period.to),
    refetchInterval: LIVE_DATA_POLL_MS,
  });

  const timeseriesQuery = useQuery({
    queryKey: ["dashboard", "timeseries", period.from, period.to],
    queryFn: () => fetchTokenTimeseries(period.from, period.to),
    refetchInterval: LIVE_DATA_POLL_MS,
  });

  const teamCostQuery = useQuery({
    queryKey: ["dashboard", "teamCost", period.from, period.to],
    queryFn: () => fetchTeamCost(period.from, period.to),
    refetchInterval: LIVE_DATA_POLL_MS,
  });

  const topUsersQuery = useQuery({
    queryKey: ["dashboard", "topUsers", period.from, period.to],
    queryFn: () => fetchTopUsers(period.from, period.to),
    refetchInterval: LIVE_DATA_POLL_MS,
  });

  const alertsQuery = useQuery({
    queryKey: ["dashboard", "recentAlerts"],
    queryFn: fetchRecentAlerts,
    refetchInterval: LIVE_DATA_POLL_MS,
  });

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <PeriodSelector value={period} onChange={setPeriod} />

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "16px",
        }}
      >
        {statsQuery.isLoading && (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        )}

        {statsQuery.isError && (
          <Box sx={{ gridColumn: "1 / -1" }}>
            <SectionError />
          </Box>
        )}

        {statsQuery.data && !statsQuery.isLoading && (
          <>
            <StatCard
              label="Total Tokens"
              value={formatTokens(statsQuery.data.totalTokens)}
              delta={statsQuery.data.tokensDelta}
              deltaLabel="vs prev period"
              icon={IconActivity}
              iconColor={tokens.primary}
            />
            <StatCard
              label="Total Cost"
              value={formatCost(statsQuery.data.totalCost)}
              delta={statsQuery.data.costDelta}
              deltaLabel="vs prev period"
              icon={IconCurrencyDollar}
              iconColor={tokens.success}
            />
            <StatCard
              label="Active Tools"
              value={statsQuery.data.activeTools}
              delta={statsQuery.data.toolsDelta}
              deltaLabel="vs prev period"
              icon={IconTool}
              iconColor="#8B5CF6"
            />
            <StatCard
              label="Active Teams"
              value={statsQuery.data.activeTeams}
              delta={statsQuery.data.teamsDelta}
              deltaLabel="vs prev period"
              icon={IconUsers}
              iconColor="#F59E0B"
            />
          </>
        )}
      </Box>

      {timeseriesQuery.isError ? (
        <SectionError />
      ) : (
        <ChartCard title="Token Usage" subtitle="Daily tokens consumed">
          {timeseriesQuery.isLoading ? (
            <ChartSkeleton />
          ) : (
            <TokenUsageChart data={timeseriesQuery.data ?? []} />
          )}
        </ChartCard>
      )}

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "16px",
        }}
      >
        {teamCostQuery.isError ? (
          <SectionError />
        ) : (
          <ChartCard title="Cost by Team" subtitle="USD spend this period">
            {teamCostQuery.isLoading ? (
              <ChartSkeleton />
            ) : (
              <TeamCostChart data={teamCostQuery.data ?? []} />
            )}
          </ChartCard>
        )}

        {topUsersQuery.isError ? (
          <SectionError />
        ) : (
          <Card sx={{ height: "100%" }}>
            <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
              <Typography
                variant="body2"
                sx={{ fontWeight: 600, color: "text.primary", mb: 2 }}
              >
                Top Users
              </Typography>
              <DataTable
                columns={TOP_USER_COLUMNS}
                rows={topUsersQuery.data ?? []}
                rowKey={(row) => row.id}
                loading={topUsersQuery.isLoading}
                emptyTitle="No usage data"
              />
            </CardContent>
          </Card>
        )}
      </Box>

      {alertsQuery.isError ? (
        <SectionError />
      ) : (
        <Card>
          <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 2,
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Recent Alerts
              </Typography>
              <Button
                variant="text"
                size="small"
                onClick={() => navigate("/alerts")}
              >
                View all
              </Button>
            </Box>

            {alertsQuery.isLoading ? (
              <AlertsSkeleton />
            ) : alertsQuery.data && alertsQuery.data.length > 0 ? (
              <AlertsList alerts={alertsQuery.data} />
            ) : (
              <EmptyState size="sm" title="No recent alerts" />
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

function TokenUsageChart({ data }: { data: TokenDataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={tokens.border} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: tokens.textMuted }}
          interval={4}
        />
        <YAxis
          tickFormatter={(value: number) => formatTokens(value)}
          tick={{ fontSize: 11, fill: tokens.textMuted }}
          width={60}
        />
        <Tooltip
          formatter={(value) => [formatTokens(value as number), "Tokens"]}
          contentStyle={{
            fontSize: 12,
            border: `0.5px solid ${tokens.border}`,
            borderRadius: 8,
          }}
        />
        <Line
          type="monotone"
          dataKey="tokens"
          stroke={tokens.primary}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function TeamCostChart({ data }: { data: TeamCostDataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid vertical={false} stroke={tokens.border} />
        <XAxis
          dataKey="team"
          tick={{ fontSize: 11, fill: tokens.textMuted }}
        />
        <YAxis
          tickFormatter={(value: number) => `$${value}`}
          tick={{ fontSize: 11, fill: tokens.textMuted }}
          width={45}
        />
        <Tooltip
          formatter={(value) => [formatCost(value as number), "Cost"]}
          contentStyle={{
            fontSize: 12,
            border: `0.5px solid ${tokens.border}`,
            borderRadius: 8,
          }}
        />
        <Bar
          dataKey="cost"
          fill={tokens.primary}
          radius={[4, 4, 0, 0]}
          maxBarSize={40}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

function AlertsSkeleton() {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      {Array.from({ length: 5 }).map((_, index) => (
        <Skeleton
          key={index}
          animation="wave"
          height={40}
          width="100%"
          variant="rounded"
        />
      ))}
    </Box>
  );
}

function AlertsList({ alerts }: { alerts: RecentAlert[] }) {
  return (
    <Box>
      {alerts.map((alert, index) => (
        <Box key={alert.id}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              py: 1.5,
              gap: 2,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "flex-start", gap: 1.5, minWidth: 0 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: alertDotColor(alert.severity),
                  flexShrink: 0,
                  mt: 0.75,
                }}
              />
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {alert.title}
                </Typography>
                <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                  {alert.team}
                </Typography>
              </Box>
            </Box>
            <Typography
              variant="caption"
              sx={{ color: tokens.textMuted, flexShrink: 0 }}
            >
              {formatRelativeTime(alert.triggeredAt)}
            </Typography>
          </Box>
          {index < alerts.length - 1 && (
            <Divider sx={{ borderColor: tokens.border, borderWidth: "0.5px" }} />
          )}
        </Box>
      ))}
    </Box>
  );
}

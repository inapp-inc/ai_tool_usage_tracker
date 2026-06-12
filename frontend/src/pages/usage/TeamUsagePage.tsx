import {
  IconActivity,
  IconChartLine,
  IconChevronRight,
  IconCurrencyDollar,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  IconButton,
  LinearProgress,
  Skeleton,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { endOfDay, startOfDay, subDays } from "date-fns";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
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
  fetchUsageSummary,
  type TeamUsageRow,
} from "@/api/usage";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { SkeletonCard } from "@/components/data-display/SkeletonCard";
import { StatCard } from "@/components/data-display/StatCard";
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

function SectionError() {
  return (
    <Alert severity="error">Failed to load data. Please refresh.</Alert>
  );
}

function TrendCell({ trend }: { trend: number }) {
  const isPositive = trend >= 0;
  const color = isPositive ? tokens.success : tokens.critical;
  const prefix = isPositive ? "▲ +" : "▼ -";

  return (
    <Typography variant="body2" sx={{ color, fontWeight: 600 }}>
      {`${prefix}${Math.abs(trend).toFixed(1)}%`}
    </Typography>
  );
}

function BudgetUtilizationCell({ value }: { value: number | null }) {
  if (value == null) {
    return (
      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
        No budget
      </Typography>
    );
  }

  const color = value >= 90 ? "error" : value >= 70 ? "warning" : "primary";

  return (
    <Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
      <LinearProgress
        variant="determinate"
        value={value}
        color={color}
        sx={{ width: 72, height: 6, borderRadius: 3 }}
      />
      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
        {formatPercent(value / 100)}
      </Typography>
    </Box>
  );
}

export function TeamUsagePage() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState<DateRange>(createDefaultPeriod);
  const [chartMode, setChartMode] = useState<ChartMode>("tokens");

  const from = period.from;
  const to = period.to;

  const summaryQuery = useQuery({
    queryKey: ["usage", "summary", from, to],
    queryFn: () => fetchUsageSummary(from, to),
  });

  const teamsQuery = useQuery({
    queryKey: ["usage", "teams", from, to],
    queryFn: () => fetchTeamUsage(from, to),
  });

  const dailyQuery = useQuery({
    queryKey: ["usage", "daily", from, to],
    queryFn: () => fetchDailyUsage(from, to),
  });

  const sortedTeamRows = useMemo(() => {
    const rows = teamsQuery.data ?? [];
    return [...rows].sort((a, b) => b.cost - a.cost);
  }, [teamsQuery.data]);

  const columns: Column<TeamUsageRow>[] = useMemo(
    () => [
      {
        key: "teamName",
        header: "Team",
        sortable: true,
        render: (row) => (
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {row.teamName}
          </Typography>
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
        key: "percentOfTotal",
        header: "% of total",
        sortable: true,
        align: "right",
        render: (row) => (
          <Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
            <LinearProgress
              variant="determinate"
              value={row.percentOfTotal * 100}
              sx={{ width: 72, height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {formatPercent(row.percentOfTotal)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "budgetUtilization",
        header: "Budget",
        render: (row) => (
          <BudgetUtilizationCell value={row.budgetUtilization} />
        ),
      },
      {
        key: "trend",
        header: "Trend",
        sortable: true,
        align: "right",
        render: (row) => <TrendCell trend={row.trend} />,
      },
      {
        key: "actions",
        header: "",
        align: "right",
        render: (row) => (
          <IconButton
            size="small"
            aria-label={`View ${row.teamName} usage`}
            onClick={(event) => {
              event.stopPropagation();
              navigate(`/usage/teams/${row.teamId}`);
            }}
          >
            <IconChevronRight size={15} />
          </IconButton>
        ),
      },
    ],
    [navigate],
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <PeriodSelector value={period} onChange={setPeriod} />

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
        }}
      >
        {summaryQuery.isLoading && (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        )}

        {summaryQuery.isError && (
          <Box sx={{ gridColumn: "1 / -1" }}>
            <SectionError />
          </Box>
        )}

        {summaryQuery.data && !summaryQuery.isLoading && (
          <>
            <StatCard
              label="Total Tokens"
              value={formatTokens(summaryQuery.data.totalTokens)}
              icon={IconActivity}
              iconColor={tokens.primary}
            />
            <StatCard
              label="Total Cost"
              value={formatCost(summaryQuery.data.totalCost)}
              icon={IconCurrencyDollar}
              iconColor={tokens.success}
            />
            <StatCard
              label="Avg Cost / 1K tokens"
              value={formatCost(summaryQuery.data.avgCostPerToken * 1000)}
              icon={IconChartLine}
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
                Tokens consumed per day
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

      {teamsQuery.isError ? (
        <SectionError />
      ) : (
        <Card>
          <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
            <Typography
              variant="body2"
              sx={{ fontWeight: 600, mb: 2 }}
            >
              Usage by Team
            </Typography>
            <DataTable
              columns={columns}
              rows={sortedTeamRows}
              rowKey={(row) => row.teamId}
              loading={teamsQuery.isPending}
              emptyTitle="No usage data"
              emptyDescription="No token usage recorded for this period."
              onRowClick={(row) => navigate(`/usage/teams/${row.teamId}`)}
            />
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

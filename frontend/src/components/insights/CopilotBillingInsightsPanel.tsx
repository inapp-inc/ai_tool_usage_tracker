import {
  IconCurrencyDollar,
  IconHash,
  IconReceipt,
  IconTrendingUp,
  IconUsers,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  LinearProgress,
  Skeleton,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";
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

import { fetchCopilotBillingDayUsers, fetchCopilotBillingInsights } from "@/api/copilot";
import type { CopilotBillingPeriodUser } from "@/api/copilot";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatCard } from "@/components/data-display/StatCard";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { tokens } from "@/theme/palette";
import { formatCost, formatPercent } from "@/utils/formatters";

type PeriodRow = {
  key: string;
  period: string;
  sku: string;
  monthlyCostLimit: number;
  additionalCost: number;
  creditsCost: number;
  totalCost: number;
  seatCount: string;
  fileName: string;
};

type TopUserRow = {
  id: string;
  userLogin: string;
  displayName: string;
  quantity: number;
  grossCost: number;
  netCost: number;
  percentOfTotal: number;
};

type CostTrendPoint = {
  label: string;
  isoDate: string;
  cost: number;
  onDate: string;
};

function CopilotCostTooltip({
  totalCost,
  monthlyLimit,
  additionalCost,
  creditsCost,
  configuredTotal,
}: {
  totalCost: number;
  monthlyLimit: number;
  additionalCost: number;
  creditsCost: number;
  configuredTotal: number | null;
}) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Total cost: {formatCost(totalCost)}
      </Typography>
      <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.85)" }}>
        Subscription limit + additional spend
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Subscription limit: {formatCost(monthlyLimit)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Additional (net − subscription): {formatCost(additionalCost)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        AI credits: {formatCost(creditsCost)}
      </Typography>
      {configuredTotal != null && (
        <>
          <Divider sx={{ my: 0.5, borderColor: "rgba(255,255,255,0.2)" }} />
          <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
            Configured total: {formatCost(configuredTotal)}
          </Typography>
        </>
      )}
    </Box>
  );
}

function CopilotQuantityTooltip({
  quantities,
}: {
  quantities: {
    total: number;
    aiCredits: number;
    userMonths: number;
  };
}) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Total quantity: {quantities.total}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        AI credits: {quantities.aiCredits}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        User-months: {quantities.userMonths}
      </Typography>
    </Box>
  );
}

function resolveCostTrendPoint(
  rows: CostTrendPoint[],
  state: unknown,
): CostTrendPoint | undefined {
  const chartState = state as {
    activeLabel?: string | number;
    activeTooltipIndex?: number;
    activeIndex?: number;
    activePayload?: Array<{ payload?: CostTrendPoint }>;
  };

  const fromPayload = chartState.activePayload?.[0]?.payload;
  if (fromPayload) {
    return fromPayload;
  }

  if (chartState.activeLabel != null) {
    const match = rows.find((row) => row.label === String(chartState.activeLabel));
    if (match) {
      return match;
    }
  }

  const index = chartState.activeTooltipIndex ?? chartState.activeIndex;
  if (typeof index === "number" && rows[index]) {
    return rows[index];
  }

  return undefined;
}

function CostTrendTooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload?: CostTrendPoint; value?: number | string }>;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const point = payload[0].payload as CostTrendPoint | undefined;
  const cost =
    point?.cost != null
      ? Number(point.cost)
      : Number(payload[0].value ?? 0);

  return (
    <Box
      sx={{
        backgroundColor: "#000",
        color: "#fff",
        borderRadius: 1,
        px: 1.5,
        py: 1,
      }}
    >
      <Typography variant="caption" sx={{ display: "block", fontWeight: 700, color: "#fff" }}>
        {point?.label ?? "Billing period"}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Gross cost: {formatCost(cost)}
      </Typography>
    </Box>
  );
}

function ChartCostTooltipContent({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value?: number | string; name?: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const cost = Number(payload[0].value ?? 0);

  return (
    <Box
      sx={{
        backgroundColor: "#000",
        color: "#fff",
        borderRadius: 1,
        px: 1.5,
        py: 1,
      }}
    >
      {label && (
        <Typography variant="caption" sx={{ display: "block", fontWeight: 700, color: "#fff" }}>
          {label}
        </Typography>
      )}
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        {payload[0].name ?? "Cost"}: {formatCost(cost)}
      </Typography>
    </Box>
  );
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function UserAvatar({ name }: { name: string }) {
  return (
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
      {getInitials(name)}
    </Box>
  );
}

function BillingSummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <Box
      sx={{
        flex: 1,
        backgroundColor: tokens.bgDefault,
        borderRadius: 1,
        p: "10px 14px",
      }}
    >
      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 600 }}>
        {value}
      </Typography>
    </Box>
  );
}

function BillingPeriodBreakdown({
  users,
  dayGross,
  totalGross,
  totalNet,
  loading,
  error,
  onUserClick,
}: {
  users: CopilotBillingPeriodUser[];
  dayGross: number | null;
  totalGross: number;
  totalNet: number;
  loading: boolean;
  error: boolean;
  onUserClick?: (user: CopilotBillingPeriodUser) => void;
}) {
  if (loading) {
    return (
      <Box>
        <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
          <Skeleton variant="rounded" width="50%" height={52} />
          <Skeleton variant="rounded" width="50%" height={52} />
        </Box>
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} variant="rounded" height={36} sx={{ mb: 1 }} />
        ))}
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Unable to load user breakdown for this period.</Alert>;
  }

  if (users.length === 0) {
    return (
      <EmptyState
        size="sm"
        title="No user rows in this period"
        description="Map user_login on CSV rows with per-user billing lines to see a breakdown."
      />
    );
  }

  const grossBase = dayGross ?? totalGross;

  return (
    <Box>
      <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
        <BillingSummaryStat
          label="Day gross"
          value={formatCost(dayGross ?? totalGross)}
        />
        <BillingSummaryStat label="User net" value={formatCost(totalNet)} />
      </Box>

      <Typography variant="caption" sx={{ color: tokens.textMuted, mb: 1, display: "block" }}>
        Users on this date
      </Typography>

      {users.map((user, index) => {
        const displayName = user.display_name ?? user.user_login;
        const grossCost = Number(user.gross_cost);
        const netCost = Number(user.net_cost);
        const share = grossBase > 0 ? grossCost / grossBase : 0;

        return (
          <Box
            key={user.user_id || user.user_login}
            onClick={onUserClick ? () => onUserClick(user) : undefined}
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              py: 1,
              borderBottom:
                index < users.length - 1 ? `0.5px solid ${tokens.border}` : undefined,
              cursor: onUserClick ? "pointer" : "default",
              borderRadius: 1,
              px: 0.5,
              "&:hover": onUserClick ? { backgroundColor: tokens.bgDefault } : undefined,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.25, minWidth: 0 }}>
              <UserAvatar name={displayName} />
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }} noWrap>
                  {displayName}
                </Typography>
                <Typography variant="caption" sx={{ color: tokens.textMuted }} noWrap>
                  {user.user_login}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexShrink: 0 }}>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {formatCost(grossCost)}
              </Typography>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {formatCost(netCost)}
              </Typography>
              <Typography
                variant="caption"
                sx={{ color: tokens.textMuted, minWidth: 40, textAlign: "right" }}
              >
                {formatPercent(share)}
              </Typography>
            </Box>
          </Box>
        );
      })}
    </Box>
  );
}

function CopilotUserDetailContent({ user, totalGross }: { user: TopUserRow; totalGross: number }) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
        <UserAvatar name={user.displayName} />
        <Box>
          <Typography variant="body1" sx={{ fontWeight: 600 }}>
            {user.displayName}
          </Typography>
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {user.userLogin}
          </Typography>
        </Box>
      </Box>
      <BillingSummaryStat label="Gross spend" value={formatCost(user.grossCost)} />
      <BillingSummaryStat label="Net spend" value={formatCost(user.netCost)} />
      <BillingSummaryStat label="Seat-months" value={String(user.quantity)} />
      <BillingSummaryStat
        label="% of total"
        value={formatPercent(totalGross > 0 ? user.grossCost / totalGross : user.percentOfTotal)}
      />
    </Box>
  );
}

interface CopilotBillingInsightsPanelProps {
  teamId: string;
  toolId: string;
  from: string;
  to: string;
}

export function CopilotBillingInsightsPanel({
  teamId,
  toolId,
  from,
  to,
}: CopilotBillingInsightsPanelProps) {
  const navigate = useNavigate();
  const [dateDrilldown, setDateDrilldown] = useState<{
    open: boolean;
    label: string | null;
    onDate: string | null;
    dayCost: number | null;
  }>({ open: false, label: null, onDate: null, dayCost: null });
  const [userDrilldown, setUserDrilldown] = useState<TopUserRow | null>(null);

  const insightsQuery = useQuery({
    queryKey: ["copilot", "billing-insights", teamId, toolId, from, to],
    queryFn: () => fetchCopilotBillingInsights(teamId, toolId, from, to),
    enabled: Boolean(teamId && toolId),
  });

  const data = insightsQuery.data;
  const monthlyLimit = Number(
    data?.monthly_cost_limit ?? data?.configured_monthly_cost ?? 0,
  );
  const additionalCost = Number(data?.additional_cost ?? 0);
  const creditsCost = Number(data?.credits_cost ?? 0);
  const configuredTotal =
    data?.configured_monthly_cost != null
      ? Number(data.configured_monthly_cost)
      : monthlyLimit > 0
        ? monthlyLimit
        : null;
  const totalCost = Number(data?.total_cost ?? 0);
  const quantities = {
    total: data?.quantities?.total_quantity ?? 0,
    aiCredits: data?.quantities?.ai_credits_quantity ?? 0,
    userMonths: data?.quantities?.user_months_quantity ?? 0,
  };

  const costTrend: CostTrendPoint[] = useMemo(
    () =>
      (data?.cost_trend ?? []).map((point) => {
        const onDate = point.iso_date;
        return {
          label: point.label,
          isoDate: onDate,
          cost: Number(point.cost),
          onDate,
        };
      }),
    [data?.cost_trend],
  );

  const dayUsersQuery = useQuery({
    queryKey: [
      "copilot",
      "billing-day-users",
      teamId,
      toolId,
      dateDrilldown.onDate,
    ],
    queryFn: () =>
      fetchCopilotBillingDayUsers(teamId, toolId, dateDrilldown.onDate!),
    enabled: dateDrilldown.open && dateDrilldown.onDate != null,
  });

  const openDateDrilldown = useCallback((point: CostTrendPoint) => {
    if (!point.onDate) {
      return;
    }
    setDateDrilldown({
      open: true,
      label: point.label,
      onDate: point.onDate,
      dayCost: point.cost,
    });
  }, []);

  const handleTrendChartClick = useCallback(
    (state: unknown) => {
      const point = resolveCostTrendPoint(costTrend, state);
      if (point) {
        openDateDrilldown(point);
      }
    },
    [costTrend, openDateDrilldown],
  );

  const renderTrendDot = useCallback(
    (stroke: string, radius: number) =>
      function TrendDot(props: {
        cx?: number;
        cy?: number;
        payload?: CostTrendPoint;
      }) {
        const { cx = 0, cy = 0, payload } = props;
        if (!payload) {
          return null;
        }
        const clickable = Boolean(payload.onDate);
        return (
          <circle
            cx={cx}
            cy={cy}
            r={radius}
            fill={stroke}
            stroke="#fff"
            strokeWidth={2}
            style={{ cursor: clickable ? "pointer" : "default" }}
            onClick={(event) => {
              event.stopPropagation();
              if (clickable) {
                openDateDrilldown(payload);
              }
            }}
          />
        );
      },
    [openDateDrilldown],
  );

  const skuChartData = useMemo(
    () =>
      (data?.sku_breakdown ?? []).map((row) => ({
        label: row.label,
        cost: Number(row.cost),
      })),
    [data?.sku_breakdown],
  );

  const costComponentData = useMemo(
    () => {
      const subscription = monthlyLimit > 0 ? monthlyLimit : configuredTotal ?? 0;
      return data?.has_import || subscription > 0
        ? [
            { label: "Subscription", cost: subscription },
            { label: "Additional", cost: additionalCost },
            { label: "AI credits", cost: creditsCost },
          ].filter((row) => row.cost > 0)
        : [];
    },
    [additionalCost, configuredTotal, creditsCost, data?.has_import, monthlyLimit],
  );

  const topUserRows: TopUserRow[] = useMemo(() => {
    const users = data?.top_users ?? [];
    const totalGross =
      totalCost > 0 ? totalCost : Math.max(...users.map((u) => Number(u.cost)), 0);
    return users.map((user) => {
      const grossCost = Number(user.cost);
      return {
        id: user.user_id ?? user.user_login,
        userLogin: user.user_login,
        displayName: user.display_name ?? user.user_login,
        quantity: user.quantity,
        grossCost,
        netCost: Number(user.net_cost),
        percentOfTotal: totalGross > 0 ? grossCost / totalGross : 0,
      };
    });
  }, [data?.top_users, totalCost]);

  const openUserDrilldown = useCallback((user: TopUserRow) => {
    setUserDrilldown(user);
  }, []);

  const openPeriodUserDrilldown = useCallback(
    (user: CopilotBillingPeriodUser) => {
      const grossCost = Number(user.gross_cost);
      const dayGross = dateDrilldown.dayCost ?? Number(dayUsersQuery.data?.total_gross ?? 0);
      openUserDrilldown({
        id: user.user_id || user.user_login,
        userLogin: user.user_login,
        displayName: user.display_name ?? user.user_login,
        quantity: user.quantity,
        grossCost,
        netCost: Number(user.net_cost),
        percentOfTotal: dayGross > 0 ? grossCost / dayGross : 0,
      });
    },
    [openUserDrilldown, dateDrilldown.dayCost, dayUsersQuery.data?.total_gross],
  );

  const periodRows: PeriodRow[] =
    data?.periods.map((row, index) => ({
      key: `${row.sku}-${index}`,
      period:
        row.billing_period_start && row.billing_period_end
          ? `${row.billing_period_start} → ${row.billing_period_end}`
          : "—",
      sku: row.sku,
      monthlyCostLimit: Number(row.monthly_cost_limit),
      additionalCost: Number(row.additional_cost),
      creditsCost: Number(row.credits_cost),
      totalCost: Number(row.total_cost),
      seatCount: row.seat_count != null ? String(row.seat_count) : "—",
      fileName: row.upload_filename ?? "—",
    })) ?? [];

  const periodColumns: Column<PeriodRow>[] = [
    { key: "period", header: "Billing period", sortable: true },
    { key: "sku", header: "SKU" },
    {
      key: "monthlyCostLimit",
      header: "Cost limit",
      align: "right",
      render: (row) => formatCost(row.monthlyCostLimit),
    },
    {
      key: "additionalCost",
      header: "Additional",
      align: "right",
      render: (row) => formatCost(row.additionalCost),
    },
    {
      key: "creditsCost",
      header: "AI credits",
      align: "right",
      render: (row) => formatCost(row.creditsCost),
    },
    {
      key: "totalCost",
      header: "Imported total",
      align: "right",
      render: (row) => formatCost(row.totalCost),
    },
    { key: "seatCount", header: "Seats", align: "right" },
    { key: "fileName", header: "Import file" },
  ];

  const topUserColumns: Column<TopUserRow>[] = [
    {
      key: "displayName",
      header: "User",
      render: (row) => (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.25 }}>
          <UserAvatar name={row.displayName} />
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.displayName}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {row.userLogin}
            </Typography>
          </Box>
        </Box>
      ),
    },
    {
      key: "grossCost",
      header: "Gross cost",
      align: "right",
      render: (row) => formatCost(row.grossCost),
    },
    {
      key: "netCost",
      header: "Net cost",
      align: "right",
      render: (row) => formatCost(row.netCost),
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

  if (insightsQuery.isPending) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (insightsQuery.isError) {
    return (
      <Alert severity="error">
        Unable to load Copilot billing insights. Try again or upload billing data.
      </Alert>
    );
  }

  if (!data?.has_config && !data?.has_import) {
    return (
      <EmptyState
        title="No Copilot data yet"
        description="Configure Copilot on the team, then import a billing CSV to see cost insights like your other tools."
        action={{ label: "Go to Uploads", onClick: () => navigate("/uploads") }}
      />
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {data.imports_outside_filter && (
        <Alert severity="info">
          Imported billing periods fall outside the selected date range. Widen the period filter
          above to align with your CSV billing dates.
        </Alert>
      )}
      {data.budget_alert_triggered && (
        <Alert severity="warning">
          Imported spend reached your USD alert threshold
          {data.alert_threshold_usd != null
            ? ` (${formatCost(Number(data.alert_threshold_usd))})`
            : ""}
          .
        </Alert>
      )}

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
        }}
      >
        <StatCard
          label="Total Cost"
          value={data.has_import || configuredTotal != null ? formatCost(totalCost) : "—"}
          icon={IconCurrencyDollar}
          iconColor={tokens.success}
          tooltipContent={
            data.has_import ? (
              <CopilotCostTooltip
                totalCost={totalCost}
                monthlyLimit={monthlyLimit}
                additionalCost={additionalCost}
                creditsCost={creditsCost}
                configuredTotal={configuredTotal}
              />
            ) : undefined
          }
        />
        <StatCard
          label="Subscription limit"
          value={
            monthlyLimit > 0
              ? formatCost(monthlyLimit)
              : configuredTotal != null
                ? formatCost(configuredTotal)
                : "—"
          }
          icon={IconReceipt}
          iconColor={tokens.primary}
        />
        <StatCard
          label="Additional spend"
          value={data.has_import ? formatCost(additionalCost) : "—"}
          icon={IconTrendingUp}
          iconColor="#8B5CF6"
        />
        <StatCard
          label="Total quantity"
          value={
            data.has_import && quantities.total > 0
              ? String(quantities.total)
              : "—"
          }
          icon={IconHash}
          iconColor="#6366F1"
          tooltipContent={
            data.has_import && quantities.total > 0 ? (
              <CopilotQuantityTooltip quantities={quantities} />
            ) : undefined
          }
        />
        <StatCard
          label="Seats billed"
          value={
            quantities.userMonths > 0
              ? String(quantities.userMonths)
              : data.seat_count != null
                ? String(data.seat_count)
                : data.team_size != null
                  ? String(data.team_size)
                  : "—"
          }
          icon={IconUsers}
          iconColor="#F59E0B"
        />
      </Box>

      {configuredTotal != null && data.has_import && configuredTotal !== totalCost && (
        <Alert severity={totalCost > configuredTotal ? "warning" : "info"}>
          Configured subscription total is {formatCost(configuredTotal)} — imported billing is{" "}
          {formatCost(totalCost)} (
          {totalCost > configuredTotal ? "over" : "under"} by{" "}
          {formatCost(Math.abs(totalCost - configuredTotal))}).
        </Alert>
      )}

      <Card>
        <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Billing cost trend
          </Typography>
          <Typography variant="caption" sx={{ color: tokens.textMuted, mb: 2, display: "block" }}>
            Daily imported billing cost
          </Typography>
          {!data.has_import || costTrend.length === 0 ? (
            <Alert severity="info" sx={{ mt: 1 }}>
              No billing CSV imported for this period. Upload Copilot billing data in Uploads.
            </Alert>
          ) : (
            <Box>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart
                  data={costTrend}
                  onClick={handleTrendChartClick}
                  style={{ cursor: "pointer" }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={tokens.border} />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 11, fill: tokens.textMuted }}
                    interval="preserveStartEnd"
                    minTickGap={20}
                  />
                  <YAxis
                    tickFormatter={(value: number) => formatCost(value)}
                    tick={{ fontSize: 11, fill: tokens.textMuted }}
                    width={72}
                  />
                  <Tooltip
                    content={(props) => <CostTrendTooltipContent {...props} />}
                  />
                  <Line
                    type="monotone"
                    dataKey="cost"
                    stroke={tokens.success}
                    strokeWidth={2}
                    dot={renderTrendDot(tokens.success, 4)}
                    activeDot={renderTrendDot(tokens.success, 6)}
                  />
                </LineChart>
              </ResponsiveContainer>
              <Typography variant="caption" sx={{ color: tokens.textMuted, mt: 1, display: "block" }}>
                Click any day to see user spend for that date.
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "16px",
        }}
      >
        <Card sx={{ height: "100%" }}>
          <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.25 }}>
              Cost breakdown
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: tokens.textMuted, mb: 2, display: "block" }}
            >
              Subscription vs additional vs AI credits
            </Typography>
            {!data.has_import || costComponentData.length === 0 ? (
              <Typography variant="body2" sx={{ color: tokens.textMuted }}>
                No imported cost components yet.
              </Typography>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={costComponentData}>
                  <CartesianGrid vertical={false} stroke={tokens.border} />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: tokens.textMuted }} />
                  <YAxis
                    tickFormatter={(value: number) => formatCost(value)}
                    tick={{ fontSize: 11, fill: tokens.textMuted }}
                    width={72}
                  />
                  <Tooltip
                    content={(props) => <ChartCostTooltipContent {...props} />}
                  />
                  <Bar
                    dataKey="cost"
                    fill={tokens.primary}
                    radius={[4, 4, 0, 0]}
                    maxBarSize={48}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card sx={{ height: "100%" }}>
          <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
              Top Users
            </Typography>
            <DataTable
              columns={topUserColumns}
              rows={topUserRows}
              rowKey={(row) => row.id}
              emptyTitle="No user-level billing rows"
              emptyDescription="Map user_login on CSV rows to see per-user gross costs."
              onRowClick={openUserDrilldown}
            />
          </CardContent>
        </Card>
      </Box>

      {skuChartData.length > 1 && (
        <Card>
          <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.25 }}>
              Cost by SKU
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: tokens.textMuted, mb: 2, display: "block" }}
            >
              Imported totals grouped by GitHub billing SKU
            </Typography>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={skuChartData}>
                <CartesianGrid vertical={false} stroke={tokens.border} />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: tokens.textMuted }} />
                <YAxis
                  tickFormatter={(value: number) => formatCost(value)}
                  tick={{ fontSize: 11, fill: tokens.textMuted }}
                  width={72}
                />
                <Tooltip
                  content={(props) => <ChartCostTooltipContent {...props} />}
                />
                <Bar dataKey="cost" fill="#8B5CF6" radius={[4, 4, 0, 0]} maxBarSize={56} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {data.has_import && (
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              Imported billing periods
            </Typography>
            <DataTable
              columns={periodColumns}
              rows={periodRows}
              rowKey={(row) => row.key}
              emptyTitle="No periods in range"
              emptyDescription="Adjust the date filter or import billing data for this period."
            />
          </CardContent>
        </Card>
      )}
      <SlideOver
        open={dateDrilldown.open}
        onClose={() =>
          setDateDrilldown({
            open: false,
            label: null,
            onDate: null,
            dayCost: null,
          })
        }
        title={dateDrilldown.label ?? "Billing day"}
        subtitle="Gross and net spend by user for this date"
        width={520}
      >
        <BillingPeriodBreakdown
          users={dayUsersQuery.data?.users ?? []}
          dayGross={dateDrilldown.dayCost}
          totalGross={Number(dayUsersQuery.data?.total_gross ?? 0)}
          totalNet={Number(dayUsersQuery.data?.total_net ?? 0)}
          loading={dayUsersQuery.isPending}
          error={dayUsersQuery.isError}
          onUserClick={openPeriodUserDrilldown}
        />
      </SlideOver>

      <SlideOver
        open={userDrilldown !== null}
        onClose={() => setUserDrilldown(null)}
        width={480}
        title={userDrilldown?.displayName ?? ""}
        subtitle={userDrilldown?.userLogin ?? ""}
      >
        {userDrilldown && (
          <CopilotUserDetailContent user={userDrilldown} totalGross={totalCost} />
        )}
      </SlideOver>
    </Box>
  );
}

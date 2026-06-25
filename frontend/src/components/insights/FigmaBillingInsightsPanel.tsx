import {
  IconCurrencyDollar,
  IconReceipt,
  IconTrendingUp,
  IconUsers,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  CircularProgress,
  Divider,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
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
  fetchFigmaBillingDayUsers,
  fetchFigmaBillingInsights,
  type FigmaBillingPeriodUser,
} from "@/api/figma";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatCard } from "@/components/data-display/StatCard";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { tokens } from "@/theme/palette";
import {
  insightsChartTooltipItemStyle,
  insightsChartTooltipLabelStyle,
  insightsChartTooltipStyle,
} from "@/components/insights/chartTooltipStyles";
import { formatCost, formatDate, formatPercent } from "@/utils/formatters";

type PeriodRow = {
  key: string;
  period: string;
  subscriptionCost: number;
  paidCredits: number;
  additionalCost: number;
  totalCost: number;
  seats: string;
  fileName: string;
};

type TopUserRow = {
  id: string;
  displayName: string;
  email: string;
  seatType: string;
  seatCredits: number;
  paidCredits: number;
  seatCost: number;
  paidCost: number;
  totalCost: number;
  percentOfTotal: number;
};

type CostTrendPoint = {
  label: string;
  isoDate: string;
  cost: number;
  dailyCost: number;
  onDate: string;
};

function FigmaCostTrendTooltipContent({
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
  const cumulative =
    point?.cost != null ? Number(point.cost) : Number(payload[0].value ?? 0);
  const daily = point?.dailyCost ?? 0;
  const dateLabel = point?.isoDate ? formatDate(point.isoDate) : point?.label ?? "Date";

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
        {dateLabel}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Total to date: {formatCost(cumulative)}
      </Typography>
      {daily > 0 && (
        <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
          This day: {formatCost(daily)}
        </Typography>
      )}
    </Box>
  );
}

interface FigmaBillingInsightsPanelProps {
  teamId: string;
  toolId: string;
}

const FIGMA_ALL_TIME_FROM = "2020-01-01T00:00:00.000Z";
const FIGMA_ALL_TIME_TO = "2030-12-31T23:59:59.000Z";

function formatBillingPeriodLabel(start: string | null, end: string | null, fileName?: string | null) {
  const range =
    start && end ? `${start} → ${end}` : start ?? end ?? "Unknown period";
  return fileName ? `${range} (${fileName})` : range;
}

export function FigmaBillingInsightsPanel({
  teamId,
  toolId,
}: FigmaBillingInsightsPanelProps) {
  const navigate = useNavigate();
  const [selectedImportId, setSelectedImportId] = useState<string | null>(null);
  const [dateDrilldown, setDateDrilldown] = useState<{
    open: boolean;
    label: string | null;
    onDate: string | null;
  }>({ open: false, label: null, onDate: null });
  const [userDrilldown, setUserDrilldown] = useState<TopUserRow | null>(null);

  useEffect(() => {
    setSelectedImportId(null);
  }, [teamId, toolId]);

  const insightsQuery = useQuery({
    queryKey: ["figma", "billing-insights", teamId, toolId, selectedImportId],
    queryFn: () =>
      fetchFigmaBillingInsights(
        teamId,
        toolId,
        FIGMA_ALL_TIME_FROM,
        FIGMA_ALL_TIME_TO,
        selectedImportId ? { importId: selectedImportId } : undefined,
      ),
    enabled: Boolean(teamId && toolId),
  });

  const data = insightsQuery.data;

  useEffect(() => {
    if (selectedImportId != null || !data?.available_periods?.length) {
      return;
    }
    setSelectedImportId(data.available_periods[0].import_id);
  }, [data?.available_periods, selectedImportId]);
  const subscriptionTotal =
    data?.configured_seat_cost != null
      ? Number(data.configured_seat_cost)
      : Number(data?.seat_cost ?? 0);
  const paidCredits = Number(data?.credits?.total_paid_credits_used ?? 0);
  const seatCredits = Number(data?.credits?.total_seat_credits_used ?? 0);
  const usdPerCredit =
    data?.credits_per_usd != null ? Number(data.credits_per_usd) : null;
  const additionalCost =
    usdPerCredit != null && paidCredits > 0
      ? paidCredits * usdPerCredit
      : Number(data?.paid_cost ?? 0);
  const displayTotal = data?.has_import
    ? subscriptionTotal + additionalCost
    : subscriptionTotal > 0
      ? subscriptionTotal
      : 0;

  const costTrend: CostTrendPoint[] = useMemo(
    () =>
      (data?.cost_trend ?? []).map((point) => ({
        label: point.label,
        isoDate: point.iso_date,
        cost: Number(point.cost),
        dailyCost: Number(point.daily_cost ?? 0),
        onDate: point.iso_date,
      })),
    [data?.cost_trend],
  );

  const trendPeriodLabel = useMemo(() => {
    if (data?.active_billing_period_start && data?.active_billing_period_end) {
      return `${formatDate(data.active_billing_period_start)} – ${formatDate(data.active_billing_period_end)}`;
    }
    if (costTrend.length > 0) {
      const first = costTrend[0].isoDate;
      const last = costTrend[costTrend.length - 1].isoDate;
      return `${formatDate(first)} – ${formatDate(last)}`;
    }
    return null;
  }, [costTrend, data?.active_billing_period_end, data?.active_billing_period_start]);

  const dayUsersQuery = useQuery({
    queryKey: ["figma", "billing-day-users", teamId, toolId, dateDrilldown.onDate],
    queryFn: () => fetchFigmaBillingDayUsers(teamId, toolId, dateDrilldown.onDate!),
    enabled: dateDrilldown.open && dateDrilldown.onDate != null,
  });

  const costComponentData = useMemo(
    () =>
      data?.has_import || subscriptionTotal > 0
        ? [
            { label: "Subscription", cost: subscriptionTotal },
            { label: "Additional cost", cost: additionalCost },
          ].filter((row) => row.cost > 0)
        : [],
    [additionalCost, data?.has_import, subscriptionTotal],
  );

  const topUserRows: TopUserRow[] = useMemo(() => {
    const users = data?.top_users ?? [];
    const additionalBase =
      additionalCost > 0
        ? additionalCost
        : Math.max(...users.map((u) => Number(u.paid_cost_usd)), 0);
    return users.map((user) => {
      const paidCost = Number(user.paid_cost_usd);
      return {
        id: user.figma_user_id ?? user.user_email ?? user.user_name ?? "unknown",
        displayName: user.user_name ?? user.user_email ?? "Unknown",
        email: user.user_email ?? "—",
        seatType: user.seat_type ?? "—",
        seatCredits: Number(user.seat_credits_used),
        paidCredits: Number(user.paid_credits_used),
        seatCost: Number(user.seat_cost_usd),
        paidCost,
        totalCost: paidCost,
        percentOfTotal: additionalBase > 0 ? paidCost / additionalBase : 0,
      };
    });
  }, [additionalCost, data?.top_users]);

  const periodRows: PeriodRow[] =
    data?.periods.map((row, index) => {
      const periodPaidCredits = Number(row.paid_credits_used ?? 0);
      const periodAdditional =
        usdPerCredit != null && periodPaidCredits > 0
          ? periodPaidCredits * usdPerCredit
          : Number(row.paid_cost);
      const periodSubscription = Number(row.seat_cost) || subscriptionTotal;
      return {
        key: `period-${index}`,
        period:
          row.usage_period_start && row.usage_period_end
            ? `${row.usage_period_start} → ${row.usage_period_end}`
            : "—",
        subscriptionCost: periodSubscription,
        paidCredits: periodPaidCredits,
        additionalCost: periodAdditional,
        totalCost: periodSubscription + periodAdditional,
        seats: `${row.full_seat_count} full / ${row.view_seat_count} view`,
        fileName: row.upload_filename ?? "—",
      };
    }) ?? [];

  const openDateDrilldown = useCallback((point: CostTrendPoint) => {
    if (!point.onDate) {
      return;
    }
    setDateDrilldown({ open: true, label: point.label, onDate: point.onDate });
  }, []);

  const periodColumns: Column<PeriodRow>[] = [
    { key: "period", header: "Usage period", sortable: true },
    {
      key: "subscriptionCost",
      header: "Subscription",
      align: "right",
      render: (row) => formatCost(row.subscriptionCost),
    },
    {
      key: "paidCredits",
      header: "Additional credits",
      align: "right",
      render: (row) => row.paidCredits.toLocaleString(),
    },
    {
      key: "additionalCost",
      header: "Additional cost",
      align: "right",
      render: (row) => formatCost(row.additionalCost),
    },
    {
      key: "totalCost",
      header: "Total",
      align: "right",
      render: (row) => formatCost(row.totalCost),
    },
    { key: "seats", header: "Seats" },
    { key: "fileName", header: "Import file" },
  ];

  const topUserColumns: Column<TopUserRow>[] = [
    {
      key: "displayName",
      header: "User",
      render: (row) => (
        <Box>
          <Typography variant="body2">{row.displayName}</Typography>
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {row.email}
          </Typography>
        </Box>
      ),
    },
    { key: "seatType", header: "Seat" },
    {
      key: "seatCredits",
      header: "Seat credits used",
      align: "right",
      render: (row) => row.seatCredits.toLocaleString(),
    },
    {
      key: "paidCredits",
      header: "Additional credits",
      align: "right",
      render: (row) => row.paidCredits.toLocaleString(),
    },
    {
      key: "paidCost",
      header: "Additional cost",
      align: "right",
      render: (row) => formatCost(row.paidCost),
    },
    {
      key: "percentOfTotal",
      header: "% of additional",
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

  const dayUserColumns: Column<FigmaBillingPeriodUser>[] = [
    {
      key: "user",
      header: "User",
      render: (row) => row.user_name ?? row.user_email ?? "—",
    },
    { key: "seat_type", header: "Seat" },
    {
      key: "paid_credits_used",
      header: "Additional credits",
      align: "right",
      render: (row) => Number(row.paid_credits_used).toLocaleString(),
    },
    {
      key: "paid_cost_usd",
      header: "Additional cost",
      align: "right",
      render: (row) => formatCost(Number(row.paid_cost_usd)),
    },
    {
      key: "total_cost_usd",
      header: "Total",
      align: "right",
      render: (row) => formatCost(Number(row.total_cost_usd)),
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
        Unable to load Figma billing insights. Try again or upload billing data.
      </Alert>
    );
  }

  if (!data?.has_config && !data?.has_import) {
    return (
      <EmptyState
        title="No Figma data yet"
        description="Configure Figma seat pricing on the team, then import a billing CSV to see cost insights."
        action={{ label: "Go to Uploads", onClick: () => navigate("/uploads") }}
      />
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {(data?.available_periods?.length ?? 0) > 0 && (
        <FormControl size="small" sx={{ maxWidth: 480 }}>
          <InputLabel id="figma-billing-period-label">Billing period (from CSV)</InputLabel>
          <Select
            labelId="figma-billing-period-label"
            label="Billing period (from CSV)"
            value={selectedImportId ?? ""}
            onChange={(event) => setSelectedImportId(String(event.target.value))}
          >
            {(data?.available_periods ?? []).map((period) => (
              <MenuItem key={period.import_id} value={period.import_id}>
                {formatBillingPeriodLabel(
                  period.usage_period_start,
                  period.usage_period_end,
                  period.upload_filename,
                )}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}

      {data?.active_billing_period_start && data?.active_billing_period_end && (
        <Alert severity="info">
          Showing Figma usage for CSV period{" "}
          {data.active_billing_period_start} → {data.active_billing_period_end}. Seat credits
          are included in subscription; additional credits are billed separately.
        </Alert>
      )}

      {data?.budget_alert_triggered && (
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
          label="Total cost"
          value={
            data.has_import || subscriptionTotal > 0 ? formatCost(displayTotal) : "—"
          }
          icon={IconCurrencyDollar}
          iconColor={tokens.success}
        />
        <StatCard
          label="Subscription (configured)"
          value={subscriptionTotal > 0 ? formatCost(subscriptionTotal) : "—"}
          icon={IconReceipt}
          iconColor={tokens.primary}
        />
        <StatCard
          label="Additional credits"
          value={data.has_import && paidCredits > 0 ? paidCredits.toLocaleString() : "—"}
          icon={IconTrendingUp}
          iconColor="#8B5CF6"
        />
        <StatCard
          label="Additional cost"
          value={data.has_import ? formatCost(additionalCost) : "—"}
          icon={IconTrendingUp}
          iconColor="#EC4899"
        />
        <StatCard
          label="Seat credits used"
          value={
            data.has_import && seatCredits > 0
              ? seatCredits.toLocaleString()
              : "—"
          }
          icon={IconUsers}
          iconColor="#F59E0B"
        />
      </Box>

      {(subscriptionTotal > 0 || usdPerCredit != null) && (
        <Alert severity="info">
          {subscriptionTotal > 0 && (
            <>Configured subscription: {formatCost(subscriptionTotal)} · </>
          )}
          {seatCredits > 0 && (
            <>
              Seat credits used: {seatCredits.toLocaleString()} (included in subscription) ·{" "}
            </>
          )}
          {usdPerCredit != null && data.has_import && paidCredits > 0 && (
            <>
              Additional credits: {paidCredits.toLocaleString()} × ${usdPerCredit} ={" "}
              {formatCost(additionalCost)} · Total: {formatCost(displayTotal)}
            </>
          )}
          {usdPerCredit != null && (!data.has_import || paidCredits === 0) && (
            <>Additional cost = paid credits used × ${usdPerCredit} per credit.</>
          )}
        </Alert>
      )}

      {costTrend.length > 0 && (
        <Box
          sx={{
            p: 2,
            borderRadius: 1,
            border: `0.5px solid ${tokens.border}`,
            backgroundColor: tokens.bgDefault,
          }}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Monthly cost trend
          </Typography>
          {trendPeriodLabel && (
            <Typography variant="caption" sx={{ color: tokens.textMuted, mb: 2, display: "block" }}>
              {trendPeriodLabel}
              {displayTotal > 0 && ` · Period total: ${formatCost(displayTotal)}`}
            </Typography>
          )}
          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={costTrend}
              onClick={(state) => {
                const index = (state as { activeTooltipIndex?: number }).activeTooltipIndex;
                if (typeof index === "number" && costTrend[index]) {
                  openDateDrilldown(costTrend[index]);
                }
              }}
              style={{ cursor: "pointer" }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={tokens.border} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: tokens.textMuted }}
                interval="preserveStartEnd"
                minTickGap={24}
              />
              <YAxis
                tick={{ fontSize: 11, fill: tokens.textMuted }}
                tickFormatter={(value: number) => formatCost(value)}
                width={72}
              />
              <Tooltip content={(props) => <FigmaCostTrendTooltipContent {...props} />} />
              <Line
                type="monotone"
                dataKey="cost"
                name="Total to date"
                stroke={tokens.primary}
                strokeWidth={2}
                dot={{ r: 3, cursor: "pointer" }}
                activeDot={{ r: 5, cursor: "pointer" }}
              />
            </LineChart>
          </ResponsiveContainer>
          <Typography variant="caption" sx={{ color: tokens.textMuted, mt: 1, display: "block" }}>
            Click a date to see users active that day.
          </Typography>
        </Box>
      )}

      {costComponentData.length > 0 && (
        <Box
          sx={{
            p: 2,
            borderRadius: 1,
            border: `0.5px solid ${tokens.border}`,
            backgroundColor: tokens.bgDefault,
          }}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
            Cost breakdown
          </Typography>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={costComponentData}>
              <CartesianGrid strokeDasharray="3 3" stroke={tokens.border} />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
              <Tooltip
                formatter={(value) => formatCost(Number(value))}
                contentStyle={insightsChartTooltipStyle}
                labelStyle={insightsChartTooltipLabelStyle}
                itemStyle={insightsChartTooltipItemStyle}
              />
              <Bar dataKey="cost" fill={tokens.primary} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Box>
      )}

      {topUserRows.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            Users in billing period ({topUserRows.length})
          </Typography>
          <DataTable
            columns={topUserColumns}
            rows={topUserRows}
            rowKey={(row) => row.id}
            onRowClick={(row) => setUserDrilldown(row)}
            stickyHeader
          />
        </Box>
      )}

      {periodRows.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            Imported periods
          </Typography>
          <DataTable
            columns={periodColumns}
            rows={periodRows}
            rowKey={(row) => row.key}
            stickyHeader
          />
        </Box>
      )}

      <SlideOver
        open={dateDrilldown.open}
        onClose={() => setDateDrilldown({ open: false, label: null, onDate: null })}
        title={`Users on ${dateDrilldown.label ?? ""}`}
        width={640}
      >
        {dayUsersQuery.isPending ? (
          <CircularProgress size={24} />
        ) : (
          <DataTable
            columns={dayUserColumns}
            rows={dayUsersQuery.data?.users ?? []}
            rowKey={(row) => row.figma_user_id ?? row.user_email ?? row.user_name ?? "row"}
            emptyTitle="No users for this day"
          />
        )}
      </SlideOver>

      <SlideOver
        open={userDrilldown != null}
        onClose={() => setUserDrilldown(null)}
        title={userDrilldown?.displayName ?? "User"}
        width={480}
      >
        {userDrilldown && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              {userDrilldown.email}
            </Typography>
            <Divider sx={{ my: 1 }} />
            <Typography variant="body2">Seat type: {userDrilldown.seatType}</Typography>
            <Typography variant="body2">
              Seat credits used: {userDrilldown.seatCredits.toLocaleString()} (included in
              subscription)
            </Typography>
            <Typography variant="body2">
              Additional credits: {userDrilldown.paidCredits.toLocaleString()}
            </Typography>
            <Typography variant="body2">
              Additional cost: {formatCost(userDrilldown.paidCost)}
            </Typography>
          </Box>
        )}
      </SlideOver>
    </Box>
  );
}

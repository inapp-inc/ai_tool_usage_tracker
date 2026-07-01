import { zodResolver } from "@hookform/resolvers/zod";
import {
  IconActivity,
  IconBell,
  IconCurrencyDollar,
  IconDownload,
  IconMail,
  IconPlus,
  IconTool,
  IconTrash,
  IconUsers,
} from "@tabler/icons-react";
import {
  Alert,
  Badge,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  Collapse,
  Divider,
  FormControl,
  FormHelperText,
  IconButton,
  InputLabel,
  LinearProgress,
  ListItemText,
  MenuItem,
  Select,
  Skeleton,
  Tab,
  Tabs,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip as MuiTooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type SyntheticEvent,
} from "react";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { z } from "zod";

import {
  fetchDashboardStats,
  fetchOrganizationCostBreakdown,
  fetchOrganizationCosts,
  fetchRecentAlerts,
  fetchTeamCost,
  fetchTopUsers,
  type DashboardStats,
  type OrganizationCostBreakdownItem,
  type OrganizationCostSummary,
  type RecentAlert,
  type TeamCostDataPoint,
  type TopUser,
} from "@/api/dashboard";
import {
  createReport,
  createSubscription,
  deleteReport,
  deleteSubscription,
  downloadReport,
  fetchReports,
  fetchSubscriptions,
  type Report,
  type ReportFormat,
  type ReportSchedule,
  type ReportSubscription,
  type ReportType,
  type SubscriptionCadence,
  type SubscriptionChannel,
} from "@/api/reports";
import { fetchCredentials, type Credential } from "@/api/credentials";
import { fetchTeams, type Team } from "@/api/teams";
import { fetchTeamToolAssignment } from "@/api/teamTools";
import { fetchTools } from "@/api/tools";
import {
  fetchDailyBreakdown,
  fetchDailyUsage,
  fetchTeamUsage,
  fetchToolOptions,
  type DailyBreakdownTeam,
  type DailyUsagePoint,
  type DashboardFilters,
  type TeamUsageRow,
  type UserUsageRow,
} from "@/api/usage";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { SkeletonCard } from "@/components/data-display/SkeletonCard";
import { StatCard } from "@/components/data-display/StatCard";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { TeamDetailSlideOver } from "@/components/insights/TeamDetailSlideOver";
import { CopilotBillingInsightsPanel } from "@/components/insights/CopilotBillingInsightsPanel";
import { FigmaBillingInsightsPanel } from "@/components/insights/FigmaBillingInsightsPanel";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import type { DateRange } from "@/types";
import { Role } from "@/types";
import { useAuthStore } from "@/stores/authStore";
import { useInsightsPeriodStore } from "@/stores/insightsPeriodStore";
import { useOrgScopeStore } from "@/stores/orgScopeStore";
import { tenantScopeKey } from "@/lib/tenantScope";
import { tokens } from "@/theme/palette";
import {
  insightsChartTooltipItemStyle,
  insightsChartTooltipLabelStyle,
  insightsChartTooltipStyle,
} from "@/components/insights/chartTooltipStyles";
import {
  formatCost,
  formatPercent,
  formatRelativeTime,
  formatTokens,
} from "@/utils/formatters";
import { currentMonthUtcRange, currentSubscriptionPeriodRange } from "@/utils/periods";

type ChartMode = "tokens" | "cost" | "bill";

interface InsightsFilters {
  period: DateRange;
  teamId: string;
  toolId: string;
}

const EMPTY_TEAMS: Team[] = [];

const FORMAT_CHIP_COLORS: Record<
  ReportFormat,
  { background: string; color: string }
> = {
  pdf: { background: "#FEE2E2", color: "#DC2626" },
  csv: { background: "#DCFCE7", color: "#16A34A" },
  xlsx: { background: "#EFF6FF", color: "#2563EB" },
};

const SCHEDULE_LABELS: Record<ReportSchedule, string> = {
  once: "Once",
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

const REPORT_TYPE_OPTIONS: Array<{ value: ReportType; label: string }> = [
  { value: "usage_summary", label: "Usage Summary" },
  { value: "cost_breakdown", label: "Cost Breakdown" },
  { value: "team_comparison", label: "Team Comparison" },
  { value: "user_activity", label: "User Activity" },
  { value: "budget_variance", label: "Budget Variance" },
];

const FORMAT_OPTIONS: Array<{ value: ReportFormat; label: string }> = [
  { value: "pdf", label: "PDF" },
  { value: "csv", label: "CSV" },
  { value: "xlsx", label: "Excel" },
];

const SCHEDULE_OPTIONS: Array<{ value: ReportSchedule; label: string }> = [
  { value: "once", label: "Once" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

const reportSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  type: z.enum([
    "usage_summary",
    "cost_breakdown",
    "team_comparison",
    "user_activity",
    "budget_variance",
  ]),
  format: z.enum(["pdf", "csv", "xlsx"]),
  schedule: z.enum(["once", "daily", "weekly", "monthly"]),
  periodFrom: z.string().min(1, "Start date required"),
  periodTo: z.string().min(1, "End date required"),
  teamIds: z.array(z.string()),
});

type ReportFormValues = z.infer<typeof reportSchema>;

const subscribeSchema = z
  .object({
    channel: z.enum(["email", "in_app", "both"]),
    cadence: z.enum(["daily", "weekly", "monthly"]),
    emailRecipients: z.string(),
  })
  .refine(
    (value) =>
      value.channel === "in_app" || value.emailRecipients.trim().length > 0,
    {
      message: "Enter at least one email recipient",
      path: ["emailRecipients"],
    },
  );

type SubscribeFormValues = z.infer<typeof subscribeSchema>;

const SUBSCRIPTION_CADENCE_LABELS: Record<SubscriptionCadence, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

const SUBSCRIPTION_CHANNEL_LABELS: Record<SubscriptionChannel, string> = {
  email: "Email",
  in_app: "In-app",
  both: "Both",
};

const SUBSCRIPTION_CADENCE_OPTIONS: Array<{
  value: SubscriptionCadence;
  label: string;
}> = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

function defaultSubscribeValues(): SubscribeFormValues {
  return {
    channel: "email",
    cadence: "weekly",
    emailRecipients: "",
  };
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength)}…`;
}

function formatSubscriptionRecipients(recipients: string[]): string {
  if (recipients.length === 0) {
    return "";
  }
  return truncateText(recipients.join(", "), 40);
}

function SubscriptionChannelIcons({ channel }: { channel: SubscriptionChannel }) {
  if (channel === "email") {
    return <IconMail size={14} color={tokens.textMuted} />;
  }
  if (channel === "in_app") {
    return <IconBell size={14} color={tokens.textMuted} />;
  }
  return (
    <Box sx={{ display: "inline-flex", alignItems: "center", gap: 0.25 }}>
      <IconMail size={14} color={tokens.textMuted} />
      <IconBell size={14} color={tokens.textMuted} />
    </Box>
  );
}

function createDefaultFilters(): InsightsFilters {
  return {
    period: currentMonthUtcRange(),
    teamId: "",
    toolId: "",
  };
}

function resolveFirstToolForTeam(
  teamId: string,
  teams: Team[],
  credentials: Credential[],
): string {
  const team = teams.find((row) => row.id === teamId);
  if (!team) {
    return "";
  }
  if (team.toolIds.length > 0) {
    return team.toolIds[0];
  }
  const credential = credentials.find(
    (row) => row.teamId === teamId && row.catalogueToolId,
  );
  return credential?.catalogueToolId ?? "";
}

function resolveDefaultInsightsFilters(
  teams: Team[],
  credentials: Credential[],
): { teamId: string; toolId: string } | null {
  const sorted = [...teams].sort((a, b) => a.name.localeCompare(b.name));
  const firstTeam = sorted[0];
  if (!firstTeam) {
    return null;
  }
  return {
    teamId: firstTeam.id,
    toolId: resolveFirstToolForTeam(firstTeam.id, teams, credentials),
  };
}

function TokenStatTooltip({ stats }: { stats: DashboardStats }) {
  if (!stats.breakdownAvailable) {
    return (
      <Typography variant="caption" sx={{ display: "block", color: "#fff", fontWeight: 700 }}>
        Cursor breakdown not applicable for this tool, or re-sync Cursor to populate
        included vs billable data.
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Total tokens: {formatTokens(stats.totalTokens)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Included in plan: {formatTokens(stats.includedTokens ?? 0)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Billable: {formatTokens(stats.billableTokens ?? 0)}
      </Typography>
      <Divider sx={{ my: 0.5, borderColor: "rgba(255,255,255,0.2)" }} />
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Input: {formatTokens(stats.inputTokens ?? 0)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Output: {formatTokens(stats.outputTokens ?? 0)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Cache write: {formatTokens(stats.cacheWriteTokens ?? 0)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Cache read: {formatTokens(stats.cacheReadTokens ?? 0)}
      </Typography>
    </Box>
  );
}

function CostStatTooltip({ stats }: { stats: DashboardStats }) {
  if (!stats.breakdownAvailable) {
    return (
      <Typography variant="caption" sx={{ display: "block", color: "#fff", fontWeight: 700 }}>
        Cursor breakdown not applicable for this tool.
      </Typography>
    );
  }

  const allowanceUsed =
    stats.packageAllowance && stats.packageAllowance > 0
      ? `${(((stats.includedCost ?? 0) / stats.packageAllowance) * 100).toFixed(1)}%`
      : "—";

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Total cost: {formatCost(stats.totalCost)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Included in plan: {formatCost(stats.includedCost ?? 0)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Additional billable: {formatCost(stats.billableCost ?? 0)}
      </Typography>
      <Divider sx={{ my: 0.5, borderColor: "rgba(255,255,255,0.2)" }} />
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Package allowance: {formatCost(stats.packageAllowance ?? 0)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Allowance used: {allowanceUsed}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Overage (billable): {formatCost(stats.overageCost ?? 0)}
      </Typography>
    </Box>
  );
}

function OrgCostStatTooltip({ costs }: { costs: OrganizationCostSummary }) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Organization total: {formatCost(costs.totalCost)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Total tools cost: {formatCost(costs.toolsCost)}
      </Typography>
      <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
        Additional billable: {formatCost(costs.additionalBillableCost)}
      </Typography>
      <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.85)" }}>
        Tools cost is configured per team and does not change with the date filter.
        Billable cost reflects imports and overage in the selected period.
      </Typography>
    </Box>
  );
}

function OrganizationCostCards({
  costs,
  loading,
}: {
  costs: OrganizationCostSummary | undefined;
  loading: boolean;
}) {
  if (loading) {
    return (
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
          mb: 2,
        }}
      >
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </Box>
    );
  }

  if (!costs) {
    return null;
  }

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: "16px",
        mb: 2,
      }}
    >
      <StatCard
        label="Organization Total Cost"
        value={formatCost(costs.totalCost)}
        icon={IconCurrencyDollar}
        iconColor={tokens.success}
        tooltipContent={<OrgCostStatTooltip costs={costs} />}
      />
      <StatCard
        label="Total Tools Cost"
        value={formatCost(costs.toolsCost)}
        icon={IconTool}
        iconColor="#8B5CF6"
        tooltipContent={
          <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
            Same as Teams: configured package and subscription amounts (static)
          </Typography>
        }
      />
      <StatCard
        label="Billable Cost"
        value={formatCost(costs.additionalBillableCost)}
        icon={IconCurrencyDollar}
        iconColor="#F59E0B"
        tooltipContent={
          <Typography variant="caption" sx={{ color: "#fff", fontWeight: 700 }}>
            Imports and overage in the selected date range (same rules as Teams billable)
          </Typography>
        }
      />
    </Box>
  );
}

function OrganizationCostBreakdownPanel({
  rows,
  loading,
}: {
  rows: OrganizationCostBreakdownItem[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", mb: 2 }}>
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </Box>
    );
  }

  if (rows.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No customer organizations with connected tools.
      </Alert>
    );
  }

  const totals = rows.reduce(
    (acc, row) => ({
      toolsCost: acc.toolsCost + row.toolsCost,
      additionalBillableCost: acc.additionalBillableCost + row.additionalBillableCost,
      totalCost: acc.totalCost + row.totalCost,
    }),
    { toolsCost: 0, additionalBillableCost: 0, totalCost: 0 },
  );

  return (
    <Box sx={{ mb: 2 }}>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
          mb: 2,
        }}
      >
        <StatCard
          label="All Organizations Total Cost"
          value={formatCost(totals.totalCost)}
          icon={IconCurrencyDollar}
          iconColor={tokens.success}
        />
        <StatCard
          label="All Organizations Tools Cost"
          value={formatCost(totals.toolsCost)}
          icon={IconTool}
          iconColor="#8B5CF6"
        />
        <StatCard
          label="All Organizations Billable Cost"
          value={formatCost(totals.additionalBillableCost)}
          icon={IconCurrencyDollar}
          iconColor="#F59E0B"
        />
      </Box>

      <Card variant="outlined" sx={{ borderColor: tokens.border }}>
        <CardContent sx={{ p: 0, "&:last-child": { pb: 0 } }}>
          <Box sx={{ px: 2, py: 1.5, borderBottom: `0.5px solid ${tokens.border}` }}>
            <Typography sx={{ fontSize: "0.875rem", fontWeight: 600 }}>
              Organization cost breakdown
            </Typography>
          </Box>
          <Box component="table" sx={{ width: "100%", borderCollapse: "collapse" }}>
            <Box component="thead">
              <Box component="tr" sx={{ backgroundColor: tokens.bgDefault }}>
                {["Organization", "Total cost", "Tools cost", "Billable cost", "Tools"].map(
                  (header) => (
                    <Box
                      component="th"
                      key={header}
                      sx={{
                        textAlign: "left",
                        px: 2,
                        py: 1,
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        color: tokens.textMuted,
                      }}
                    >
                      {header}
                    </Box>
                  ),
                )}
              </Box>
            </Box>
            <Box component="tbody">
              {rows.map((row) => (
                <Box
                  component="tr"
                  key={row.organizationId}
                  sx={{ borderTop: `0.5px solid ${tokens.border}` }}
                >
                  <Box component="td" sx={{ px: 2, py: 1.25, fontSize: "0.8125rem" }}>
                    {row.organizationName}
                  </Box>
                  <Box component="td" sx={{ px: 2, py: 1.25, fontSize: "0.8125rem" }}>
                    {formatCost(row.totalCost)}
                  </Box>
                  <Box component="td" sx={{ px: 2, py: 1.25, fontSize: "0.8125rem" }}>
                    {formatCost(row.toolsCost)}
                  </Box>
                  <Box component="td" sx={{ px: 2, py: 1.25, fontSize: "0.8125rem" }}>
                    {formatCost(row.additionalBillableCost)}
                  </Box>
                  <Box component="td" sx={{ px: 2, py: 1.25, fontSize: "0.8125rem" }}>
                    {row.connectedToolCount}
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

function SectionError() {
  return (
    <Alert severity="error">Failed to load data. Please refresh.</Alert>
  );
}

function formatReportType(type: ReportType): string {
  return type
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function FormatChip({ format }: { format: ReportFormat }) {
  const colors = FORMAT_CHIP_COLORS[format];
  return (
    <Box
      component="span"
      sx={{
        display: "inline-block",
        px: 1,
        py: 0.25,
        borderRadius: "4px",
        backgroundColor: colors.background,
        color: colors.color,
        fontWeight: 600,
        fontSize: "0.6875rem",
      }}
    >
      {format.toUpperCase()}
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

function InlineStat({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <Box>
      <Typography
        sx={{ fontSize: "0.8125rem", fontWeight: 600, color: "text.primary" }}
      >
        {value}
      </Typography>
      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
        {label}
      </Typography>
    </Box>
  );
}

function resolveDailyChartPoint(
  rows: DailyUsagePoint[],
  state: unknown,
): DailyUsagePoint | undefined {
  const chartState = state as {
    activeLabel?: string | number;
    activeTooltipIndex?: number;
    activeIndex?: number;
    activePayload?: Array<{ payload?: DailyUsagePoint }>;
  };

  const fromPayload = chartState.activePayload?.[0]?.payload;
  if (fromPayload?.isoDate) {
    return fromPayload;
  }

  if (chartState.activeLabel != null) {
    const match = rows.find((row) => row.date === String(chartState.activeLabel));
    if (match?.isoDate) {
      return match;
    }
  }

  const index = chartState.activeTooltipIndex ?? chartState.activeIndex;
  if (typeof index === "number" && rows[index]?.isoDate) {
    return rows[index];
  }

  return undefined;
}

export function InsightsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isSuperAdmin = useAuthStore((s) => s.user?.platformRole === Role.SuperAdmin);
  const currentUser = useAuthStore((s) => s.user);
  const selectedOrganizationId = useOrgScopeStore((s) => s.selectedOrganizationId);
  const tenantScope = tenantScopeKey(currentUser, selectedOrganizationId);
  const showOrgCostBreakdown = isSuperAdmin && !selectedOrganizationId;
  const insightsOrgReady = !isSuperAdmin || Boolean(selectedOrganizationId);

  const [filters, setFilters] = useState<InsightsFilters>(createDefaultFilters);
  const [filtersInitialized, setFiltersInitialized] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [chartMode, setChartMode] = useState<ChartMode>("tokens");
  const [drilldown, setDrilldown] = useState<{
    open: boolean;
    team: TeamUsageRow | null;
  }>({ open: false, team: null });
  const [userDrilldown, setUserDrilldown] = useState<TopUser | null>(null);
  const [reportSlideOpen, setReportSlideOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Report | null>(null);
  const [subscribeTarget, setSubscribeTarget] = useState<Report | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [dateDrilldown, setDateDrilldown] = useState<{
    open: boolean;
    dateIso: string | null;
    dateLabel: string | null;
  }>({ open: false, dateIso: null, dateLabel: null });

  const { from, to, teamId, toolId } = {
    from: filters.period.from,
    to: filters.period.to,
    teamId: filters.teamId,
    toolId: filters.toolId,
  };

  const dashboardFilters: DashboardFilters = { teamId, toolId };
  const insightsFiltersReady =
    insightsOrgReady &&
    filtersInitialized &&
    Boolean(teamId) &&
    Boolean(toolId);

  useEffect(() => {
    setFiltersInitialized(false);
    setFilters(createDefaultFilters());
  }, [selectedOrganizationId]);

  useEffect(() => {
    const register = useInsightsPeriodStore.getState().register;
    const setActive = useInsightsPeriodStore.getState().setActive;
    register((period) => {
      setFilters((prev) => ({ ...prev, period }));
    });
    setActive(true);
    return () => {
      setActive(false);
    };
  }, []);

  useEffect(() => {
    useInsightsPeriodStore.getState().syncPeriod(filters.period);
  }, [filters.period.from, filters.period.to]);

  const statsQuery = useQuery({
    queryKey: ["insights", "stats", from, to, teamId, toolId],
    queryFn: () => fetchDashboardStats(from, to, dashboardFilters),
    enabled: insightsFiltersReady,
  });

  const dailyQuery = useQuery({
    queryKey: ["insights", "daily", from, to, teamId, toolId],
    queryFn: () => fetchDailyUsage(from, to, dashboardFilters),
    enabled: insightsFiltersReady,
  });

  const openDateDrilldown = useCallback((point: DailyUsagePoint) => {
    setDateDrilldown({
      open: true,
      dateIso: point.isoDate,
      dateLabel: point.date,
    });
  }, []);

  const handleDailyChartClick = useCallback(
    (state: unknown) => {
      const point = resolveDailyChartPoint(dailyQuery.data ?? [], state);
      if (point) {
        openDateDrilldown(point);
      }
    },
    [dailyQuery.data, openDateDrilldown],
  );

  const renderClickableActiveDot = useCallback(
    (stroke: string) =>
      function ClickableActiveDot(props: {
        cx?: number;
        cy?: number;
        payload?: DailyUsagePoint;
      }) {
        const { cx = 0, cy = 0, payload } = props;
        if (payload == null) {
          return null;
        }
        return (
          <circle
            cx={cx}
            cy={cy}
            r={6}
            fill={stroke}
            stroke="#fff"
            strokeWidth={2}
            style={{ cursor: "pointer" }}
            onClick={(event) => {
              event.stopPropagation();
              if (payload.isoDate) {
                openDateDrilldown(payload);
              }
            }}
          />
        );
      },
    [openDateDrilldown],
  );

  const teamCostQuery = useQuery({
    queryKey: ["insights", "teamCost", from, to, teamId, toolId],
    queryFn: () => fetchTeamCost(from, to, dashboardFilters),
    enabled: insightsFiltersReady,
  });

  const topUsersQuery = useQuery({
    queryKey: ["insights", "topUsers", from, to, teamId, toolId],
    queryFn: () => fetchTopUsers(from, to, dashboardFilters),
    enabled: insightsFiltersReady,
  });

  const alertsQuery = useQuery({
    queryKey: ["insights", "recentAlerts", teamId, toolId],
    queryFn: () => fetchRecentAlerts(dashboardFilters),
    enabled: Boolean(teamId),
  });

  const teamsUsageQuery = useQuery({
    queryKey: ["insights", "teams", from, to, teamId, toolId],
    queryFn: () => fetchTeamUsage(from, to, dashboardFilters),
    enabled: insightsFiltersReady,
  });

  const reportsQuery = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  const teamsQuery = useQuery({
    queryKey: ["teams", tenantScope],
    queryFn: fetchTeams,
    enabled: insightsOrgReady,
  });

  const orgCostBreakdownQuery = useQuery({
    queryKey: ["insights", "org-cost-breakdown", from, to],
    queryFn: () => fetchOrganizationCostBreakdown({ from, to }),
    enabled: showOrgCostBreakdown && Boolean(from) && Boolean(to),
  });

  const organizationCostsQuery = useQuery({
    queryKey: ["insights", "org-costs", from, to],
    queryFn: () => fetchOrganizationCosts(from, to),
    enabled: !showOrgCostBreakdown && insightsFiltersReady,
  });

  const toolOptionsQuery = useQuery({
    queryKey: ["tools-options"],
    queryFn: fetchToolOptions,
  });

  const catalogToolsQuery = useQuery({
    queryKey: ["tools", "catalog"],
    queryFn: () => fetchTools(),
  });

  const credentialsQuery = useQuery({
    queryKey: ["credentials", tenantScope],
    queryFn: fetchCredentials,
    enabled: insightsOrgReady,
  });

  useEffect(() => {
    if (filtersInitialized || teamsQuery.isPending) {
      return;
    }
    const teams = teamsQuery.data ?? EMPTY_TEAMS;
    const credentials = credentialsQuery.data ?? [];
    const defaults = resolveDefaultInsightsFilters(teams, credentials);
    if (defaults) {
      setFilters((prev) => ({
        ...prev,
        teamId: defaults.teamId,
        toolId: defaults.toolId,
      }));
    }
    setFiltersInitialized(true);
  }, [
    credentialsQuery.data,
    filtersInitialized,
    teamsQuery.data,
    teamsQuery.isPending,
  ]);

  const {
    data: dailyBreakdown,
    isPending: dailyBreakdownLoading,
    isError: dailyBreakdownError,
  } = useQuery({
    queryKey: [
      "insights",
      "daily-breakdown",
      dateDrilldown.dateIso,
      filters.teamId,
      filters.toolId,
    ],
    queryFn: () =>
      fetchDailyBreakdown(
        dateDrilldown.dateIso!,
        filters.teamId,
        filters.toolId,
        dashboardFilters,
      ),
    enabled: dateDrilldown.open && dateDrilldown.dateIso !== null,
  });

  const createReportMutation = useMutation({
    mutationFn: createReport,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      setReportSlideOpen(false);
    },
  });

  const deleteReportMutation = useMutation({
    mutationFn: deleteReport,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      setDeleteTarget(null);
    },
  });

  const downloadMutation = useMutation({
    mutationFn: downloadReport,
    onMutate: (id) => setDownloadingId(id),
    onSettled: () => setDownloadingId(null),
  });

  const subscriptionsQuery = useQuery({
    queryKey: ["subscriptions", subscribeTarget?.id],
    queryFn: () => fetchSubscriptions(subscribeTarget!.id),
    enabled: subscribeTarget !== null,
  });

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ReportFormValues>({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      name: "",
      type: "usage_summary",
      format: "pdf",
      schedule: "once",
      periodFrom: "",
      periodTo: "",
      teamIds: [],
    },
  });

  const {
    register: registerSubscribe,
    control: subscribeControl,
    handleSubmit: handleSubscribeSubmit,
    reset: resetSubscribeForm,
    watch: watchSubscribe,
    formState: { errors: subscribeErrors },
  } = useForm<SubscribeFormValues>({
    resolver: zodResolver(subscribeSchema),
    defaultValues: defaultSubscribeValues(),
  });

  const createSubscriptionMutation = useMutation({
    mutationFn: ({
      reportId,
      body,
    }: {
      reportId: string;
      body: Parameters<typeof createSubscription>[1];
    }) => createSubscription(reportId, body),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: ["subscriptions", variables.reportId],
      });
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      resetSubscribeForm(defaultSubscribeValues());
    },
  });

  const deleteSubscriptionMutation = useMutation({
    mutationFn: ({
      reportId,
      subscriptionId,
    }: {
      reportId: string;
      subscriptionId: string;
    }) => deleteSubscription(reportId, subscriptionId),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: ["subscriptions", variables.reportId],
      });
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });

  useEffect(() => {
    if (!reportSlideOpen) {
      reset({
        name: "",
        type: "usage_summary",
        format: "pdf",
        schedule: "once",
        periodFrom: "",
        periodTo: "",
        teamIds: [],
      });
    }
  }, [reportSlideOpen, reset]);

  const watchedSubscribeChannel = watchSubscribe("channel");

  useEffect(() => {
    if (subscribeTarget) {
      resetSubscribeForm(defaultSubscribeValues());
    }
  }, [resetSubscribeForm, subscribeTarget]);

  const teams = teamsQuery.data ?? EMPTY_TEAMS;
  const toolOptions = toolOptionsQuery.data ?? [];
  const isCopilotTool =
    catalogToolsQuery.data?.find((tool) => tool.id === toolId)?.provider === "copilot" ||
    toolOptions.find((tool) => tool.id === toolId)?.provider === "copilot";
  const isFigmaTool =
    catalogToolsQuery.data?.find((tool) => tool.id === toolId)?.provider === "figma" ||
    toolOptions.find((tool) => tool.id === toolId)?.provider === "figma";
  const isCursorTool =
    catalogToolsQuery.data?.find((tool) => tool.id === toolId)?.provider === "cursor" ||
    toolOptions.find((tool) => tool.id === toolId)?.provider === "cursor";
  const credentials = credentialsQuery.data ?? [];

  const cursorBillTrendAvailable = useMemo(() => {
    if (!isCursorTool) {
      return false;
    }
    if (statsQuery.data?.breakdownAvailable) {
      return true;
    }
    return (dailyQuery.data ?? []).some(
      (point) =>
        point.breakdownAvailable ||
        (point.includedCost ?? 0) > 0 ||
        (point.billableCost ?? 0) > 0,
    );
  }, [dailyQuery.data, isCursorTool, statsQuery.data?.breakdownAvailable]);

  useEffect(() => {
    if (isCursorTool) {
      setChartMode("bill");
      return;
    }
    setChartMode("tokens");
  }, [isCursorTool, toolId]);

  const drilldownAssignedToolIds = useMemo(() => {
    if (!drilldown.team) {
      return [];
    }
    const selectedTeam = teams.find((team) => team.id === drilldown.team?.teamId);
    const ids = new Set(selectedTeam?.toolIds ?? []);
    for (const credential of credentials) {
      if (credential.teamId === drilldown.team.teamId && credential.catalogueToolId) {
        ids.add(credential.catalogueToolId);
      }
    }
    return [...ids];
  }, [credentials, drilldown.team, teams]);

  const drilldownTeamMeta = useMemo(
    () => teams.find((team) => team.id === drilldown.team?.teamId) ?? null,
    [drilldown.team?.teamId, teams],
  );

  const filteredToolOptions = useMemo(() => {
    const selectedTeam = teams.find((team) => team.id === teamId);
    if (!selectedTeam) {
      return [];
    }
    const assignedToolIds = new Set(selectedTeam.toolIds ?? []);
    for (const credential of credentials) {
      if (credential.teamId === teamId && credential.catalogueToolId) {
        assignedToolIds.add(credential.catalogueToolId);
      }
    }
    return toolOptions.filter((tool) => assignedToolIds.has(tool.id));
  }, [credentials, teamId, teams, toolOptions]);

  useEffect(() => {
    if (!teamId) {
      return;
    }
    setFilters((prev) => {
      if (!prev.toolId) {
        const firstTool = resolveFirstToolForTeam(teamId, teams, credentials);
        return firstTool ? { ...prev, toolId: firstTool } : prev;
      }
      const stillValid = filteredToolOptions.some((tool) => tool.id === prev.toolId);
      if (stillValid) {
        return prev;
      }
      return {
        ...prev,
        toolId: resolveFirstToolForTeam(teamId, teams, credentials),
      };
    });
  }, [credentials, filteredToolOptions, teamId, teams]);

  useEffect(() => {
    if (!isFigmaTool || !teamId || !toolId) {
      return;
    }
    let cancelled = false;
    void fetchTeamToolAssignment(teamId, toolId).then((assignment) => {
      if (cancelled) {
        return;
      }
      const subscriptionStart = assignment?.package.subscriptionStart;
      if (!subscriptionStart) {
        return;
      }
      setFilters((prev) => {
        if (prev.teamId !== teamId || prev.toolId !== toolId) {
          return prev;
        }
        return {
          ...prev,
          period: currentSubscriptionPeriodRange(subscriptionStart),
        };
      });
    });
    return () => {
      cancelled = true;
    };
  }, [isFigmaTool, teamId, toolId]);

  const sortedTeamRows = useMemo(() => {
    const rows = teamsUsageQuery.data ?? [];
    return [...rows].sort((a, b) => b.cost - a.cost);
  }, [teamsUsageQuery.data]);

  const noTeamsAvailable = filtersInitialized && teams.length === 0;
  const noToolsAssigned =
    filtersInitialized && Boolean(teamId) && filteredToolOptions.length === 0;

  const topUserColumns: Column<TopUser>[] = useMemo(
    () => [
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
    ],
    [],
  );

  const teamColumns: Column<TeamUsageRow>[] = useMemo(
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
    ],
    [],
  );

  const drilldownColumns: Column<UserUsageRow>[] = useMemo(
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

  const reportColumns: Column<Report>[] = useMemo(
    () => [
      {
        key: "name",
        header: "Report",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.name}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {formatReportType(row.type)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "format",
        header: "Format",
        render: (row) => <FormatChip format={row.format} />,
      },
      {
        key: "schedule",
        header: "Schedule",
        render: (row) => SCHEDULE_LABELS[row.schedule],
      },
      {
        key: "status",
        header: "Status",
        render: (row) => <StatusBadge status={row.status} />,
      },
      {
        key: "generatedAt",
        header: "Generated",
        sortable: true,
        render: (row) =>
          row.generatedAt ? (
            formatRelativeTime(row.generatedAt)
          ) : (
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              Pending
            </Typography>
          ),
      },
      {
        key: "fileSizeKb",
        header: "Size",
        align: "right",
        render: (row) => (
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {row.fileSizeKb != null ? `${row.fileSizeKb} KB` : "—"}
          </Typography>
        ),
      },
      {
        key: "actions",
        header: "",
        align: "right",
        render: (row) => {
          const canDownload = row.status === "completed";
          return (
            <Box sx={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
              <IconButton
                size="small"
                aria-label={`Download ${row.name}`}
                disabled={!canDownload || downloadingId === row.id}
                onClick={(event) => {
                  event.stopPropagation();
                  downloadMutation.mutate(row.id);
                }}
                sx={{ color: canDownload ? "inherit" : tokens.textMuted }}
              >
                {downloadingId === row.id ? (
                  <CircularProgress size={12} />
                ) : (
                  <IconDownload size={15} />
                )}
              </IconButton>
              <MuiTooltip title="Manage subscriptions">
                <IconButton
                  size="small"
                  aria-label={`Manage subscriptions for ${row.name}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    setSubscribeTarget(row);
                  }}
                >
                  {row.subscriptionCount > 0 ? (
                    <Badge badgeContent={row.subscriptionCount} color="primary">
                      <IconBell size={15} />
                    </Badge>
                  ) : (
                    <IconBell size={15} />
                  )}
                </IconButton>
              </MuiTooltip>
              <IconButton
                size="small"
                aria-label={`Delete ${row.name}`}
                onClick={(event) => {
                  event.stopPropagation();
                  setDeleteTarget(row);
                }}
                sx={{ color: tokens.critical }}
              >
                <IconTrash size={15} />
              </IconButton>
            </Box>
          );
        },
      },
    ],
    [downloadMutation, downloadingId],
  );

  const onSubscribeSubmit = (data: SubscribeFormValues) => {
    if (!subscribeTarget) {
      return;
    }

    const emailRecipients =
      data.channel === "in_app"
        ? []
        : data.emailRecipients
            .split(",")
            .map((email) => email.trim())
            .filter(Boolean);

    createSubscriptionMutation.mutate({
      reportId: subscribeTarget.id,
      body: {
        channel: data.channel,
        cadence: data.cadence,
        emailRecipients,
      },
    });
  };

  const onReportSubmit = (data: ReportFormValues) => {
    createReportMutation.mutate({
      name: data.name,
      type: data.type,
      format: data.format,
      schedule: data.schedule,
      periodFrom: new Date(`${data.periodFrom}T00:00:00`).toISOString(),
      periodTo: new Date(`${data.periodTo}T23:59:59`).toISOString(),
      teamIds: data.teamIds,
    });
  };

  const handleTabChange = (_event: SyntheticEvent, value: number) => {
    setActiveTab(value);
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {isSuperAdmin && !selectedOrganizationId && (
        <Alert severity="info">
          Select a customer organization in the header to view team-level insights and
          date-filtered dashboards. The table below shows all-tenant cost summary.
        </Alert>
      )}

      {showOrgCostBreakdown ? (
        <OrganizationCostBreakdownPanel
          rows={orgCostBreakdownQuery.data ?? []}
          loading={orgCostBreakdownQuery.isLoading}
        />
      ) : (
        <OrganizationCostCards
          costs={organizationCostsQuery.data}
          loading={organizationCostsQuery.isLoading}
        />
      )}

      {orgCostBreakdownQuery.isError && showOrgCostBreakdown && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load organization cost breakdown.
        </Alert>
      )}

      <Box sx={{ display: "flex", gap: 2, mb: 0, alignItems: "center", flexWrap: "wrap" }}>
        <FormControl size="small" sx={{ width: 180 }}>
          <InputLabel id="insights-team-label">Team</InputLabel>
          <Select
            labelId="insights-team-label"
            label="Team"
            value={filters.teamId}
            onChange={(event) => {
              const nextTeamId = event.target.value;
              setFilters((prev) => ({
                ...prev,
                teamId: nextTeamId,
                toolId: resolveFirstToolForTeam(nextTeamId, teams, credentials),
              }));
            }}
            disabled={teams.length === 0}
          >
            {teams.map((team) => (
              <MenuItem key={team.id} value={team.id}>
                {team.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ width: 180 }}>
          <InputLabel id="insights-tool-label">AI Tool</InputLabel>
          <Select
            labelId="insights-tool-label"
            label="AI Tool"
            value={filters.toolId}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, toolId: event.target.value }))
            }
            disabled={filteredToolOptions.length === 0}
          >
            {filteredToolOptions.map((tool) => (
              <MenuItem key={tool.id} value={tool.id}>
                {tool.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        {noTeamsAvailable && (
          <Alert severity="info" sx={{ flex: 1 }}>
            No teams available. Create a team to view insights.
          </Alert>
        )}
        {noToolsAssigned && (
          <Alert severity="info" sx={{ flex: 1 }}>
            No tools assigned to this team. Assign tools or connect a credential to see
            usage.
          </Alert>
        )}
      </Box>

      {isCopilotTool && insightsFiltersReady ? (
        <CopilotBillingInsightsPanel
          teamId={teamId}
          toolId={toolId}
          from={from}
          to={to}
        />
      ) : isFigmaTool && insightsFiltersReady ? (
        <FigmaBillingInsightsPanel
          teamId={teamId}
          toolId={toolId}
          from={from}
          to={to}
        />
      ) : (
        <>
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
              tooltipContent={<TokenStatTooltip stats={statsQuery.data} />}
            />
            <StatCard
              label="Total Cost"
              value={formatCost(statsQuery.data.totalCost)}
              delta={statsQuery.data.costDelta}
              deltaLabel="vs prev period"
              icon={IconCurrencyDollar}
              iconColor={tokens.success}
              tooltipContent={<CostStatTooltip stats={statsQuery.data} />}
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
                {chartMode === "bill"
                  ? "Bill cost trend"
                  : chartMode === "cost"
                    ? "Cost trend"
                    : "Token usage"}
              </Typography>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {chartMode === "bill"
                  ? "Daily included plan consumption vs additional billable spend"
                  : chartMode === "cost"
                    ? "Daily total cost over selected period"
                    : "Daily usage over selected period"}
              </Typography>
              {chartMode !== "bill" ? (
                <Typography
                  sx={{ fontSize: "0.75rem", color: "text.secondary", mb: 1, mt: 0.5 }}
                >
                  Click any point to see team breakdown
                </Typography>
              ) : null}
            </Box>
            <ToggleButtonGroup
              size="small"
              exclusive
              value={chartMode}
              onChange={(_, value: ChartMode | null) => {
                if (value) setChartMode(value);
              }}
            >
              <ToggleButton value="tokens">Tokens</ToggleButton>
              <ToggleButton value="cost">Cost</ToggleButton>
              {isCursorTool ? <ToggleButton value="bill">Bill</ToggleButton> : null}
            </ToggleButtonGroup>
          </Box>
          {isCursorTool && chartMode === "bill" && !cursorBillTrendAvailable ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              Bill cost breakdown is not available yet. Re-sync Cursor usage to populate
              included vs billable spend.
            </Alert>
          ) : null}
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
          ) : (dailyQuery.data ?? []).length === 0 ? (
            <Alert severity="info">No usage data for this period.</Alert>
          ) : (
            <ResponsiveContainer width="100%" height={chartMode === "bill" ? 240 : 200}>
              <LineChart
                data={dailyQuery.data ?? []}
                onClick={chartMode === "bill" ? undefined : handleDailyChartClick}
                style={{ cursor: chartMode === "bill" ? "default" : "pointer" }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={tokens.border} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: tokens.textMuted }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tickFormatter={(value: number) =>
                    chartMode === "tokens"
                      ? formatTokens(value)
                      : formatCost(value)
                  }
                  tick={{ fontSize: 11, fill: tokens.textMuted }}
                  width={chartMode === "bill" ? 72 : 65}
                />
                {chartMode === "bill" ? (
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (!active || !payload?.length) {
                        return null;
                      }
                      const point = payload[0]?.payload as DailyUsagePoint | undefined;
                      if (!point) {
                        return null;
                      }
                      return (
                        <Box
                          sx={{
                            backgroundColor: "#fff",
                            border: `1px solid ${tokens.border}`,
                            borderRadius: 1,
                            px: 1.5,
                            py: 1,
                          }}
                        >
                          <Typography variant="caption" sx={{ fontWeight: 600, display: "block" }}>
                            {label}
                          </Typography>
                          <Typography variant="caption" sx={{ display: "block" }}>
                            Included in plan: {formatCost(point.includedCost ?? 0)}
                          </Typography>
                          <Typography variant="caption" sx={{ display: "block" }}>
                            Billable: {formatCost(point.billableCost ?? 0)}
                          </Typography>
                        </Box>
                      );
                    }}
                  />
                ) : (
                  <Tooltip
                    formatter={(value) =>
                      chartMode === "tokens"
                        ? [formatTokens(value as number), "Tokens"]
                        : [formatCost(value as number), "Cost"]
                    }
                    contentStyle={insightsChartTooltipStyle}
                    labelStyle={insightsChartTooltipLabelStyle}
                    itemStyle={insightsChartTooltipItemStyle}
                  />
                )}
                {dateDrilldown.dateLabel && chartMode !== "bill" && (
                  <ReferenceLine
                    x={dateDrilldown.dateLabel}
                    stroke={tokens.primary}
                    strokeDasharray="4 4"
                    strokeWidth={1.5}
                  />
                )}
                {chartMode === "tokens" ? (
                  <Line
                    type="monotone"
                    dataKey="tokens"
                    stroke={tokens.primary}
                    strokeWidth={2}
                    dot={false}
                    activeDot={renderClickableActiveDot(tokens.primary)}
                  />
                ) : chartMode === "cost" ? (
                  <Line
                    type="monotone"
                    dataKey="cost"
                    stroke={tokens.success}
                    strokeWidth={2}
                    dot={false}
                    activeDot={renderClickableActiveDot(tokens.success)}
                  />
                ) : (
                  <>
                    <Legend verticalAlign="top" height={28} />
                    <Line
                      type="monotone"
                      dataKey="includedCost"
                      name="Included in plan"
                      stroke={tokens.primary}
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="billableCost"
                      name="Billable"
                      stroke={tokens.success}
                      strokeWidth={2}
                      dot={false}
                    />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Tabs value={activeTab} onChange={handleTabChange}>
        <Tab label="Overview" />
        <Tab label="By Team" />
        <Tab label="Reports" />
      </Tabs>

      {activeTab === 0 && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
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
              <Card sx={{ height: "100%" }}>
                <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.25 }}>
                    Cost by Team
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{ color: tokens.textMuted, mb: 2, display: "block" }}
                  >
                    USD spend this period
                  </Typography>
                  {teamCostQuery.isLoading ? (
                    <Skeleton height={220} variant="rounded" />
                  ) : (
                    <TeamCostChart data={teamCostQuery.data ?? []} />
                  )}
                </CardContent>
              </Card>
            )}

            {topUsersQuery.isError ? (
              <SectionError />
            ) : (
              <Card sx={{ height: "100%" }}>
                <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
                    Top Users
                  </Typography>
                  <DataTable
                    columns={topUserColumns}
                    rows={topUsersQuery.data ?? []}
                    rowKey={(row) => row.id}
                    loading={topUsersQuery.isLoading}
                    emptyTitle="No usage data"
                    onRowClick={(row) => setUserDrilldown(row)}
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
      )}

      {activeTab === 1 && (
        <>
          {teamsUsageQuery.isError ? (
            <SectionError />
          ) : (
            <Card>
              <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
                  Usage by Team
                </Typography>
                <DataTable
                  columns={teamColumns}
                  rows={sortedTeamRows}
                  rowKey={(row) => row.teamId}
                  loading={teamsUsageQuery.isPending}
                  emptyTitle="No usage data"
                  emptyDescription="No token usage recorded for this period."
                  onRowClick={(row) =>
                    setDrilldown({ open: true, team: row })
                  }
                />
              </CardContent>
            </Card>
          )}
        </>
      )}

      {activeTab === 2 && (
        <Box>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 2,
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              Reports
            </Typography>
            <Button
              variant="contained"
              size="small"
              startIcon={<IconPlus size={15} />}
              onClick={() => setReportSlideOpen(true)}
            >
              New Report
            </Button>
          </Box>

          {reportsQuery.isError && <SectionError />}

          <DataTable
            columns={reportColumns}
            rows={reportsQuery.data ?? []}
            rowKey={(row) => row.id}
            loading={reportsQuery.isPending}
            emptyTitle="No reports yet"
            emptyDescription="Generate your first report to export usage data."
          />
        </Box>
      )}
        </>
      )}

      <SlideOver
        open={dateDrilldown.open}
        onClose={() => setDateDrilldown({ open: false, dateIso: null, dateLabel: null })}
        title={dateDrilldown.dateLabel ?? ""}
        subtitle="Token and cost breakdown by team and user"
        width={520}
      >
        <DailyBreakdownContent
          teams={dailyBreakdown ?? []}
          loading={dailyBreakdownLoading}
          error={dailyBreakdownError}
        />
      </SlideOver>

      <TeamDetailSlideOver
        open={drilldown.open}
        onClose={() => setDrilldown({ open: false, team: null })}
        teamRow={drilldown.team}
        teamMeta={drilldownTeamMeta}
        from={from}
        to={to}
        filterToolId={toolId}
        toolOptions={toolOptions}
        assignedToolIds={drilldownAssignedToolIds}
        credentials={credentials}
        userColumns={drilldownColumns}
      />

      <SlideOver
        open={userDrilldown !== null}
        onClose={() => setUserDrilldown(null)}
        width={480}
        title={userDrilldown?.name ?? ""}
        subtitle={userDrilldown?.team ?? ""}
      >
        {userDrilldown && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <InlineStat label="Tokens" value={formatTokens(userDrilldown.tokens)} />
            <InlineStat label="Cost" value={formatCost(userDrilldown.cost)} />
            <InlineStat
              label="% of total"
              value={formatPercent(userDrilldown.percentOfTotal)}
            />
          </Box>
        )}
      </SlideOver>

      <SlideOver
        open={reportSlideOpen}
        onClose={() => setReportSlideOpen(false)}
        width={520}
        title="New Report"
        subtitle="Configure and generate a usage export"
        footer={
          <>
            <Button
              variant="text"
              onClick={() => setReportSlideOpen(false)}
              disabled={createReportMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleSubmit(onReportSubmit)}
              disabled={createReportMutation.isPending}
              startIcon={
                createReportMutation.isPending ? (
                  <CircularProgress size={14} color="inherit" />
                ) : undefined
              }
            >
              Generate Report
            </Button>
          </>
        }
      >
        <Box component="form" onSubmit={handleSubmit(onReportSubmit)}>
          <TextField
            {...register("name")}
            fullWidth
            size="small"
            label="Report name"
            error={Boolean(errors.name)}
            helperText={errors.name?.message}
            sx={{ mb: 2 }}
          />

          <Controller
            name="type"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel id="insights-report-type-label">Report type</InputLabel>
                <Select
                  {...field}
                  labelId="insights-report-type-label"
                  label="Report type"
                >
                  {REPORT_TYPE_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 2,
              mb: 2,
            }}
          >
            <Controller
              name="format"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="insights-report-format-label">Format</InputLabel>
                  <Select
                    {...field}
                    labelId="insights-report-format-label"
                    label="Format"
                  >
                    {FORMAT_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
            <Controller
              name="schedule"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="insights-report-schedule-label">Schedule</InputLabel>
                  <Select
                    {...field}
                    labelId="insights-report-schedule-label"
                    label="Schedule"
                  >
                    {SCHEDULE_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
          </Box>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 2,
              mb: 2,
            }}
          >
            <TextField
              {...register("periodFrom")}
              fullWidth
              size="small"
              type="date"
              label="From"
              slotProps={{ inputLabel: { shrink: true } }}
              error={Boolean(errors.periodFrom)}
              helperText={errors.periodFrom?.message}
            />
            <TextField
              {...register("periodTo")}
              fullWidth
              size="small"
              type="date"
              label="To"
              slotProps={{ inputLabel: { shrink: true } }}
              error={Boolean(errors.periodTo)}
              helperText={errors.periodTo?.message}
            />
          </Box>

          <Controller
            name="teamIds"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth size="small">
                <InputLabel id="insights-report-teams-label">Teams</InputLabel>
                <Select
                  {...field}
                  multiple
                  labelId="insights-report-teams-label"
                  label="Teams"
                  renderValue={(selected) =>
                    teams
                      .filter((team) => selected.includes(team.id))
                      .map((team) => team.name)
                      .join(", ") || "All teams"
                  }
                >
                  {teams.map((team) => (
                    <MenuItem key={team.id} value={team.id}>
                      <Checkbox checked={field.value.includes(team.id)} />
                      <ListItemText primary={team.name} />
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>Leave empty to include all teams</FormHelperText>
              </FormControl>
            )}
          />
        </Box>
      </SlideOver>

      <SlideOver
        open={subscribeTarget !== null}
        onClose={() => setSubscribeTarget(null)}
        title="Report Subscriptions"
        subtitle={subscribeTarget?.name ?? ""}
        width={480}
        footer={
          <Button
            variant="text"
            fullWidth
            onClick={() => setSubscribeTarget(null)}
          >
            Close
          </Button>
        }
      >
        <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
          Active subscriptions
        </Typography>

        {subscriptionsQuery.isPending && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1, mb: 2 }}>
            <Skeleton variant="rounded" height={56} />
            <Skeleton variant="rounded" height={56} />
          </Box>
        )}

        {!subscriptionsQuery.isPending &&
          (subscriptionsQuery.data?.length ?? 0) === 0 && (
            <EmptyState
              size="sm"
              title="No subscriptions yet"
              description="Add one below"
            />
          )}

        {!subscriptionsQuery.isPending &&
          (subscriptionsQuery.data?.length ?? 0) > 0 && (
            <Box sx={{ mb: 2 }}>
              {subscriptionsQuery.data?.map((subscription, index) => (
                <Box key={subscription.id}>
                  <SubscriptionRow
                    subscription={subscription}
                    deleting={
                      deleteSubscriptionMutation.isPending &&
                      deleteSubscriptionMutation.variables?.subscriptionId ===
                        subscription.id
                    }
                    onDelete={() => {
                      if (subscribeTarget) {
                        deleteSubscriptionMutation.mutate({
                          reportId: subscribeTarget.id,
                          subscriptionId: subscription.id,
                        });
                      }
                    }}
                  />
                  {index < (subscriptionsQuery.data?.length ?? 0) - 1 && (
                    <Divider sx={{ my: 1.5 }} />
                  )}
                </Box>
              ))}
            </Box>
          )}

        <Typography variant="body2" sx={{ fontWeight: 600, mt: 2, mb: 1 }}>
          Add subscription
        </Typography>

        <Box
          component="form"
          onSubmit={handleSubscribeSubmit(onSubscribeSubmit)}
        >
          <Controller
            name="channel"
            control={subscribeControl}
            render={({ field }) => (
              <ToggleButtonGroup
                exclusive
                fullWidth
                size="small"
                value={field.value}
                onChange={(_, value: SubscriptionChannel | null) => {
                  if (value) {
                    field.onChange(value);
                  }
                }}
                sx={{ mb: 2 }}
              >
                {(
                  [
                    { value: "email", label: "Email" },
                    { value: "in_app", label: "In-app" },
                    { value: "both", label: "Both" },
                  ] as const
                ).map((option) => (
                  <ToggleButton
                    key={option.value}
                    value={option.value}
                    sx={{
                      "&.Mui-selected": {
                        backgroundColor: tokens.primary,
                        color: "#fff",
                        "&:hover": { backgroundColor: tokens.primary },
                      },
                    }}
                  >
                    {option.label}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
            )}
          />

          <Controller
            name="cadence"
            control={subscribeControl}
            render={({ field }) => (
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel id="subscribe-cadence-label">
                  Delivery cadence
                </InputLabel>
                <Select
                  {...field}
                  labelId="subscribe-cadence-label"
                  label="Delivery cadence"
                >
                  {SUBSCRIPTION_CADENCE_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />

          <Collapse in={watchedSubscribeChannel !== "in_app"}>
            <TextField
              {...registerSubscribe("emailRecipients")}
              fullWidth
              size="small"
              label="Email recipients"
              placeholder="alice@co.com, bob@co.com"
              helperText={
                subscribeErrors.emailRecipients?.message ?? "Comma-separated"
              }
              error={Boolean(subscribeErrors.emailRecipients)}
              sx={{ mb: 2 }}
            />
          </Collapse>

          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="medium"
            disabled={createSubscriptionMutation.isPending}
            startIcon={
              createSubscriptionMutation.isPending ? (
                <CircularProgress size={14} color="inherit" />
              ) : undefined
            }
          >
            Add subscription
          </Button>
        </Box>
      </SlideOver>

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete report?"
        description={`"${deleteTarget?.name ?? ""}" will be permanently removed.`}
        dangerous
        confirmLabel="Delete"
        loading={deleteReportMutation.isPending}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => {
          if (deleteTarget) {
            deleteReportMutation.mutate(deleteTarget.id);
          }
        }}
      />
    </Box>
  );
}

function SubscriptionRow({
  subscription,
  deleting,
  onDelete,
}: {
  subscription: ReportSubscription;
  deleting: boolean;
  onDelete: () => void;
}) {
  const recipients = formatSubscriptionRecipients(subscription.emailRecipients);

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 1,
      }}
    >
      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, mb: 0.25 }}>
          <SubscriptionChannelIcons channel={subscription.channel} />
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {SUBSCRIPTION_CADENCE_LABELS[subscription.cadence]} ·{" "}
            {SUBSCRIPTION_CHANNEL_LABELS[subscription.channel]}
          </Typography>
        </Box>
        {recipients && (
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {recipients}
          </Typography>
        )}
      </Box>
      <IconButton
        size="small"
        aria-label="Delete subscription"
        disabled={deleting}
        onClick={onDelete}
        sx={{ color: tokens.critical, flexShrink: 0 }}
      >
        {deleting ? (
          <CircularProgress size={12} />
        ) : (
          <IconTrash size={14} />
        )}
      </IconButton>
    </Box>
  );
}

function DailyBreakdownContent({
  teams,
  loading,
  error,
}: {
  teams: DailyBreakdownTeam[];
  loading: boolean;
  error: boolean;
}) {
  const totals = useMemo(
    () =>
      teams.reduce(
        (acc, team) => ({
          tokens: acc.tokens + team.tokens,
          cost: acc.cost + team.cost,
        }),
        { tokens: 0, cost: 0 },
      ),
    [teams],
  );

  if (loading) {
    return (
      <Box>
        <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
          <Skeleton variant="rounded" width="50%" height={52} />
          <Skeleton variant="rounded" width="50%" height={52} />
        </Box>
        {Array.from({ length: 3 }).map((_, index) => (
          <Box key={index} sx={{ mb: 2 }}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                py: 1,
                borderBottom: `0.5px solid ${tokens.border}`,
              }}
            >
              <Skeleton width="40%" height={20} />
              <Skeleton width="20%" height={20} />
            </Box>
            <Box sx={{ pl: 2 }}>
              <Skeleton width="30%" height={16} sx={{ my: "4px" }} />
              <Skeleton width="15%" height={16} sx={{ my: "4px" }} />
            </Box>
          </Box>
        ))}
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Failed to load breakdown.</Alert>;
  }

  if (teams.length === 0) {
    return <EmptyState size="sm" title="No data for this date" />;
  }

  return (
    <Box>
      <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
        <Box
          sx={{
            flex: 1,
            backgroundColor: tokens.bgDefault,
            borderRadius: 8,
            p: "10px 14px",
          }}
        >
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            Total tokens
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {formatTokens(totals.tokens)}
          </Typography>
        </Box>
        <Box
          sx={{
            flex: 1,
            backgroundColor: tokens.bgDefault,
            borderRadius: 8,
            p: "10px 14px",
          }}
        >
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            Total cost
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {formatCost(totals.cost)}
          </Typography>
        </Box>
      </Box>

      {teams.map((team, teamIndex) => (
        <Box key={team.teamId}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              py: 1,
              borderBottom:
                teamIndex < teams.length - 1
                  ? `0.5px solid ${tokens.border}`
                  : undefined,
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {team.teamName}
            </Typography>
            <Box sx={{ display: "flex", gap: 2 }}>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {formatTokens(team.tokens)}
              </Typography>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {formatCost(team.cost)}
              </Typography>
            </Box>
          </Box>

          <Box sx={{ pl: 2, pb: teamIndex < teams.length - 1 ? 1 : 0 }}>
            {team.users.map((user) => (
              <Box
                key={user.userId}
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  py: "4px",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Box
                    sx={{
                      width: 20,
                      height: 20,
                      borderRadius: "50%",
                      backgroundColor: "#1E3A5F",
                      color: "#60A5FA",
                      fontSize: 9,
                      fontWeight: 500,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    {getInitials(user.userName)}
                  </Box>
                  <Typography variant="body2">{user.userName}</Typography>
                </Box>
                <Box sx={{ display: "flex", gap: 2 }}>
                  <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                    {formatTokens(user.tokens)}
                  </Typography>
                  <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                    {formatCost(user.cost)}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      ))}
    </Box>
  );
}

function TeamCostChart({ data }: { data: TeamCostDataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid vertical={false} stroke={tokens.border} />
        <XAxis dataKey="team" tick={{ fontSize: 11, fill: tokens.textMuted }} />
        <YAxis
          tickFormatter={(value: number) => `$${value}`}
          tick={{ fontSize: 11, fill: tokens.textMuted }}
          width={45}
        />
        <Tooltip
          formatter={(value) => [formatCost(value as number), "Cost"]}
          contentStyle={insightsChartTooltipStyle}
          labelStyle={insightsChartTooltipLabelStyle}
          itemStyle={insightsChartTooltipItemStyle}
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
            <Box
              sx={{
                display: "flex",
                alignItems: "flex-start",
                gap: 1.5,
                minWidth: 0,
              }}
            >
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

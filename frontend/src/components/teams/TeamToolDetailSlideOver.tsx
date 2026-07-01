import { Alert, Box, CircularProgress, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { endOfDay, startOfMonth } from "date-fns";
import { useMemo } from "react";

import { fetchCopilotBillingInsights } from "@/api/copilot";
import { fetchFigmaBillingInsights } from "@/api/figma";
import { fetchDashboardStats } from "@/api/dashboard";
import { fetchTeamTools } from "@/api/teamTools";
import { fetchTools } from "@/api/tools";
import type { Team } from "@/api/teams";
import type { TeamToolAssignment } from "@/api/teamTools";
import type { CopilotBillingInsights } from "@/api/copilot";
import type { FigmaBillingInsights } from "@/api/figma";
import { isCopilotProvider, isFigmaProvider, type ToolProvider } from "@/api/adapters/tools";
import { SlideOver } from "@/components/layout/SlideOver";
import { TeamToolPricingSummary } from "@/components/teams/TeamToolPricingSummary";
import { UsageBreakdownStats } from "@/components/usage/UsageBreakdownStats";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { tokens } from "@/theme/palette";
import { formatCost, formatTokens } from "@/utils/formatters";

interface TeamToolDetailSlideOverProps {
  open: boolean;
  onClose: () => void;
  team: Team | null;
  toolId: string | null;
  toolName: string;
  toolProvider?: ToolProvider | null;
}

const ALL_TIME_PERIOD = {
  from: new Date(2000, 0, 1).toISOString(),
  to: new Date(2099, 11, 31, 23, 59, 59, 999).toISOString(),
};

function currentMonthPeriod() {
  const today = new Date();
  return {
    from: startOfMonth(today).toISOString(),
    to: endOfDay(today).toISOString(),
  };
}

function UsageStat({
  label,
  value,
  subvalue,
}: {
  label: string;
  value: string;
  subvalue?: string;
}) {
  return (
    <Box
      sx={{
        flex: 1,
        minWidth: 120,
        p: 1.5,
        borderRadius: "6px",
        border: `0.5px solid ${tokens.border}`,
        backgroundColor: tokens.bgDefault,
      }}
    >
      <Typography variant="caption" sx={{ color: tokens.textMuted, display: "block" }}>
        {label}
      </Typography>
      <Typography variant="body1" sx={{ fontWeight: 600, mt: 0.25 }}>
        {value}
      </Typography>
      {subvalue && (
        <Typography variant="caption" sx={{ color: tokens.textMuted }}>
          {subvalue}
        </Typography>
      )}
    </Box>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        gap: 2,
        py: 0.75,
        borderBottom: `0.5px solid ${tokens.border}`,
      }}
    >
      <Typography variant="body2" sx={{ color: tokens.textMuted }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 500, textAlign: "right" }}>
        {value}
      </Typography>
    </Box>
  );
}

function copilotConfiguredSubscriptionFromAssignment(
  assignment: TeamToolAssignment | null,
): number {
  if (!assignment) {
    return 0;
  }
  const { model, costPerSeat, flatMonthlyCost, seatCount } = assignment.pricing;
  if (seatCount == null) {
    return 0;
  }
  if (model === "per_team") {
    return flatMonthlyCost != null ? flatMonthlyCost * seatCount : 0;
  }
  return costPerSeat != null ? costPerSeat * seatCount : 0;
}

function CopilotTeamToolSummary({
  insights,
  assignment,
}: {
  insights: CopilotBillingInsights;
  assignment: TeamToolAssignment | null;
}) {
  const configuredSubscription = copilotConfiguredSubscriptionFromAssignment(assignment);
  const subscriptionLimit =
    configuredSubscription > 0
      ? configuredSubscription
      : Number(insights.monthly_cost_limit ?? insights.configured_monthly_cost ?? 0);
  const additionalCost = Number(insights.additional_cost ?? 0);
  const totalCost = subscriptionLimit + additionalCost;
  const quantities = insights.quantities;
  const pkg = assignment?.package;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2.5 }}>
      <Box>
        <Typography
          variant="caption"
          sx={{
            color: tokens.textMuted,
            textTransform: "uppercase",
            display: "block",
            mb: 1,
          }}
        >
          Imported billing (all periods)
        </Typography>
        {!insights.has_import && !insights.has_config && subscriptionLimit <= 0 ? (
          <Alert severity="info">
            Configure Copilot on this team, then import billing CSV in Uploads to see costs
            here.
          </Alert>
        ) : (
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5 }}>
            <UsageStat
              label="Total cost"
              value={subscriptionLimit > 0 || additionalCost > 0 ? formatCost(totalCost) : "—"}
            />
            <UsageStat
              label="Subscription (configured)"
              value={subscriptionLimit > 0 ? formatCost(subscriptionLimit) : "—"}
            />
            <UsageStat
              label="Additional spend"
              value={insights.has_import ? formatCost(additionalCost) : "—"}
            />
            <UsageStat
              label="Total quantity"
              value={
                quantities.total_quantity > 0 ? String(quantities.total_quantity) : "—"
              }
              subvalue={
                quantities.user_months_quantity > 0
                  ? `${quantities.user_months_quantity} seat-months`
                  : undefined
              }
            />
          </Box>
        )}
        {insights.budget_alert_triggered && (
          <Alert severity="warning" sx={{ mt: 1.5 }}>
            Imported spend reached the configured USD alert threshold
            {insights.alert_threshold_usd != null
              ? ` (${formatCost(Number(insights.alert_threshold_usd))})`
              : ""}
            .
          </Alert>
        )}
      </Box>

      {(pkg?.monthlyBudget != null ||
        pkg?.alertThresholdUsd != null ||
        assignment?.pricing.planName) && (
        <Box>
          <Typography
            variant="caption"
            sx={{
              color: tokens.textMuted,
              textTransform: "uppercase",
              display: "block",
              mb: 1,
            }}
          >
            Team configuration
          </Typography>
          <Box
            sx={{
              border: `0.5px solid ${tokens.border}`,
              borderRadius: "6px",
              px: 1.5,
            }}
          >
            {assignment?.pricing.planName && (
              <DetailRow label="Package" value={assignment.pricing.planName} />
            )}
            {assignment?.pricing.costPerSeat != null && (
              <DetailRow
                label="Cost per seat"
                value={formatCost(assignment.pricing.costPerSeat)}
              />
            )}
            {assignment?.pricing.seatCount != null && (
              <DetailRow
                label="Seat count"
                value={String(assignment.pricing.seatCount)}
              />
            )}
            {assignment?.pricing.flatMonthlyCost != null && (
              <DetailRow
                label="Configured monthly"
                value={formatCost(assignment.pricing.flatMonthlyCost)}
              />
            )}
            {pkg?.monthlyBudget != null && (
              <DetailRow label="Monthly budget" value={formatCost(pkg.monthlyBudget)} />
            )}
            {pkg?.alertThresholdUsd != null && (
              <DetailRow
                label="Alert threshold"
                value={formatCost(pkg.alertThresholdUsd)}
              />
            )}
            {pkg?.subscriptionStart && (
              <DetailRow label="Subscription start" value={pkg.subscriptionStart} />
            )}
          </Box>
        </Box>
      )}

      {insights.periods.length > 0 && (
        <Box>
          <Typography
            variant="caption"
            sx={{
              color: tokens.textMuted,
              textTransform: "uppercase",
              display: "block",
              mb: 1,
            }}
          >
            Imported periods ({insights.periods.length})
          </Typography>
          <Box
            sx={{
              border: `0.5px solid ${tokens.border}`,
              borderRadius: "6px",
              px: 1.5,
            }}
          >
            {insights.periods.slice(0, 5).map((period, index) => {
              const label =
                period.billing_period_start && period.billing_period_end
                  ? `${period.billing_period_start} → ${period.billing_period_end}`
                  : period.billing_period_start ?? "Imported";
              return (
                <DetailRow
                  key={`${period.sku}-${index}`}
                  label={label}
                  value={formatCost(Number(period.total_cost))}
                />
              );
            })}
          </Box>
        </Box>
      )}
    </Box>
  );
}

function figmaConfiguredSubscriptionFromAssignment(
  assignment: TeamToolAssignment | null,
): number {
  if (!assignment) {
    return 0;
  }
  const { costPerSeat, seatCount } = assignment.pricing;
  if (costPerSeat == null || seatCount == null) {
    return 0;
  }
  return costPerSeat * seatCount;
}

function FigmaTeamToolSummary({
  insights,
  assignment,
}: {
  insights: FigmaBillingInsights;
  assignment: TeamToolAssignment | null;
}) {
  const configuredSubscription = figmaConfiguredSubscriptionFromAssignment(assignment);
  const subscriptionTotal =
    configuredSubscription > 0
      ? configuredSubscription
      : Number(insights.seat_cost ?? insights.configured_seat_cost ?? 0);
  const paidCredits = Number(insights.credits?.total_paid_credits_used ?? 0);
  const creditsPerUsd = assignment?.pricing.creditsPerUsd ?? null;
  const additionalCost =
    creditsPerUsd != null && paidCredits > 0
      ? paidCredits * creditsPerUsd
      : Number(insights.paid_cost ?? 0);
  const displayTotal = subscriptionTotal + additionalCost;
  const pkg = assignment?.package;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2.5 }}>
      <Box>
        <Typography
          variant="caption"
          sx={{
            color: tokens.textMuted,
            textTransform: "uppercase",
            display: "block",
            mb: 1,
          }}
        >
          Imported billing (all periods)
        </Typography>
        {!insights.has_import && !insights.has_config ? (
          <Alert severity="info">
            Configure Figma seat pricing on this team, then import billing CSV in Uploads.
          </Alert>
        ) : (
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5 }}>
            <UsageStat
              label="Total cost"
              value={
                insights.has_import || subscriptionTotal > 0
                  ? formatCost(displayTotal)
                  : "—"
              }
            />
            <UsageStat
              label="Subscription (configured)"
              value={subscriptionTotal > 0 ? formatCost(subscriptionTotal) : "—"}
            />
            <UsageStat
              label="Additional credits"
              value={
                insights.has_import && paidCredits > 0
                  ? paidCredits.toLocaleString()
                  : "—"
              }
            />
            <UsageStat
              label="Additional cost"
              value={insights.has_import ? formatCost(additionalCost) : "—"}
            />
          </Box>
        )}
        {insights.budget_alert_triggered && (
          <Alert severity="warning" sx={{ mt: 1.5 }}>
            Imported spend reached the configured USD alert threshold
            {insights.alert_threshold_usd != null
              ? ` (${formatCost(Number(insights.alert_threshold_usd))})`
              : ""}
            .
          </Alert>
        )}
      </Box>

      {(assignment?.pricing.costPerSeat != null ||
        assignment?.pricing.viewSeatCostUsd != null ||
        assignment?.pricing.creditsPerUsd != null ||
        pkg?.monthlyBudget != null) && (
        <Box>
          <Typography
            variant="caption"
            sx={{
              color: tokens.textMuted,
              textTransform: "uppercase",
              display: "block",
              mb: 1,
            }}
          >
            Team configuration
          </Typography>
          <Box
            sx={{
              border: `0.5px solid ${tokens.border}`,
              borderRadius: "6px",
              px: 1.5,
            }}
          >
            {assignment?.pricing.costPerSeat != null && (
              <DetailRow
                label="Paid seat cost"
                value={formatCost(assignment.pricing.costPerSeat)}
              />
            )}
            {assignment?.pricing.seatCount != null && (
              <DetailRow
                label="Paid seats"
                value={String(assignment.pricing.seatCount)}
              />
            )}
            {assignment?.pricing.includedCreditsPerSeat != null && (
              <DetailRow
                label="Included credits per seat"
                value={assignment.pricing.includedCreditsPerSeat.toLocaleString()}
              />
            )}
            {assignment?.pricing.viewSeatCostUsd != null && (
              <DetailRow
                label="View seat cost"
                value={formatCost(assignment.pricing.viewSeatCostUsd)}
              />
            )}
            {assignment?.pricing.creditsPerUsd != null && (
              <DetailRow
                label="USD per paid credit"
                value={String(assignment.pricing.creditsPerUsd)}
              />
            )}
            {pkg?.monthlyBudget != null && (
              <DetailRow label="Monthly budget" value={formatCost(pkg.monthlyBudget)} />
            )}
            {pkg?.alertThresholdUsd != null && (
              <DetailRow
                label="Alert threshold"
                value={formatCost(pkg.alertThresholdUsd)}
              />
            )}
          </Box>
        </Box>
      )}

      {insights.periods.length > 0 && (
        <Box>
          <Typography
            variant="caption"
            sx={{
              color: tokens.textMuted,
              textTransform: "uppercase",
              display: "block",
              mb: 1,
            }}
          >
            Imported periods ({insights.periods.length})
          </Typography>
          <Box
            sx={{
              border: `0.5px solid ${tokens.border}`,
              borderRadius: "6px",
              px: 1.5,
            }}
          >
            {insights.periods.slice(0, 5).map((period, index) => {
              const label =
                period.usage_period_start && period.usage_period_end
                  ? `${period.usage_period_start} → ${period.usage_period_end}`
                  : period.usage_period_start ?? "Imported";
              return (
                <DetailRow
                  key={`figma-period-${index}`}
                  label={label}
                  value={formatCost(Number(period.total_cost))}
                />
              );
            })}
          </Box>
        </Box>
      )}
    </Box>
  );
}

export function TeamToolDetailSlideOver({
  open,
  onClose,
  team,
  toolId,
  toolName,
  toolProvider = null,
}: TeamToolDetailSlideOverProps) {
  const monthPeriod = useMemo(() => currentMonthPeriod(), []);

  const catalogToolsQuery = useQuery({
    queryKey: ["tools", "catalog"],
    queryFn: () => fetchTools(),
    enabled: open,
  });

  const catalogTool = catalogToolsQuery.data?.find((tool) => tool.id === toolId);
  const resolvedProvider = toolProvider ?? catalogTool?.provider ?? null;
  const isCopilot = isCopilotProvider(resolvedProvider);
  const isFigma = isFigmaProvider(resolvedProvider);
  const isBillingImportTool = isCopilot || isFigma;

  const assignmentQuery = useQuery({
    queryKey: ["team-tool-assignment", team?.id, toolId, resolvedProvider],
    queryFn: async () => {
      const providerMap =
        toolId && resolvedProvider ? { [toolId]: resolvedProvider as ToolProvider } : undefined;
      const rows = await fetchTeamTools(team!.id, providerMap);
      return rows.find((row) => row.toolId === toolId) ?? null;
    },
    enabled:
      open &&
      Boolean(team?.id) &&
      Boolean(toolId) &&
      (catalogToolsQuery.isSuccess || Boolean(toolProvider)),
  });

  const usageQuery = useQuery({
    queryKey: ["team-tool-usage", team?.id, toolId, monthPeriod.from, monthPeriod.to],
    queryFn: () =>
      fetchDashboardStats(monthPeriod.from, monthPeriod.to, {
        teamId: team!.id,
        toolId: toolId!,
      }),
    enabled: open && Boolean(team?.id) && Boolean(toolId) && !isBillingImportTool,
  });

  const copilotInsightsQuery = useQuery({
    queryKey: ["team-tool-copilot-billing", team?.id, toolId],
    queryFn: () =>
      fetchCopilotBillingInsights(
        team!.id,
        toolId!,
        ALL_TIME_PERIOD.from,
        ALL_TIME_PERIOD.to,
      ),
    enabled: open && Boolean(team?.id) && Boolean(toolId) && isCopilot,
  });

  const figmaInsightsQuery = useQuery({
    queryKey: ["team-tool-figma-billing", team?.id, toolId],
    queryFn: () =>
      fetchFigmaBillingInsights(
        team!.id,
        toolId!,
        ALL_TIME_PERIOD.from,
        ALL_TIME_PERIOD.to,
      ),
    enabled: open && Boolean(team?.id) && Boolean(toolId) && isFigma,
  });

  const assignment = assignmentQuery.data;
  const pricing = assignment?.pricing ?? catalogTool?.pricing;
  const pricingSource = assignment ? "team" : "tool_default";

  const loading = isCopilot
    ? assignmentQuery.isPending ||
      catalogToolsQuery.isPending ||
      copilotInsightsQuery.isPending
    : isFigma
      ? assignmentQuery.isPending ||
        catalogToolsQuery.isPending ||
        figmaInsightsQuery.isPending
      : assignmentQuery.isPending || catalogToolsQuery.isPending || usageQuery.isPending;

  const error = isCopilot
    ? assignmentQuery.isError || catalogToolsQuery.isError || copilotInsightsQuery.isError
    : isFigma
      ? assignmentQuery.isError || catalogToolsQuery.isError || figmaInsightsQuery.isError
      : assignmentQuery.isError || catalogToolsQuery.isError || usageQuery.isError;

  return (
    <SlideOver
      open={open}
      onClose={onClose}
      title={toolName}
      subtitle={team ? `${team.name} · tool details` : undefined}
      width={480}
    >
      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {error && !loading && (
        <Alert severity="error">Failed to load tool details. Please try again.</Alert>
      )}

      {!loading && !error && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {catalogTool && (
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <StatusBadge status={catalogTool.status} />
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                Provider: {(resolvedProvider ?? catalogTool.provider).replace(/_/g, " ")}
              </Typography>
            </Box>
          )}

          {isCopilot ? (
            copilotInsightsQuery.data ? (
              <CopilotTeamToolSummary
                insights={copilotInsightsQuery.data}
                assignment={assignment ?? null}
              />
            ) : null
          ) : isFigma ? (
            figmaInsightsQuery.data ? (
              <FigmaTeamToolSummary
                insights={figmaInsightsQuery.data}
                assignment={assignment ?? null}
              />
            ) : null
          ) : (
            <>
              <Box>
                <Typography
                  variant="caption"
                  sx={{
                    color: tokens.textMuted,
                    textTransform: "uppercase",
                    display: "block",
                    mb: 1,
                  }}
                >
                  Current usage (this month)
                </Typography>
                {usageQuery.data ? (
                  <UsageBreakdownStats stats={usageQuery.data} showIncludedCost />
                ) : (
                  <Box sx={{ display: "flex", gap: 1.5 }}>
                    <UsageStat label="Tokens" value={formatTokens(0)} />
                    <UsageStat label="Cost" value={formatCost(0)} />
                  </Box>
                )}
              </Box>

              {catalogTool && (
                <Box>
                  <Typography
                    variant="caption"
                    sx={{
                      color: tokens.textMuted,
                      textTransform: "uppercase",
                      display: "block",
                      mb: 1,
                    }}
                  >
                    Tool snapshot
                  </Typography>
                  <Box
                    sx={{
                      border: `0.5px solid ${tokens.border}`,
                      borderRadius: "6px",
                      px: 1.5,
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        py: 0.75,
                        borderBottom: `0.5px solid ${tokens.border}`,
                      }}
                    >
                      <Typography variant="body2" sx={{ color: tokens.textMuted }}>
                        Org-wide tokens (synced)
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {formatTokens(catalogTool.tokenCount)}
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        py: 0.75,
                        borderBottom: `0.5px solid ${tokens.border}`,
                      }}
                    >
                      <Typography variant="body2" sx={{ color: tokens.textMuted }}>
                        Org-wide cost (synced)
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {formatCost(catalogTool.costTotal)}
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        py: 0.75,
                      }}
                    >
                      <Typography variant="body2" sx={{ color: tokens.textMuted }}>
                        Members
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {catalogTool.memberCount.toLocaleString("en-US")}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              )}
            </>
          )}

          {!isBillingImportTool &&
            (pricing ? (
              <TeamToolPricingSummary pricing={pricing} pricingSource={pricingSource} />
            ) : (
              <Alert severity="info">
                No pricing configured for this tool. Edit the team to set tool pricing.
              </Alert>
            ))}
        </Box>
      )}
    </SlideOver>
  );
}

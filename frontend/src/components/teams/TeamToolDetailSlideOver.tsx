import { Alert, Box, CircularProgress, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { endOfDay, startOfMonth } from "date-fns";
import { useMemo } from "react";

import { fetchTeamToolAssignment } from "@/api/teamTools";
import { fetchTools } from "@/api/tools";
import { fetchUsageSummary } from "@/api/usage";
import type { Team } from "@/api/teams";
import { SlideOver } from "@/components/layout/SlideOver";
import { TeamToolPricingSummary } from "@/components/teams/TeamToolPricingSummary";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { tokens } from "@/theme/palette";
import { formatCost, formatTokens } from "@/utils/formatters";

interface TeamToolDetailSlideOverProps {
  open: boolean;
  onClose: () => void;
  team: Team | null;
  toolId: string | null;
  toolName: string;
}

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

export function TeamToolDetailSlideOver({
  open,
  onClose,
  team,
  toolId,
  toolName,
}: TeamToolDetailSlideOverProps) {
  const period = useMemo(() => currentMonthPeriod(), []);

  const assignmentQuery = useQuery({
    queryKey: ["team-tool-assignment", team?.id, toolId],
    queryFn: () => fetchTeamToolAssignment(team!.id, toolId!),
    enabled: open && Boolean(team?.id) && Boolean(toolId),
  });

  const catalogToolsQuery = useQuery({
    queryKey: ["tools", "catalog"],
    queryFn: fetchTools,
    enabled: open,
  });

  const usageQuery = useQuery({
    queryKey: ["team-tool-usage", team?.id, toolId, period.from, period.to],
    queryFn: () =>
      fetchUsageSummary(period.from, period.to, {
        teamId: team!.id,
        toolId: toolId!,
      }),
    enabled: open && Boolean(team?.id) && Boolean(toolId),
  });

  const catalogTool = catalogToolsQuery.data?.find((tool) => tool.id === toolId);
  const assignment = assignmentQuery.data;
  const pricing = assignment?.pricing ?? catalogTool?.pricing;
  const pricingSource = assignment ? "team" : "tool_default";

  const loading =
    assignmentQuery.isPending || catalogToolsQuery.isPending || usageQuery.isPending;
  const error =
    assignmentQuery.isError || catalogToolsQuery.isError || usageQuery.isError;

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
                Provider: {catalogTool.provider.replace(/_/g, " ")}
              </Typography>
            </Box>
          )}

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
            <Box sx={{ display: "flex", gap: 1.5 }}>
              <UsageStat
                label="Tokens"
                value={formatTokens(usageQuery.data?.totalTokens ?? 0)}
              />
              <UsageStat
                label="Cost"
                value={formatCost(usageQuery.data?.totalCost ?? 0)}
                subvalue={
                  usageQuery.data && usageQuery.data.totalTokens > 0
                    ? `${formatCost(usageQuery.data.avgCostPerToken)} / token`
                    : undefined
                }
              />
            </Box>
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

          {pricing ? (
            <TeamToolPricingSummary pricing={pricing} pricingSource={pricingSource} />
          ) : (
            <Alert severity="info">
              No pricing configured for this tool. Edit the team to set tool pricing.
            </Alert>
          )}
        </Box>
      )}
    </SlideOver>
  );
}

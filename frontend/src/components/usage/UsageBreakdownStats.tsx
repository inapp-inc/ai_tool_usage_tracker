import { Box, Typography } from "@mui/material";

import type { DashboardStats } from "@/api/dashboard";
import { tokens } from "@/theme/palette";
import { formatCost, formatTokens } from "@/utils/formatters";

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

interface UsageBreakdownStatsProps {
  stats: DashboardStats;
  showIncludedCost?: boolean;
}

export function UsageBreakdownStats({
  stats,
  showIncludedCost = false,
}: UsageBreakdownStatsProps) {
  if (stats.breakdownAvailable) {
    return (
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5 }}>
        <UsageStat label="Total tokens" value={formatTokens(stats.totalTokens)} />
        <UsageStat
          label="Included in plan"
          value={formatTokens(stats.includedTokens ?? 0)}
          subvalue={
            showIncludedCost
              ? formatCost(stats.includedCost ?? 0)
              : undefined
          }
        />
        <UsageStat
          label="Additional billable"
          value={formatTokens(stats.billableTokens ?? 0)}
        />
        <UsageStat
          label="Billable cost"
          value={formatCost(stats.billableCost ?? 0)}
          subvalue="beyond package"
        />
        {showIncludedCost && (
          <UsageStat
            label="Total cost"
            value={formatCost(stats.totalCost)}
            subvalue="included + billable"
          />
        )}
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", gap: 1.5 }}>
      <UsageStat label="Total tokens" value={formatTokens(stats.totalTokens)} />
      <UsageStat label="Total cost" value={formatCost(stats.totalCost)} />
    </Box>
  );
}

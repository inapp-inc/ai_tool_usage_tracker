import {
  IconActivity,
  IconCurrencyDollar,
  IconInfoCircle,
  IconUsers,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Skeleton,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { endOfDay, startOfDay, subDays } from "date-fns";
import { useMemo, useState } from "react";

import { fetchMyUsage } from "@/api/usage";
import { StatCard } from "@/components/data-display/StatCard";
import { SkeletonCard } from "@/components/data-display/SkeletonCard";
import { PeriodSelector } from "@/components/inputs/PeriodSelector";
import type { DateRange } from "@/types";
import { tokens } from "@/theme/palette";
import { formatCost, formatTokens } from "@/utils/formatters";

function createDefaultPeriod(): DateRange {
  const today = new Date();
  return {
    from: startOfDay(subDays(today, 30)).toISOString(),
    to: endOfDay(today).toISOString(),
  };
}

export function MyUsagePage() {
  const [period, setPeriod] = useState<DateRange>(createDefaultPeriod);

  const { data, isPending, isError } = useQuery({
    queryKey: ["my-usage", period.from, period.to],
    queryFn: () => fetchMyUsage(period.from, period.to),
  });

  const totalTokens = useMemo(
    () => (data?.teams ?? []).reduce((sum, t) => sum + t.total_tokens, 0),
    [data],
  );

  const totalCost = useMemo(
    () => (data?.teams ?? []).reduce((sum, t) => sum + t.estimated_cost, 0),
    [data],
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Box>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          My Usage
        </Typography>
        {data && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              {data.display_name ?? data.email}
            </Typography>
            <Chip
              label={data.role.replace("_", " ")}
              size="small"
              sx={{ fontSize: "0.6875rem", height: 18 }}
            />
          </Box>
        )}
      </Box>

      <PeriodSelector value={period} onChange={setPeriod} />

      <Alert
        severity="info"
        icon={<IconInfoCircle size={16} />}
        sx={{ fontSize: "0.8125rem" }}
      >
        Usage figures represent your team's total consumption. Individual-level
        tracking will be available once provider sync is enabled.
      </Alert>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "16px",
        }}
      >
        {isPending ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : isError ? null : (
          <>
            <StatCard
              label="My Teams' Tokens"
              value={formatTokens(totalTokens)}
              icon={IconActivity}
              iconColor={tokens.primary}
            />
            <StatCard
              label="My Teams' Cost"
              value={formatCost(totalCost)}
              icon={IconCurrencyDollar}
              iconColor={tokens.success}
            />
            <StatCard
              label="Teams"
              value={(data?.teams ?? []).length}
              icon={IconUsers}
              iconColor="#F59E0B"
            />
          </>
        )}
      </Box>

      {isError && (
        <Alert severity="error">Failed to load usage data. Please refresh.</Alert>
      )}

      {!isError && (
        <Card>
          <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
              Team Breakdown
            </Typography>

            {isPending ? (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                {[1, 2].map((i) => (
                  <Skeleton key={i} variant="rounded" height={60} />
                ))}
              </Box>
            ) : (data?.teams ?? []).length === 0 ? (
              <Typography
                variant="body2"
                sx={{ color: tokens.textMuted, textAlign: "center", py: 3 }}
              >
                You are not a member of any team yet.
              </Typography>
            ) : (
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                {(data?.teams ?? []).map((team) => (
                  <Box
                    key={team.team_id}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      p: "12px 16px",
                      borderRadius: "8px",
                      border: `0.5px solid ${tokens.border}`,
                      backgroundColor: tokens.surface,
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: "6px",
                          backgroundColor: "rgba(59,130,246,0.1)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          flexShrink: 0,
                        }}
                      >
                        <IconUsers size={14} color={tokens.primary} />
                      </Box>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {team.team_name}
                      </Typography>
                    </Box>

                    <Box
                      sx={{
                        display: "flex",
                        gap: 3,
                        alignItems: "center",
                      }}
                    >
                      <Box sx={{ textAlign: "right" }}>
                        <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                          Tokens
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {formatTokens(team.total_tokens)}
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: "right" }}>
                        <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                          Cost
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {formatCost(team.estimated_cost)}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

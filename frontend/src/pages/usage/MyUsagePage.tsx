import { Box, Card, CardContent, Divider, Skeleton, Typography } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { endOfDay, startOfDay, subDays } from "date-fns";
import { useState } from "react";

import { fetchMyUsage } from "@/api/usage";
import { StatCard } from "@/components/data-display/StatCard";
import { PeriodSelector } from "@/components/inputs/PeriodSelector";
import type { DateRange } from "@/types";

function defaultPeriod(): DateRange {
  return {
    from: startOfDay(subDays(new Date(), 29)).toISOString(),
    to: endOfDay(new Date()).toISOString(),
  };
}

export function MyUsagePage() {
  const [period, setPeriod] = useState<DateRange>(defaultPeriod);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["my-usage", period.from, period.to],
    queryFn: () => fetchMyUsage(period.from, period.to),
  });

  return (
    <Box sx={{ p: 3 }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 3,
        }}
      >
        <Typography variant="h5" fontWeight={600}>
          My Usage
        </Typography>
        <PeriodSelector value={period} onChange={setPeriod} />
      </Box>

      <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
        {isLoading ? (
          <>
            <Skeleton variant="rounded" width={200} height={100} />
            <Skeleton variant="rounded" width={200} height={100} />
          </>
        ) : data ? (
          <>
            <StatCard
              label="Total Tokens"
              value={data.totalTokens.toLocaleString()}
            />
            <StatCard
              label="Total Cost"
              value={`$${data.totalCost.toFixed(2)}`}
            />
          </>
        ) : null}
      </Box>

      {isError && (
        <Typography color="error">Failed to load usage data.</Typography>
      )}
      {!isLoading && data && data.tools.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
              Usage by Tool
            </Typography>
            {data.tools.map((tool, i) => (
              <Box key={tool.toolId}>
                <Box sx={{ display: "flex", justifyContent: "space-between", py: 1 }}>
                  <Typography variant="body2">{tool.toolName}</Typography>
                  <Box sx={{ textAlign: "right" }}>
                    <Typography variant="body2">
                      {tool.tokens.toLocaleString()} tokens
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ${tool.cost.toFixed(2)}
                    </Typography>
                  </Box>
                </Box>
                {i < data.tools.length - 1 && <Divider />}
              </Box>
            ))}
          </CardContent>
        </Card>
      )}
      {!isLoading && data && data.tools.length === 0 && (
        <Typography color="text.secondary">No usage recorded for this period.</Typography>
      )}
    </Box>
  );
}

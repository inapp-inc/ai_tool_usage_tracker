import { Box, Typography } from "@mui/material";

import type { PricingModel, ToolPricing } from "@/api/adapters/tools";
import { tokens } from "@/theme/palette";
import { formatCost, formatTokens } from "@/utils/formatters";

const MODEL_LABELS: Record<PricingModel, string> = {
  per_token: "Per token",
  per_seat: "Per seat",
  flat_fee: "Flat fee",
  hybrid: "Hybrid",
};

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

function formatUsd(value: number | null): string {
  if (value == null) {
    return "—";
  }
  return formatCost(value);
}

function formatCount(value: number | null): string {
  if (value == null) {
    return "—";
  }
  return value.toLocaleString("en-US");
}

interface TeamToolPricingSummaryProps {
  pricing: ToolPricing;
  pricingSource: "team" | "tool_default";
}

export function TeamToolPricingSummary({
  pricing,
  pricingSource,
}: TeamToolPricingSummaryProps) {
  const showTokenFields = pricing.model === "per_token" || pricing.model === "hybrid";
  const showSeatFields = pricing.model === "per_seat" || pricing.model === "hybrid";
  const showPackageFields = pricing.model === "flat_fee" || pricing.model === "hybrid";

  return (
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
        Pricing ({pricingSource === "team" ? "team override" : "tool default"})
      </Typography>

      <Box
        sx={{
          border: `0.5px solid ${tokens.border}`,
          borderRadius: "6px",
          px: 1.5,
        }}
      >
        <DetailRow label="Model" value={MODEL_LABELS[pricing.model]} />

        {showTokenFields && (
          <>
            <DetailRow
              label="Input cost / 1K"
              value={formatUsd(pricing.inputCostPer1K)}
            />
            <DetailRow
              label="Output cost / 1K"
              value={formatUsd(pricing.outputCostPer1K)}
            />
          </>
        )}

        {showSeatFields && (
          <>
            <DetailRow label="Cost per seat" value={formatUsd(pricing.costPerSeat)} />
            <DetailRow label="Seat count" value={formatCount(pricing.seatCount)} />
          </>
        )}

        {showPackageFields && (
          <>
            <DetailRow label="Plan" value={pricing.planName ?? "—"} />
            <DetailRow
              label="Flat monthly cost"
              value={formatUsd(pricing.flatMonthlyCost)}
            />
            <DetailRow
              label="Included tokens"
              value={
                pricing.includedTokens != null
                  ? formatTokens(pricing.includedTokens)
                  : "—"
              }
            />
            <DetailRow label="Overage rate" value={formatUsd(pricing.overageRate)} />
          </>
        )}
      </Box>
    </Box>
  );
}

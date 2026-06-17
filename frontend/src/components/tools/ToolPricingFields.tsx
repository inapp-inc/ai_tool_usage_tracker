import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";

import type { PricingModel, ToolPricing } from "@/api/adapters/tools";
import { tokens } from "@/theme/palette";

const MODEL_LABELS: Record<PricingModel, string> = {
  per_token: "Per token",
  per_seat: "Per seat",
  flat_fee: "Flat fee",
  hybrid: "Hybrid",
};

function parseOptionalNumber(value: string): number | null {
  if (value.trim() === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

interface ToolPricingFieldsProps {
  value: ToolPricing;
  onChange: (value: ToolPricing) => void;
  disabled?: boolean;
}

export function ToolPricingFields({
  value,
  onChange,
  disabled = false,
}: ToolPricingFieldsProps) {
  const set = (patch: Partial<ToolPricing>) => onChange({ ...value, ...patch });

  const showTokenFields = value.model === "per_token" || value.model === "hybrid";
  const showSeatFields = value.model === "per_seat" || value.model === "hybrid";
  const showPackageFields = value.model === "flat_fee" || value.model === "hybrid";

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      <FormControl fullWidth size="small" disabled={disabled}>
        <InputLabel id="pricing-model-label">Pricing model</InputLabel>
        <Select
          labelId="pricing-model-label"
          label="Pricing model"
          value={value.model}
          onChange={(event) => set({ model: event.target.value as PricingModel })}
        >
          {(Object.keys(MODEL_LABELS) as PricingModel[]).map((model) => (
            <MenuItem key={model} value={model}>
              {MODEL_LABELS[model]}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {showTokenFields && (
        <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
          <TextField
            fullWidth
            size="small"
            label="Input cost / 1K (USD)"
            type="number"
            disabled={disabled}
            value={value.inputCostPer1K ?? ""}
            onChange={(event) =>
              set({ inputCostPer1K: parseOptionalNumber(event.target.value) })
            }
          />
          <TextField
            fullWidth
            size="small"
            label="Output cost / 1K (USD)"
            type="number"
            disabled={disabled}
            value={value.outputCostPer1K ?? ""}
            onChange={(event) =>
              set({ outputCostPer1K: parseOptionalNumber(event.target.value) })
            }
          />
        </Box>
      )}

      {showSeatFields && (
        <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
          <TextField
            fullWidth
            size="small"
            label="Cost per seat (USD)"
            type="number"
            disabled={disabled}
            value={value.costPerSeat ?? ""}
            onChange={(event) =>
              set({ costPerSeat: parseOptionalNumber(event.target.value) })
            }
          />
          <TextField
            fullWidth
            size="small"
            label="Seat count"
            type="number"
            disabled={disabled}
            value={value.seatCount ?? ""}
            onChange={(event) =>
              set({ seatCount: parseOptionalNumber(event.target.value) })
            }
          />
        </Box>
      )}

      {showPackageFields && (
        <>
          <TextField
            fullWidth
            size="small"
            label="Plan name"
            disabled={disabled}
            value={value.planName ?? ""}
            onChange={(event) => set({ planName: event.target.value || null })}
          />
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
            <TextField
              fullWidth
              size="small"
              label="Flat monthly cost (USD)"
              type="number"
              disabled={disabled}
              value={value.flatMonthlyCost ?? ""}
              onChange={(event) =>
                set({ flatMonthlyCost: parseOptionalNumber(event.target.value) })
              }
            />
            <TextField
              fullWidth
              size="small"
              label="Included tokens"
              type="number"
              disabled={disabled}
              value={value.includedTokens ?? ""}
              onChange={(event) =>
                set({ includedTokens: parseOptionalNumber(event.target.value) })
              }
            />
          </Box>
          <TextField
            fullWidth
            size="small"
            label="Overage rate (USD)"
            type="number"
            disabled={disabled}
            value={value.overageRate ?? ""}
            onChange={(event) =>
              set({ overageRate: parseOptionalNumber(event.target.value) })
            }
          />
        </>
      )}

      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
        Leave fields blank to use the tool&apos;s default pricing where applicable.
      </Typography>
    </Box>
  );
}

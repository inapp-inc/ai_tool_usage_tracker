import {
  Box,
  CircularProgress,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";

import {
  emptyTeamToolPackageBinding,
  type TeamToolPackageBinding,
} from "@/api/adapters/teamTools";
import {
  fetchToolPackages,
  normalizePricing,
  pricingFromPackage,
  type ToolPackage,
  type ToolPricing,
} from "@/api/tools";

interface TeamToolPackageSelectorProps {
  toolId: string;
  value: TeamToolPackageBinding;
  pricing: ToolPricing;
  onChange: (next: TeamToolPackageBinding) => void;
  onPricingChange: (next: ToolPricing) => void;
  disabled?: boolean;
}

function formatPackageLabel(pkg: ToolPackage): string {
  const parts = [pkg.packageName];
  if (pkg.monthlyPrice != null) {
    parts.push(`$${pkg.monthlyPrice}/mo`);
  }
  if (pkg.tokenLimit != null) {
    parts.push(`${pkg.tokenLimit.toLocaleString()} tokens`);
  }
  if (pkg.requestLimit != null) {
    parts.push(`${pkg.requestLimit.toLocaleString()} requests`);
  }
  if (pkg.seatLimit != null) {
    parts.push(`${pkg.seatLimit} seats`);
  }
  return parts.join(" · ");
}

export function TeamToolPackageSelector({
  toolId,
  value,
  pricing,
  onChange,
  onPricingChange,
  disabled = false,
}: TeamToolPackageSelectorProps) {
  const packagesQuery = useQuery({
    queryKey: ["tool-packages", toolId],
    queryFn: () => fetchToolPackages(toolId),
    enabled: Boolean(toolId),
  });

  const packages = packagesQuery.data ?? [];
  const binding = value ?? emptyTeamToolPackageBinding();

  const applyPackage = (packageId: string) => {
    const selected = packages.find((row) => row.id === packageId);
    if (!selected) {
      onChange({ ...binding, packageId: packageId || null });
      return;
    }
    onChange({ ...binding, packageId: selected.id });
    onPricingChange(normalizePricing({ ...pricing, ...pricingFromPackage(selected) }));
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5, mb: 2 }}>
      <FormControl fullWidth size="small" disabled={disabled || packagesQuery.isPending}>
        <InputLabel id={`tool-package-${toolId}`}>Subscription package</InputLabel>
        <Select
          labelId={`tool-package-${toolId}`}
          label="Subscription package"
          value={binding.packageId ?? ""}
          onChange={(event) => applyPackage(String(event.target.value))}
          displayEmpty
        >
          <MenuItem value="">
            <em>Custom pricing</em>
          </MenuItem>
          {packages.map((pkg) => (
            <MenuItem key={pkg.id} value={pkg.id}>
              {formatPackageLabel(pkg)}
            </MenuItem>
          ))}
        </Select>
        {packagesQuery.isPending ? (
          <FormHelperText sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <CircularProgress size={12} />
            Loading packages…
          </FormHelperText>
        ) : packages.length === 0 ? (
          <FormHelperText>No predefined packages — configure pricing manually below</FormHelperText>
        ) : (
          <FormHelperText>Select a vendor package or use custom pricing</FormHelperText>
        )}
      </FormControl>

      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
        <TextField
          label="Subscription start"
          type="date"
          size="small"
          InputLabelProps={{ shrink: true }}
          value={binding.subscriptionStart ?? ""}
          onChange={(event) =>
            onChange({ ...binding, subscriptionStart: event.target.value || null })
          }
          disabled={disabled}
        />
        <TextField
          label="Subscription end"
          type="date"
          size="small"
          InputLabelProps={{ shrink: true }}
          value={binding.subscriptionEnd ?? ""}
          onChange={(event) =>
            onChange({ ...binding, subscriptionEnd: event.target.value || null })
          }
          disabled={disabled}
        />
        <TextField
          label="Monthly budget (USD)"
          type="number"
          size="small"
          value={binding.monthlyBudget ?? ""}
          onChange={(event) =>
            onChange({
              ...binding,
              monthlyBudget:
                event.target.value === "" ? null : Number(event.target.value),
            })
          }
          disabled={disabled}
        />
        <TextField
          label="Alert threshold (%)"
          type="number"
          size="small"
          inputProps={{ min: 0, max: 100 }}
          value={binding.alertThreshold ?? ""}
          onChange={(event) =>
            onChange({
              ...binding,
              alertThreshold:
                event.target.value === "" ? null : Number(event.target.value),
            })
          }
          disabled={disabled}
        />
      </Box>
    </Box>
  );
}

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
  type BillingType,
  type PricingModel,
  type ToolPackage,
  type ToolPricing,
  type ToolProvider,
} from "@/api/tools";

const BILLING_TYPE_LABELS: Record<BillingType, string> = {
  TOKEN_BASED: "Token based",
  REQUEST_BASED: "Request based",
  CREDIT_BASED: "Credit based",
  SEAT_BASED: "Seat based",
  LICENSE_BASED: "License based",
};

const COPILOT_PRICING_MODELS: PricingModel[] = ["per_seat", "per_team"];

const COPILOT_PRICING_MODEL_LABELS: Record<"per_seat" | "per_team", string> = {
  per_seat: "Per seat",
  per_team: "Per team (flat fee)",
};

interface TeamToolPackageSelectorProps {
  toolId: string;
  vendor?: ToolProvider;
  value: TeamToolPackageBinding;
  pricing: ToolPricing;
  onChange: (next: Partial<TeamToolPackageBinding>) => void;
  onPricingChange: (next: ToolPricing) => void;
  disabled?: boolean;
  teamMemberCount?: number;
}

function copilotConfiguredTotal(pricing: ToolPricing): number | null {
  if (pricing.model === "per_team") {
    if (pricing.flatMonthlyCost == null || pricing.seatCount == null) {
      return null;
    }
    return pricing.flatMonthlyCost * pricing.seatCount;
  }
  if (pricing.costPerSeat == null || pricing.seatCount == null) {
    return null;
  }
  return pricing.costPerSeat * pricing.seatCount;
}

function figmaConfiguredTotal(pricing: ToolPricing): number | null {
  if (pricing.costPerSeat == null || pricing.seatCount == null) {
    return null;
  }
  return pricing.costPerSeat * pricing.seatCount;
}

function copilotCountLabel(model: PricingModel, creditPackage: boolean): string {
  if (creditPackage) {
    return model === "per_team" ? "Team members" : "Number of users";
  }
  return model === "per_team" ? "Team members" : "Team size";
}

function copilotCountHelper(
  model: PricingModel,
  teamMemberCount: number,
  creditPackage: boolean,
): string {
  if (teamMemberCount > 0) {
    return `${teamMemberCount} members on this team`;
  }
  if (creditPackage) {
    return model === "per_team"
      ? "How many teams or members use AI credits"
      : "How many users consume AI credits";
  }
  return model === "per_team"
    ? "Enter expected team members billed for Copilot"
    : "Enter expected Copilot seats for this team";
}

function copilotCostLabel(model: PricingModel, creditPackage: boolean): string {
  if (creditPackage) {
    return model === "per_team" ? "Cost per team (USD)" : "Cost per user (USD)";
  }
  return model === "per_team" ? "Cost per team (USD)" : "Cost per seat (USD)";
}

function copilotTotalHelper(model: PricingModel, creditPackage: boolean): string {
  if (creditPackage) {
    return model === "per_team"
      ? "Cost per team × team members — actual credit spend comes from CSV imports"
      : "Cost per user × user count — actual credit spend comes from CSV imports";
  }
  return model === "per_team"
    ? "Cost per team × team members — compare with CSV import totals in Insights"
    : "Cost per seat × team size — compare with CSV import totals in Insights";
}

function copilotModelOptions(creditPackage: boolean): Array<{
  value: "per_seat" | "per_team";
  label: string;
}> {
  if (creditPackage) {
    return [
      { value: "per_seat", label: "Per user" },
      { value: "per_team", label: "Per team" },
    ];
  }
  return COPILOT_PRICING_MODELS.map((model) => ({
    value: model as "per_seat" | "per_team",
    label: COPILOT_PRICING_MODEL_LABELS[model as "per_seat" | "per_team"],
  }));
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
  vendor,
  value,
  pricing,
  onChange,
  onPricingChange,
  disabled = false,
  teamMemberCount = 0,
}: TeamToolPackageSelectorProps) {
  const isCopilot = vendor === "copilot";
  const isFigma = vendor === "figma";
  const requiresPackage = isCopilot || isFigma;

  const packagesQuery = useQuery({
    queryKey: ["tool-packages", toolId],
    queryFn: () => fetchToolPackages(toolId),
    enabled: Boolean(toolId),
  });

  const packages = packagesQuery.data ?? [];
  const binding = value ?? emptyTeamToolPackageBinding();
  const selectedPackage =
    packages.find((row) => row.id === binding.packageId) ?? null;

  const isCopilotCreditPackage =
    isCopilot &&
    selectedPackage != null &&
    (selectedPackage.billingType === "CREDIT_BASED" ||
      selectedPackage.packageName.toLowerCase().includes("credit"));
  const pricingType = selectedPackage?.billingType ?? binding.billingType ?? null;
  const showCopilotPricingFields = isCopilot;
  const showFigmaPricingFields = isFigma;
  const copilotModel: PricingModel =
    pricing.model === "per_team" ? "per_team" : "per_seat";

  const syncCopilotBudget = (nextPricing: ToolPricing) => {
    const total = copilotConfiguredTotal(nextPricing);
    if (total == null) {
      return;
    }
    onChange({ monthlyBudget: total });
  };

  const syncFigmaBudget = (nextPricing: ToolPricing) => {
    const total = figmaConfiguredTotal(nextPricing);
    if (total == null) {
      return;
    }
    onChange({ monthlyBudget: total });
  };

  const applyCopilotPricingPatch = (patch: Partial<ToolPricing>) => {
    const nextPricing = normalizePricing({ ...pricing, ...patch });
    onPricingChange(nextPricing);
    syncCopilotBudget(nextPricing);
  };

  const applyFigmaPricingPatch = (patch: Partial<ToolPricing>) => {
    const nextPricing = normalizePricing({ ...pricing, ...patch });
    onPricingChange(nextPricing);
    syncFigmaBudget(nextPricing);
  };

  const applyPackage = (packageId: string) => {
    const selected = packages.find((row) => row.id === packageId);
    if (!selected) {
      onChange({ packageId: packageId || null, billingType: null });
      return;
    }
    const nextBinding: TeamToolPackageBinding = {
      ...binding,
      packageId: selected.id,
      billingType: selected.billingType,
    };
    const fromPackage = pricingFromPackage(selected, vendor);
    const defaultTeamSize =
      teamMemberCount > 0 ? teamMemberCount : (fromPackage.seatCount ?? 1);
    const nextPricing = normalizePricing({
      ...fromPackage,
      seatCount: isCopilot || isFigma ? defaultTeamSize : fromPackage.seatCount,
    });
    onPricingChange(nextPricing);
    const copilotTotal = copilotConfiguredTotal(nextPricing);
    const figmaTotal = figmaConfiguredTotal(nextPricing);
    onChange({
      ...nextBinding,
      monthlyBudget: copilotTotal ?? figmaTotal ?? nextBinding.monthlyBudget,
    });
  };

  const figmaSubscriptionTotal = figmaConfiguredTotal(pricing);

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
          required={requiresPackage}
        >
          {!requiresPackage && (
            <MenuItem value="">
              <em>Custom pricing</em>
            </MenuItem>
          )}
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
        ) : isCopilot ? (
          <FormHelperText>Required for Copilot — matches GitHub billing SKU</FormHelperText>
        ) : isFigma ? (
          <FormHelperText>Required for Figma — aligns seat credit amounts with your plan</FormHelperText>
        ) : (
          <FormHelperText>Select a vendor package or use custom pricing</FormHelperText>
        )}
      </FormControl>

      {pricingType && (
        <FormControl fullWidth size="small" disabled>
          <InputLabel id={`pricing-type-${toolId}`}>Pricing type</InputLabel>
          <Select
            labelId={`pricing-type-${toolId}`}
            label="Pricing type"
            value={pricingType}
          >
            <MenuItem value={pricingType}>{BILLING_TYPE_LABELS[pricingType]}</MenuItem>
          </Select>
          <FormHelperText>Derived from the selected subscription package</FormHelperText>
        </FormControl>
      )}

      {showFigmaPricingFields && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <FormHelperText sx={{ mx: 0 }}>
            Subscription is paid seats × monthly seat price (e.g. 11 × $55). Each seat includes
            package AI credits. CSV imports add paid-credit overage only: paid credits used × USD
            per paid credit.
          </FormHelperText>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
            <TextField
              label="Paid seat cost (USD/month)"
              type="number"
              size="small"
              inputProps={{ min: 0, step: 0.01 }}
              value={pricing.costPerSeat ?? ""}
              onChange={(event) => {
                const parsed =
                  event.target.value === "" ? null : Number(event.target.value);
                applyFigmaPricingPatch({
                  model: "per_seat",
                  costPerSeat: Number.isNaN(parsed) ? null : parsed,
                });
              }}
              disabled={disabled}
              helperText="Monthly cost per paid seat (e.g. $55)"
            />
            <TextField
              label="Number of paid seats"
              type="number"
              size="small"
              inputProps={{ min: 1, step: 1 }}
              value={pricing.seatCount ?? ""}
              onChange={(event) => {
                const parsed =
                  event.target.value === "" ? null : Number(event.target.value);
                applyFigmaPricingPatch({
                  model: "per_seat",
                  seatCount: Number.isNaN(parsed) ? null : parsed,
                });
              }}
              disabled={disabled}
              helperText={
                teamMemberCount > 0
                  ? `${teamMemberCount} members on this team`
                  : "Configured paid seats for this team (e.g. 11)"
              }
            />
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
            <TextField
              label="Included credits per seat"
              type="number"
              size="small"
              inputProps={{ min: 0, step: 1 }}
              value={pricing.includedCreditsPerSeat ?? ""}
              onChange={(event) => {
                const parsed =
                  event.target.value === "" ? null : Number(event.target.value);
                onPricingChange(
                  normalizePricing({
                    ...pricing,
                    model: "per_seat",
                    includedCreditsPerSeat: Number.isNaN(parsed) ? null : parsed,
                  }),
                );
              }}
              disabled={disabled}
              helperText="Package allowance (e.g. 3500) — tracked, not billed from CSV"
            />
            <TextField
              label="View seat cost (USD/month)"
              type="number"
              size="small"
              inputProps={{ min: 0, step: 0.01 }}
              value={pricing.viewSeatCostUsd ?? ""}
              onChange={(event) => {
                const parsed =
                  event.target.value === "" ? null : Number(event.target.value);
                applyFigmaPricingPatch({
                  model: "per_seat",
                  viewSeatCostUsd: Number.isNaN(parsed) ? null : parsed,
                });
              }}
              disabled={disabled}
              helperText="Optional view/collab seat package amount"
            />
          </Box>
          <TextField
            label="USD per paid credit"
            type="number"
            size="small"
            inputProps={{ min: 0.0001, step: 0.001 }}
            value={pricing.creditsPerUsd ?? ""}
            onChange={(event) => {
              const parsed =
                event.target.value === "" ? null : Number(event.target.value);
              onPricingChange(
                normalizePricing({
                  ...pricing,
                  model: "per_seat",
                  creditsPerUsd: Number.isNaN(parsed) ? null : parsed,
                }),
              );
            }}
            disabled={disabled}
            helperText="Paid credits used × this value = additional cost (e.g. 0.03 from $30/1000 credits)"
          />
          {figmaSubscriptionTotal != null && (
            <TextField
              label="Configured subscription total (USD/month)"
              type="number"
              size="small"
              value={figmaSubscriptionTotal}
              disabled
              helperText="Paid seat cost × number of paid seats — CSV overage is added in Insights"
            />
          )}
        </Box>
      )}

      {showCopilotPricingFields && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          {isCopilotCreditPackage && (
            <FormHelperText sx={{ mx: 0 }}>
              Configure expected credit allocation below. Actual AI credit spend is calculated from
              billing CSV imports in Insights.
            </FormHelperText>
          )}

          <FormControl fullWidth size="small" disabled={disabled}>
            <InputLabel id={`copilot-pricing-model-${toolId}`}>Pricing model</InputLabel>
            <Select
              labelId={`copilot-pricing-model-${toolId}`}
              label="Pricing model"
              value={copilotModel}
              onChange={(event) => {
                const model = event.target.value as "per_seat" | "per_team";
                if (model === "per_team") {
                  applyCopilotPricingPatch({
                    model: "per_team",
                    costPerSeat: null,
                    flatMonthlyCost: pricing.costPerSeat ?? pricing.flatMonthlyCost,
                  });
                  return;
                }
                applyCopilotPricingPatch({
                  model: "per_seat",
                  flatMonthlyCost: null,
                  costPerSeat: pricing.flatMonthlyCost ?? pricing.costPerSeat,
                });
              }}
            >
              {copilotModelOptions(isCopilotCreditPackage).map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>
              {isCopilotCreditPackage
                ? "Choose whether credits are allocated per user or per team"
                : "Per seat for Business-style plans; per team for flat-fee Enterprise deals"}
            </FormHelperText>
          </FormControl>

          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
            {copilotModel === "per_seat" ? (
              <TextField
                label={copilotCostLabel(copilotModel, isCopilotCreditPackage)}
                type="number"
                size="small"
                inputProps={{ min: 0, step: 0.01 }}
                value={pricing.costPerSeat ?? ""}
                onChange={(event) => {
                  const parsed =
                    event.target.value === "" ? null : Number(event.target.value);
                  applyCopilotPricingPatch({
                    model: "per_seat",
                    costPerSeat: Number.isNaN(parsed) ? null : parsed,
                  });
                }}
                disabled={disabled}
              />
            ) : (
              <TextField
                label={copilotCostLabel(copilotModel, isCopilotCreditPackage)}
                type="number"
                size="small"
                inputProps={{ min: 0, step: 0.01 }}
                value={pricing.flatMonthlyCost ?? ""}
                onChange={(event) => {
                  const parsed =
                    event.target.value === "" ? null : Number(event.target.value);
                  applyCopilotPricingPatch({
                    model: "per_team",
                    flatMonthlyCost: Number.isNaN(parsed) ? null : parsed,
                  });
                }}
                disabled={disabled}
              />
            )}
            <TextField
              label={copilotCountLabel(copilotModel, isCopilotCreditPackage)}
              type="number"
              size="small"
              inputProps={{ min: 1, step: 1 }}
              value={pricing.seatCount ?? ""}
              onChange={(event) => {
                const parsed =
                  event.target.value === "" ? null : Number(event.target.value);
                applyCopilotPricingPatch({
                  seatCount: Number.isNaN(parsed) ? null : parsed,
                });
              }}
              disabled={disabled}
              helperText={copilotCountHelper(
                copilotModel,
                teamMemberCount,
                isCopilotCreditPackage,
              )}
            />
          </Box>
          <TextField
            label="Configured subscription total (USD)"
            size="small"
            value={
              copilotConfiguredTotal(pricing) != null
                ? copilotConfiguredTotal(pricing)!.toFixed(2)
                : ""
            }
            disabled
            helperText={copilotTotalHelper(copilotModel, isCopilotCreditPackage)}
          />
        </Box>
      )}

      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1.5 }}>
        <TextField
          label="Subscription start"
          type="date"
          size="small"
          InputLabelProps={{ shrink: true }}
          value={binding.subscriptionStart ?? ""}
          onChange={(event) =>
            onChange({ subscriptionStart: event.target.value || null })
          }
          disabled={disabled}
        />
        {!isCopilot && !isFigma && (
          <TextField
            label="Subscription end"
            type="date"
            size="small"
            InputLabelProps={{ shrink: true }}
            value={binding.subscriptionEnd ?? ""}
            onChange={(event) =>
              onChange({ subscriptionEnd: event.target.value || null })
            }
            disabled={disabled}
          />
        )}
        <TextField
          label="Monthly budget (USD)"
          type="number"
          size="small"
          value={binding.monthlyBudget ?? ""}
          onChange={(event) =>
            onChange({
              monthlyBudget:
                event.target.value === "" ? null : Number(event.target.value),
            })
          }
          disabled={disabled}
        />
        <TextField
          label={isCopilot ? "Alert threshold (USD)" : "Alert threshold (%)"}
          type="number"
          size="small"
          inputProps={isCopilot ? { min: 0, step: 0.01 } : { min: 0, max: 100 }}
          value={
            isCopilot
              ? binding.alertThresholdUsd ?? ""
              : binding.alertThreshold ?? ""
          }
          onChange={(event) => {
            const parsed =
              event.target.value === "" ? null : Number(event.target.value);
            onChange(
              isCopilot
                ? { alertThresholdUsd: parsed }
                : { alertThreshold: parsed },
            );
          }}
          disabled={disabled}
        />
      </Box>
    </Box>
  );
}

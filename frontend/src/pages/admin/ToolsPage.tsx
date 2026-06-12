import { zodResolver } from "@hookform/resolvers/zod";
import {
  IconPencil,
  IconPlus,
  IconRefresh,
  IconTrash,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import {
  createTool,
  deleteTool,
  fetchTools,
  syncTool,
  updateTool,
  type AiTool,
  type PricingModel,
  type ToolPricing,
  type ToolProvider,
} from "@/api/tools";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { formatCost, formatRelativeTime, formatTokens } from "@/utils/formatters";

const PROVIDER_OPTIONS: Array<{ value: ToolProvider; label: string }> = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google" },
  { value: "azure_openai", label: "Azure OpenAI" },
  { value: "cohere", label: "Cohere" },
  { value: "mistral", label: "Mistral" },
  { value: "custom", label: "Custom" },
];

const PRICING_MODEL_OPTIONS: Array<{ value: PricingModel; label: string }> = [
  { value: "per_token", label: "Per token" },
  { value: "per_seat", label: "Per seat" },
  { value: "flat_fee", label: "Flat fee" },
  { value: "hybrid", label: "Hybrid" },
];

const PRICING_MODEL_CHIP_COLORS: Record<
  PricingModel,
  { background: string; color: string; label: string }
> = {
  per_token: { background: "#EFF6FF", color: "#2563EB", label: "Per token" },
  per_seat: { background: "#EDE9FE", color: "#7C3AED", label: "Per seat" },
  flat_fee: { background: "#ECFDF5", color: "#059669", label: "Flat fee" },
  hybrid: { background: "#FFF7ED", color: "#C2410C", label: "Hybrid" },
};

const providerValues = [
  "openai",
  "anthropic",
  "google",
  "azure_openai",
  "cohere",
  "mistral",
  "custom",
] as const;

function parseNullableNumber(value: unknown): number | null {
  if (value === "" || value == null) {
    return null;
  }
  return Number(value);
}

function parseNullableString(value: unknown): string | null {
  if (value === "" || value == null) {
    return null;
  }
  return String(value);
}

const nullableNumberField = z.preprocess(
  parseNullableNumber,
  z.number().min(0).nullable(),
);

const nullablePositiveIntField = z.preprocess(
  parseNullableNumber,
  z.number().int().positive().nullable(),
);

const nullableStringField = z.preprocess(
  parseNullableString,
  z.string().max(100).nullable(),
);

const pricingSchema = z.object({
  model: z.enum(["per_token", "per_seat", "flat_fee", "hybrid"]),
  inputCostPer1K: nullableNumberField,
  outputCostPer1K: nullableNumberField,
  costPerSeat: nullableNumberField,
  seatCount: nullablePositiveIntField,
  flatMonthlyCost: nullableNumberField,
  planName: nullableStringField,
  includedTokens: nullablePositiveIntField,
  overageRate: nullableNumberField,
});

const createSchema = z.object({
  name: z.string().min(1, "Name is required").max(80),
  provider: z.enum(providerValues),
  apiKey: z.string().min(1, "API key is required"),
  description: z.string().max(200).default(""),
  pricing: pricingSchema,
});

const editSchema = z.object({
  name: z.string().min(1, "Name is required").max(80),
  provider: z.enum(providerValues),
  apiKey: z.string().optional().or(z.literal("")),
  description: z.string().max(200).default(""),
  pricing: pricingSchema,
});

type CreateFormValues = z.infer<typeof createSchema>;
type EditFormValues = z.infer<typeof editSchema>;
type FormValues = CreateFormValues | EditFormValues;

function defaultPricing(): ToolPricing {
  return {
    model: "per_token",
    inputCostPer1K: null,
    outputCostPer1K: null,
    costPerSeat: null,
    seatCount: null,
    flatMonthlyCost: null,
    planName: null,
    includedTokens: null,
    overageRate: null,
  };
}

function defaultFormValues(): CreateFormValues {
  return {
    name: "",
    provider: "openai",
    apiKey: "",
    description: "",
    pricing: defaultPricing(),
  };
}

function formatProviderLabel(provider: ToolProvider): string {
  return provider
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatRate(value: number | null, decimals = 3): string {
  if (value == null) {
    return "0.000";
  }
  return value.toFixed(decimals);
}

function formatPricingSummary(pricing: ToolPricing): string {
  switch (pricing.model) {
    case "per_token":
      return `$${formatRate(pricing.inputCostPer1K)} in / $${formatRate(pricing.outputCostPer1K)} out per 1K`;
    case "per_seat":
      return `$${pricing.costPerSeat ?? 0} / seat · ${pricing.seatCount ?? 0} seats`;
    case "flat_fee":
      if (pricing.includedTokens != null) {
        return `$${pricing.flatMonthlyCost ?? 0}/mo · ${formatTokens(pricing.includedTokens)} included`;
      }
      return `$${pricing.flatMonthlyCost ?? 0}/mo`;
    case "hybrid":
      return `$${pricing.flatMonthlyCost ?? 0}/mo + $${formatRate(pricing.inputCostPer1K)} per 1K tokens`;
  }
}

function PricingModelChip({ model }: { model: PricingModel }) {
  const colors = PRICING_MODEL_CHIP_COLORS[model];
  return (
    <Chip
      size="small"
      label={colors.label}
      sx={{
        backgroundColor: colors.background,
        color: colors.color,
        fontWeight: 600,
        fontSize: "0.6875rem",
        "& .MuiChip-label": { px: 1 },
      }}
    />
  );
}

interface SlideOverState {
  open: boolean;
  tool: AiTool | null;
}

export function ToolsPage() {
  const queryClient = useQueryClient();
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    tool: null,
  });
  const [deleteTarget, setDeleteTarget] = useState<AiTool | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const toolsQuery = useQuery({
    queryKey: ["tools"],
    queryFn: fetchTools,
  });

  const createMutation = useMutation({
    mutationFn: createTool,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      setSlideOver({ open: false, tool: null });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: Parameters<typeof updateTool>[1];
    }) => updateTool(id, body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      setSlideOver({ open: false, tool: null });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTool,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      setDeleteTarget(null);
    },
  });

  const syncMutation = useMutation({
    mutationFn: syncTool,
    onMutate: (id) => {
      setSyncingId(id);
    },
    onSettled: () => {
      setSyncingId(null);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
    },
  });

  const isEditMode = slideOver.tool !== null;
  const savePending = createMutation.isPending || updateMutation.isPending;

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(isEditMode ? editSchema : createSchema),
    defaultValues: defaultFormValues(),
  });

  const pricingModel = watch("pricing.model");

  useEffect(() => {
    if (!slideOver.open) {
      reset(defaultFormValues());
      return;
    }

    if (slideOver.tool) {
      reset({
        name: slideOver.tool.name,
        provider: slideOver.tool.provider,
        apiKey: "",
        description: slideOver.tool.description,
        pricing: { ...slideOver.tool.pricing },
      });
      return;
    }

    reset(defaultFormValues());
  }, [reset, slideOver]);

  const columns: Column<AiTool>[] = useMemo(
    () => [
      {
        key: "name",
        header: "Tool",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.name}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {formatProviderLabel(row.provider)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => <StatusBadge status={row.status} />,
      },
      {
        key: "tokenCount",
        header: "Tokens used",
        sortable: true,
        align: "right",
        render: (row) => formatTokens(row.tokenCount),
      },
      {
        key: "pricing",
        header: "Pricing",
        render: (row) => (
          <Box>
            <PricingModelChip model={row.pricing.model} />
            <Typography
              variant="caption"
              sx={{ color: tokens.textMuted, display: "block", mt: 0.5 }}
            >
              {formatPricingSummary(row.pricing)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "costTotal",
        header: "Total cost",
        sortable: true,
        align: "right",
        render: (row) => formatCost(row.costTotal),
      },
      {
        key: "lastSyncAt",
        header: "Last synced",
        render: (row) =>
          row.lastSyncAt ? (
            formatRelativeTime(row.lastSyncAt)
          ) : (
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              Never
            </Typography>
          ),
      },
      {
        key: "actions",
        header: "",
        align: "right",
        render: (row) => (
          <Box sx={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <IconButton
              size="small"
              aria-label={`Sync ${row.name}`}
              onClick={(event) => {
                event.stopPropagation();
                syncMutation.mutate(row.id);
              }}
              disabled={syncingId === row.id}
            >
              {syncingId === row.id ? (
                <CircularProgress size={12} />
              ) : (
                <IconRefresh size={15} />
              )}
            </IconButton>
            <IconButton
              size="small"
              aria-label={`Edit ${row.name}`}
              onClick={(event) => {
                event.stopPropagation();
                setSlideOver({ open: true, tool: row });
              }}
            >
              <IconPencil size={15} />
            </IconButton>
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
        ),
      },
    ],
    [syncMutation, syncingId],
  );

  const onSubmit = (data: FormValues) => {
    const payload = {
      name: data.name,
      provider: data.provider,
      description: data.description,
      pricing: data.pricing as ToolPricing,
    };

    if (slideOver.tool) {
      const body: Parameters<typeof updateTool>[1] = { ...payload };
      if (data.apiKey) {
        body.apiKey = data.apiKey;
      }
      updateMutation.mutate({ id: slideOver.tool.id, body });
      return;
    }

    createMutation.mutate({
      ...payload,
      apiKey: data.apiKey ?? "",
    });
  };

  const showTokenRates =
    pricingModel === "per_token" || pricingModel === "hybrid";
  const showSeatFields = pricingModel === "per_seat";
  const showFlatFee = pricingModel === "flat_fee" || pricingModel === "hybrid";

  return (
    <RoleGuard
      roles={[Role.SuperAdmin]}
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to manage tools."
        />
      }
    >
      <Box>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            mb: 3,
          }}
        >
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              AI Tools
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Manage your connected AI provider integrations
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="small"
            startIcon={<IconPlus size={15} />}
            onClick={() => setSlideOver({ open: true, tool: null })}
          >
            Connect Tool
          </Button>
        </Box>

        {toolsQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load tools. Please refresh.
          </Alert>
        )}

        <DataTable
          columns={columns}
          rows={toolsQuery.data ?? []}
          rowKey={(row) => row.id}
          loading={toolsQuery.isPending}
          emptyTitle="No tools connected"
          emptyDescription="Connect your first AI provider to start tracking usage."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, tool: null })}
          title={isEditMode ? "Edit Tool" : "Connect Tool"}
          subtitle={
            isEditMode
              ? "Update tool configuration"
              : "Add an AI provider API key"
          }
          width={520}
          footer={
            <>
              <Button
                variant="text"
                onClick={() => setSlideOver({ open: false, tool: null })}
                disabled={savePending}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleSubmit(onSubmit)}
                disabled={savePending}
                startIcon={
                  savePending ? (
                    <CircularProgress size={14} color="inherit" />
                  ) : undefined
                }
              >
                Save
              </Button>
            </>
          }
        >
          <Box
            component="form"
            onSubmit={handleSubmit(onSubmit)}
            sx={{ display: "flex", flexDirection: "column", gap: 2 }}
          >
            <TextField
              {...register("name")}
              fullWidth
              label="Tool name"
              size="small"
              placeholder="Production OpenAI"
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
            />

            <Controller
              name="provider"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="tool-provider-label">Provider</InputLabel>
                  <Select
                    {...field}
                    labelId="tool-provider-label"
                    label="Provider"
                  >
                    {PROVIDER_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />

            <TextField
              {...register("apiKey")}
              fullWidth
              label="API Key"
              size="small"
              type="password"
              placeholder={
                isEditMode ? "Leave blank to keep existing key" : undefined
              }
              error={Boolean(errors.apiKey)}
              helperText={errors.apiKey?.message}
            />

            <TextField
              {...register("description")}
              fullWidth
              label="Description"
              size="small"
              multiline
              rows={2}
              placeholder="Brief description of this tool"
              error={Boolean(errors.description)}
              helperText={errors.description?.message}
            />

            <Typography
              variant="caption"
              sx={{
                color: tokens.textMuted,
                textTransform: "uppercase",
                mt: 1,
                mb: -1,
                display: "block",
              }}
            >
              Pricing configuration
            </Typography>

            <Controller
              name="pricing.model"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="tool-pricing-model-label">
                    Pricing model
                  </InputLabel>
                  <Select
                    {...field}
                    labelId="tool-pricing-model-label"
                    label="Pricing model"
                  >
                    {PRICING_MODEL_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />

            <Collapse in={showTokenRates}>
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 2,
                  mt: 2,
                }}
              >
                <TextField
                  {...register("pricing.inputCostPer1K", {
                    setValueAs: parseNullableNumber,
                  })}
                  fullWidth
                  label="Input cost ($/1K tokens)"
                  size="small"
                  type="number"
                  placeholder="0.005"
                  inputProps={{ step: "0.001" }}
                />
                <TextField
                  {...register("pricing.outputCostPer1K", {
                    setValueAs: parseNullableNumber,
                  })}
                  fullWidth
                  label="Output cost ($/1K tokens)"
                  size="small"
                  type="number"
                  placeholder="0.015"
                  inputProps={{ step: "0.001" }}
                />
              </Box>
            </Collapse>

            <Collapse in={showSeatFields}>
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 2,
                  mt: 2,
                }}
              >
                <TextField
                  {...register("pricing.costPerSeat", {
                    setValueAs: parseNullableNumber,
                  })}
                  fullWidth
                  label="Cost per seat ($/month)"
                  size="small"
                  type="number"
                  inputProps={{ step: "0.01" }}
                />
                <TextField
                  {...register("pricing.seatCount", {
                    setValueAs: parseNullableNumber,
                  })}
                  fullWidth
                  label="Number of seats"
                  size="small"
                  type="number"
                />
              </Box>
            </Collapse>

            <Collapse in={showFlatFee}>
              <Box sx={{ mt: 2 }}>
                <TextField
                  {...register("pricing.flatMonthlyCost", {
                    setValueAs: parseNullableNumber,
                  })}
                  fullWidth
                  label="Flat monthly cost (USD)"
                  size="small"
                  type="number"
                  inputProps={{ step: "0.01" }}
                />
              </Box>
            </Collapse>

            <TextField
              {...register("pricing.planName", {
                setValueAs: parseNullableString,
              })}
              fullWidth
              label="Plan / package name"
              size="small"
              placeholder="e.g. Team Pro, Pay-as-you-go"
            />

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 2,
              }}
            >
              <TextField
                {...register("pricing.includedTokens", {
                  setValueAs: parseNullableNumber,
                })}
                fullWidth
                label="Included tokens"
                size="small"
                type="number"
                placeholder="Leave blank if unlimited"
              />
              <TextField
                {...register("pricing.overageRate", {
                  setValueAs: parseNullableNumber,
                })}
                fullWidth
                label="Overage rate ($/1K tokens)"
                size="small"
                type="number"
                placeholder="Beyond included"
                inputProps={{ step: "0.001" }}
              />
            </Box>

            {!isEditMode && (
              <Alert severity="info" sx={{ mt: 1 }}>
                Pricing rates are used to calculate cost attribution. You can
                update these at any time.
              </Alert>
            )}
          </Box>
        </SlideOver>

        <ConfirmDialog
          open={deleteTarget !== null}
          title="Delete tool?"
          description={`"${deleteTarget?.name ?? ""}" will be disconnected and all its configuration removed. Usage history is preserved.`}
          dangerous
          confirmLabel="Delete"
          loading={deleteMutation.isPending}
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => {
            if (deleteTarget) {
              deleteMutation.mutate(deleteTarget.id);
            }
          }}
        />
      </Box>
    </RoleGuard>
  );
}

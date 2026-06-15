import { zodResolver } from "@hookform/resolvers/zod";
import {
  IconPencil,
  IconPlus,
  IconRefresh,
  IconTrash,
  IconUpload,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  FormControl,
  FormHelperText,
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

import { ApiClientError } from "@/api/client";
import {
  createTool,
  deleteTool,
  fetchTools,
  mergeSyncedToolIntoList,
  syncTool,
  isCsvImportedTool,
  updateTool,
  type AiTool,
  type CollectionSchedule,
  type PricingModel,
  type ToolPricing,
} from "@/api/tools";
import { fetchProviders, validateProviderToken, type Provider } from "@/api/providers";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { LIVE_DATA_POLL_MS } from "@/config/apiPolling";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { formatCost, formatRelativeTime, formatTokens } from "@/utils/formatters";
import { ToolCsvImportDialog } from "@/pages/admin/ToolCsvImportDialog";

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

const SCHEDULE_OPTIONS: Array<{ value: CollectionSchedule; label: string }> = [
  { value: "hourly", label: "Hourly" },
  { value: "daily", label: "Daily" },
];

const createSchema = z.object({
  name: z.string().min(1, "Name is required").max(80),
  provider: z.string().min(1, "Select a provider"),
  apiKey: z.string().min(1, "API key is required"),
  collectionSchedule: z.enum(["hourly", "daily"]),
  description: z.string().max(200).default(""),
  pricing: pricingSchema,
});

const editSchema = z.object({
  name: z.string().min(1, "Name is required").max(80),
  provider: z.string().min(1, "Select a provider"),
  apiKey: z.string().optional().or(z.literal("")),
  collectionSchedule: z.enum(["hourly", "daily"]),
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

function defaultFormValues(defaultProvider = "openai"): CreateFormValues {
  return {
    name: "",
    provider: defaultProvider,
    apiKey: "",
    collectionSchedule: "daily",
    description: "",
    pricing: defaultPricing(),
  };
}

function formatProviderLabel(
  slug: string,
  providerBySlug: Map<string, Provider>,
): string {
  return providerBySlug.get(slug)?.name ?? slug.replace(/_/g, " ");
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
  const [syncFeedback, setSyncFeedback] = useState<{
    toolId: string;
    severity: "success" | "error";
    message: string;
  } | null>(null);
  const [csvDialogOpen, setCsvDialogOpen] = useState(false);
  const [csvImportTarget, setCsvImportTarget] = useState<AiTool | null>(null);
  const [tokenValidated, setTokenValidated] = useState(false);
  const [validationMessage, setValidationMessage] = useState<{
    severity: "success" | "error";
    text: string;
  } | null>(null);

  const toolsQuery = useQuery({
    queryKey: ["tools"],
    queryFn: fetchTools,
    refetchInterval: syncingId ? false : LIVE_DATA_POLL_MS,
  });

  const providersQuery = useQuery({
    queryKey: ["providers", "active"],
    queryFn: () => fetchProviders({ active: true }),
    refetchInterval: LIVE_DATA_POLL_MS,
  });

  const providerBySlug = useMemo(() => {
    const map = new Map<string, Provider>();
    for (const provider of providersQuery.data ?? []) {
      map.set(provider.slug, provider);
    }
    return map;
  }, [providersQuery.data]);

  const connectProviderOptions = providersQuery.data ?? [];

  const createMutation = useMutation({
    mutationFn: createTool,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      await queryClient.invalidateQueries({ queryKey: ["insights"] });
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
      setSyncFeedback(null);
    },
    onSettled: () => {
      setSyncingId(null);
    },
    onSuccess: async (result) => {
      queryClient.setQueryData<AiTool[]>(["tools"], (current) =>
        mergeSyncedToolIntoList(current ?? [], result.tool),
      );
      setSyncFeedback({
        toolId: result.tool.id,
        severity: "success",
        message: result.message,
      });
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      await queryClient.invalidateQueries({ queryKey: ["insights"] });
    },
    onError: (error: Error, toolId) => {
      const message =
        error instanceof ApiClientError
          ? error.apiError.detail
          : error.message || "Live usage sync failed.";
      setSyncFeedback({
        toolId,
        severity: "error",
        message,
      });
      void queryClient.invalidateQueries({ queryKey: ["tools"] });
    },
  });

  const validateMutation = useMutation({
    mutationFn: ({
      providerSlug,
      apiToken,
    }: {
      providerSlug: string;
      apiToken: string;
    }) => validateProviderToken(providerSlug, apiToken),
    onSuccess: (result) => {
      setTokenValidated(result.valid);
      setValidationMessage({
        severity: result.valid ? "success" : "error",
        text: result.message,
      });
    },
    onError: (error: Error) => {
      setTokenValidated(false);
      setValidationMessage({
        severity: "error",
        text: error.message || "Could not validate API key.",
      });
    },
  });

  const isEditMode = slideOver.tool !== null;
  const csvImportedEdit =
    isEditMode && slideOver.tool !== null && isCsvImportedTool(slideOver.tool);
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
  const selectedProvider = watch("provider");
  const apiKeyValue = watch("apiKey");

  useEffect(() => {
    setTokenValidated(false);
    setValidationMessage(null);
  }, [selectedProvider, apiKeyValue]);

  useEffect(() => {
    if (!slideOver.open) {
      const defaultProvider =
        connectProviderOptions[0]?.slug ?? "openai";
      reset(defaultFormValues(defaultProvider));
      setTokenValidated(false);
      setValidationMessage(null);
      return;
    }

    if (slideOver.tool) {
      reset({
        name: slideOver.tool.name,
        provider: slideOver.tool.provider,
        apiKey: "",
        collectionSchedule: slideOver.tool.collectionSchedule,
        description: slideOver.tool.description,
        pricing: { ...slideOver.tool.pricing },
      });
      setTokenValidated(true);
      setValidationMessage(null);
      return;
    }

    const defaultProvider = connectProviderOptions[0]?.slug ?? "openai";
    reset(defaultFormValues(defaultProvider));
    setTokenValidated(false);
    setValidationMessage(null);
  }, [reset, slideOver, connectProviderOptions]);

  const columns: Column<AiTool>[] = useMemo(
    () => [
      {
        key: "name",
        header: "Team",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.name}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {formatProviderLabel(row.provider, providerBySlug)}
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
        header: "Last updated",
        render: (row) => {
          const timestamp = isCsvImportedTool(row)
            ? row.lastCsvImportAt
            : row.lastSyncAt;
          return timestamp ? (
            formatRelativeTime(timestamp)
          ) : (
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              Never
            </Typography>
          );
        },
      },
      {
        key: "collectionSchedule",
        header: "Data source",
        render: (row) =>
          isCsvImportedTool(row) ? (
            <Chip
              size="small"
              variant="outlined"
              label="CSV import"
              sx={{ fontSize: "0.6875rem", height: 20 }}
            />
          ) : (
            <Chip
              size="small"
              variant="outlined"
              label={row.collectionSchedule === "hourly" ? "Hourly pull" : "Daily pull"}
              sx={{ fontSize: "0.6875rem", height: 20 }}
            />
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
              aria-label={`Import CSV for ${row.name}`}
              title="Import usage from CSV"
              onClick={(event) => {
                event.stopPropagation();
                setCsvImportTarget(row);
                setCsvDialogOpen(true);
              }}
            >
              <IconUpload size={15} />
            </IconButton>
            {!isCsvImportedTool(row) && (
              <IconButton
                size="small"
                aria-label={`Pull live usage for ${row.name}`}
                title="Pull live usage from provider"
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
            )}
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
    [providerBySlug, syncMutation, syncingId],
  );

  const onSubmit = (data: FormValues) => {
    const needsValidation =
      !csvImportedEdit &&
      (!isEditMode || Boolean(data.apiKey && data.apiKey.trim().length > 0));
    if (needsValidation && !tokenValidated) {
      setValidationMessage({
        severity: "error",
        text: "Test the connection before saving.",
      });
      return;
    }

    const payload = {
      name: data.name,
      provider: data.provider,
      description: data.description,
      pricing: data.pricing as ToolPricing,
      collectionSchedule: data.collectionSchedule,
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

  const handleTestConnection = () => {
    const provider = selectedProvider;
    const apiKey = apiKeyValue?.trim();
    if (!provider) {
      setValidationMessage({
        severity: "error",
        text: "Select a provider first.",
      });
      return;
    }
    if (!apiKey) {
      setValidationMessage({
        severity: "error",
        text: "Enter an API key to test the connection.",
      });
      return;
    }
    validateMutation.mutate({ providerSlug: provider, apiToken: apiKey });
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
          description="You don't have permission to manage teams."
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
              Teams
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Connect provider API keys and track usage per team
            </Typography>
          </Box>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<IconUpload size={15} />}
              onClick={() => {
                setCsvImportTarget(null);
                setCsvDialogOpen(true);
              }}
            >
              Import CSV
            </Button>
            <Button
              variant="contained"
              size="small"
              startIcon={<IconPlus size={15} />}
              onClick={() => setSlideOver({ open: true, tool: null })}
            >
              Connect Team
            </Button>
          </Box>
        </Box>

        {toolsQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load teams. Please refresh.
          </Alert>
        )}

        {syncFeedback && (
          <Alert
            severity={syncFeedback.severity}
            sx={{ mb: 2 }}
            onClose={() => setSyncFeedback(null)}
          >
            {syncFeedback.message}
          </Alert>
        )}

        <ToolCsvImportDialog
          open={csvDialogOpen}
          onClose={() => {
            setCsvDialogOpen(false);
            setCsvImportTarget(null);
          }}
          providers={connectProviderOptions}
          tools={toolsQuery.data ?? []}
          initialTool={csvImportTarget}
          onSuccess={async (message) => {
            setSyncFeedback({
              toolId: csvImportTarget?.id ?? "",
              severity: "success",
              message,
            });
            await queryClient.invalidateQueries({ queryKey: ["tools"] });
            await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
            await queryClient.invalidateQueries({ queryKey: ["insights"] });
          }}
        />

        <DataTable
          columns={columns}
          rows={toolsQuery.data ?? []}
          rowKey={(row) => row.id}
          loading={toolsQuery.isPending}
          emptyTitle="No teams connected"
          emptyDescription="Connect your first team API key to start tracking usage."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, tool: null })}
          title={isEditMode ? "Edit Team" : "Connect Team"}
          subtitle={
            isEditMode
              ? "Update team configuration"
              : "Add a provider API key for a team"
          }
          width={520}
          footer={
            <>
              <Button
                variant="text"
                onClick={() => setSlideOver({ open: false, tool: null })}
                disabled={savePending || validateMutation.isPending}
              >
                Cancel
              </Button>
              {!csvImportedEdit && (
                <Button
                  variant="outlined"
                  onClick={handleTestConnection}
                  disabled={validateMutation.isPending || savePending}
                  startIcon={
                    validateMutation.isPending ? (
                      <CircularProgress size={14} color="inherit" />
                    ) : undefined
                  }
                >
                  Test connection
                </Button>
              )}
              <Button
                variant="contained"
                onClick={handleSubmit(onSubmit)}
                disabled={savePending || validateMutation.isPending}
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
          {createMutation.isPending && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Saving and pulling live usage from the provider…
            </Alert>
          )}
          <Box
            component="form"
            onSubmit={handleSubmit(onSubmit)}
            sx={{ display: "flex", flexDirection: "column", gap: 2 }}
          >
            <TextField
              {...register("name")}
              fullWidth
              label="Team name"
              size="small"
              placeholder="Production OpenAI"
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
            />

            <Controller
              name="provider"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small" error={Boolean(errors.provider)}>
                  <InputLabel id="tool-provider-label">Provider</InputLabel>
                  <Select
                    {...field}
                    labelId="tool-provider-label"
                    label="Provider"
                    disabled={providersQuery.isPending}
                  >
                    {connectProviderOptions.map((option) => (
                      <MenuItem key={option.slug} value={option.slug}>
                        {option.name}
                      </MenuItem>
                    ))}
                  </Select>
                  {errors.provider?.message && (
                    <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                      {errors.provider.message}
                    </Typography>
                  )}
                  {selectedProvider && providerBySlug.get(selectedProvider) && (
                    <Typography
                      variant="caption"
                      sx={{ color: tokens.textMuted, mt: 0.5, display: "block" }}
                    >
                      Usage API:{" "}
                      {providerBySlug.get(selectedProvider)?.usageApiUrl}
                    </Typography>
                  )}
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
              sx={{ display: csvImportedEdit ? "none" : undefined }}
            />

            {csvImportedEdit && (
              <Alert severity="info">
                Usage for this team comes from CSV imports. Use Import CSV on the
                teams table to update metrics — no API pull is required.
              </Alert>
            )}

            {validationMessage && !csvImportedEdit && (
              <Alert severity={validationMessage.severity}>
                {validationMessage.text}
              </Alert>
            )}

            {!csvImportedEdit && (
              <Controller
                name="collectionSchedule"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth size="small">
                    <InputLabel id="tool-schedule-label">Usage pull schedule</InputLabel>
                    <Select
                      {...field}
                      labelId="tool-schedule-label"
                      label="Usage pull schedule"
                    >
                      {SCHEDULE_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      How often usage data will be collected from the provider
                    </FormHelperText>
                  </FormControl>
                )}
              />
            )}

            <TextField
              {...register("description")}
              fullWidth
              label="Description"
              size="small"
              multiline
              rows={2}
              placeholder="Brief description of this team"
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
          title="Delete team?"
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

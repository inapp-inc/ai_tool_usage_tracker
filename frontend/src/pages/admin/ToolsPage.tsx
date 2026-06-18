import { zodResolver } from "@hookform/resolvers/zod";
import { IconPencil, IconPlus, IconTrash } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
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
  normalizePricing,
  updateTool,
  type AiTool,
  type ToolProvider,
} from "@/api/tools";
import {
  BUILT_IN_PROVIDER_PARENTS,
  fetchProviderParents,
  providerRequiresOrganizationId,
  type ProviderParent,
} from "@/api/providers";
import { ApiClientError } from "@/api/client";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { ToolUsagePollingForm, type ToolFormWithPolling } from "@/components/tools/ToolUsagePollingForm";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { useToast } from "@/hooks/useToast";
import {
  defaultUsagePollingFormValues,
  formValuesToIntegrationConfig,
  integrationConfigToFormValues,
} from "@/types/integrationConfig";

const toolFormSchema = z
  .object({
    name: z.string().min(1, "Name is required").max(80),
    parentProvider: z.string().min(1, "Provider is required"),
    provider: z.string().min(1),
    description: z.string().max(200),
    apiEndpoint: z
      .string()
      .max(512)
      .optional()
      .refine(
        (val) => !val || val.startsWith("https://"),
        "API Endpoint URL must start with https://",
      ),
    organizationId: z.string().max(100).optional(),
    enabled: z.boolean(),
    authType: z.enum(["bearer", "api_key_header"]),
    authHeader: z.string().min(1, "Auth header is required"),
    authPrefix: z.string(),
    method: z.enum(["GET", "POST"]),
    usageUrl: z.string(),
    querySinceName: z.string(),
    querySinceValue: z.string(),
    queryUntilName: z.string(),
    queryUntilValue: z.string(),
    extraHeadersJson: z.string(),
    responseType: z.enum(["json_array", "json_object"]),
    recordsPath: z.string(),
    fieldEventId: z.string(),
    fieldOccurredAt: z.string(),
    fieldInputTokens: z.string(),
    fieldOutputTokens: z.string(),
    fieldCost: z.string(),
    fieldModel: z.string(),
    fieldUserEmail: z.string(),
    fieldUserName: z.string(),
  })
  .superRefine((data, ctx) => {
    if (data.provider === "custom" && !data.parentProvider?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Select the vendor / platform company for this tool",
        path: ["parentProvider"],
      });
    }
    if (data.provider === "copilot" && !data.organizationId?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "GitHub organization ID is required for Microsoft Copilot",
        path: ["organizationId"],
      });
    }
    if (data.provider !== "custom" || !data.enabled) {
      return;
    }
    if (!data.apiEndpoint?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "API Endpoint URL is required when usage polling is enabled",
        path: ["apiEndpoint"],
      });
    } else if (!data.apiEndpoint.trim().startsWith("https://")) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "API Endpoint URL must start with https://",
        path: ["apiEndpoint"],
      });
    }
    if (!data.usageUrl.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Usage URL is required when polling is enabled",
        path: ["usageUrl"],
      });
    }
    if (!data.fieldEventId.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Event ID mapping is required",
        path: ["fieldEventId"],
      });
    }
    if (!data.fieldOccurredAt.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Occurred at mapping is required",
        path: ["fieldOccurredAt"],
      });
    }
    if (!data.fieldInputTokens.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Input tokens mapping is required",
        path: ["fieldInputTokens"],
      });
    }
  });

type FormValues = ToolFormWithPolling;

function defaultFormValues(): FormValues {
  return {
    name: "",
    parentProvider: "",
    provider: "custom",
    description: "",
    apiEndpoint: "",
    organizationId: "",
    ...defaultUsagePollingFormValues(),
  };
}

function displayToolName(row: AiTool): string {
  return row.productLabel ?? row.name;
}

interface SlideOverState {
  open: boolean;
  tool: AiTool | null;
}

function getApiErrorMessage(error: unknown): string {  if (error instanceof ApiClientError) {
    return error.apiError.detail;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

export function ToolsPage() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    tool: null,
  });
  const [deleteTarget, setDeleteTarget] = useState<AiTool | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const toolsQuery = useQuery({
    queryKey: ["tools"],
    queryFn: () => fetchTools({ catalogueOnly: true }),
  });

  const providersQuery = useQuery({
    queryKey: ["settings", "provider-parents"],
    queryFn: () => fetchProviderParents(),
    staleTime: 5 * 60 * 1000,
  });

  const providerParents =
    providersQuery.data && providersQuery.data.length > 0
      ? providersQuery.data
      : BUILT_IN_PROVIDER_PARENTS;

  const createMutation = useMutation({
    mutationFn: createTool,
    onSuccess: async () => {
      showToast("Tool added successfully.", "success");
      setSaveError(null);
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      setSlideOver({ open: false, tool: null });
    },
    onError: (error) => {
      const message = getApiErrorMessage(error);
      setSaveError(message);
      showToast(message, "error");
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
      showToast("Tool updated successfully.", "success");
      setSaveError(null);
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      setSlideOver({ open: false, tool: null });
    },
    onError: (error) => {
      const message = getApiErrorMessage(error);
      setSaveError(message);
      showToast(message, "error");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTool,
    onSuccess: async () => {
      showToast("Tool deleted.", "success");
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      setDeleteTarget(null);
    },
    onError: (error) => {
      showToast(getApiErrorMessage(error), "error");
    },
  });

  const isEditMode = slideOver.tool !== null;
  const editingBuiltIn = Boolean(slideOver.tool?.builtIn);
  const editingCustom = isEditMode && !editingBuiltIn;
  const isAddCustom = !isEditMode;
  const showParentProviderField = isAddCustom || editingCustom;
  const savePending = createMutation.isPending || updateMutation.isPending;

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(toolFormSchema),
    defaultValues: defaultFormValues(),
  });

  const pollingEnabled = watch("enabled");
  const productSlug = watch("provider");
  const isCustomProvider = productSlug === "custom";
  const isCopilotProvider = productSlug === "copilot";
  const showApiEndpoint = isCustomProvider && !isCopilotProvider && pollingEnabled;
  const showOrganizationId = providerRequiresOrganizationId(productSlug);
  const showUsagePolling = isCustomProvider;

  useEffect(() => {
    if (!slideOver.open) {
      reset(defaultFormValues());
      setSaveError(null);
      return;
    }

    if (slideOver.tool) {
      reset({
        name: slideOver.tool.builtIn
          ? (slideOver.tool.productLabel ?? slideOver.tool.name)
          : slideOver.tool.name,
        parentProvider:
          slideOver.tool.parentSlug ?? slideOver.tool.pricing.parentSlug ?? "",
        provider: slideOver.tool.provider,
        description: slideOver.tool.description,
        apiEndpoint: slideOver.tool.apiEndpoint ?? "",
        organizationId: slideOver.tool.pricing.organizationId ?? "",
        ...integrationConfigToFormValues(slideOver.tool.integrationConfig),
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
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {displayToolName(row)}
            </Typography>
            {row.builtIn && (
              <Chip label="Built-in" size="small" variant="outlined" sx={{ height: 20 }} />
            )}
          </Box>
        ),
      },
      {
        key: "provider",
        header: "Provider",
        sortable: true,
        render: (row) => (
          <Typography variant="body2">{row.parentLabel ?? "—"}</Typography>
        ),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => <StatusBadge status={row.status} />,
      },
      {
        key: "actions",
        header: "",
        align: "right",
        render: (row) => (
          <Box sx={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
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
            {!row.builtIn && (
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
            )}
          </Box>
        ),
      },
    ],
    [providerParents],
  );
  const onSubmit = (data: FormValues) => {
    setSaveError(null);

    if (providerRequiresOrganizationId(data.provider) && !data.organizationId?.trim()) {
      setSaveError("GitHub organization ID is required for Microsoft Copilot.");
      return;
    }

    if (data.provider === "custom" && !data.parentProvider?.trim()) {
      setSaveError("Select the vendor / platform company for this tool.");
      return;
    }

    const integrationConfig =
      data.provider === "custom" ? formValuesToIntegrationConfig(data) : null;

    const formBody = {
      name: editingBuiltIn ? slideOver.tool!.name : data.name,
      provider: (editingBuiltIn ? data.provider : "custom") as ToolProvider,
      description: data.description,
      apiEndpoint: data.apiEndpoint?.trim() || null,
      integrationConfig,
      pricing: normalizePricing({
        model: "per_token",
        inputCostPer1K: null,
        outputCostPer1K: null,
        costPerSeat: null,
        seatCount: null,
        flatMonthlyCost: null,
        planName: null,
        includedTokens: null,
        overageRate: null,
        organizationId: data.organizationId?.trim() || null,
        parentSlug: data.parentProvider?.trim() || null,
      }),
    };

    if (slideOver.tool) {
      updateMutation.mutate({
        id: slideOver.tool.id,
        body: formBody,
      });
      return;
    }

    createMutation.mutate(formBody);
  };

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
              Built-in AI tools are provisioned automatically. Add custom integrations or connect credentials.
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="small"
            startIcon={<IconPlus size={15} />}
            onClick={() => setSlideOver({ open: true, tool: null })}
          >
            Add Custom Tool
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
          emptyTitle="No tools available"
          emptyDescription="Built-in tools appear after the backend seeds your organization catalogue."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, tool: null })}
          title={isEditMode ? "Edit Tool" : "Add Custom Tool"}
          subtitle={
            isEditMode
              ? editingBuiltIn
                ? "Built-in tool — update optional settings"
                : "Update tool configuration"
              : "Register a custom HTTP integration"
          }
          width={560}
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
            {saveError && (
              <Alert severity="error" onClose={() => setSaveError(null)}>
                {saveError}
              </Alert>
            )}

            {showParentProviderField && (
              <Controller
                name="parentProvider"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth size="small" error={Boolean(errors.parentProvider)}>
                    <InputLabel id="tool-parent-provider-label">Provider</InputLabel>
                    <Select
                      {...field}
                      labelId="tool-parent-provider-label"
                      label="Provider"
                    >
                      {providerParents.map((parent: ProviderParent) => (
                        <MenuItem key={parent.slug} value={parent.slug}>
                          {parent.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />
            )}

            {editingBuiltIn && slideOver.tool && (
              <>
                <TextField
                  fullWidth
                  label="Provider"
                  size="small"
                  value={slideOver.tool.parentLabel ?? ""}
                  disabled
                />
                <TextField
                  fullWidth
                  label="Tool"
                  size="small"
                  value={slideOver.tool.productLabel ?? slideOver.tool.name}
                  disabled
                />
              </>
            )}

            {!editingBuiltIn && (
              <TextField
                {...register("name")}
                fullWidth
                label="Tool name"
                size="small"
                placeholder="Internal LLM Gateway"
                error={Boolean(errors.name)}
                helperText={errors.name?.message}
              />
            )}

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

            {showOrganizationId && (
              <TextField
                {...register("organizationId")}
                fullWidth
                label="GitHub organization ID"
                size="small"
                placeholder="my-company"
                error={Boolean(errors.organizationId)}
                helperText={
                  errors.organizationId?.message ??
                  "Your GitHub organization login — used in the Copilot API URL (e.g. api.github.com/orgs/my-company/...)."
                }
              />
            )}

            {showApiEndpoint && (
              <TextField
                {...register("apiEndpoint")}
                fullWidth
                label="API Endpoint URL"
                size="small"
                placeholder="https://api.example.com/v1/chat/completions"
                error={Boolean(errors.apiEndpoint)}
                helperText={
                  errors.apiEndpoint?.message ??
                  (isCustomProvider && pollingEnabled
                    ? "Required when usage polling is enabled — HTTPS URL your usage API expects."
                    : "HTTPS base URL for this provider's API.")
                }
              />
            )}

            {showUsagePolling && (
              <ToolUsagePollingForm
                control={control}
                errors={errors}
                enabled={pollingEnabled}
              />
            )}

          </Box>
        </SlideOver>

        <ConfirmDialog          open={deleteTarget !== null}
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

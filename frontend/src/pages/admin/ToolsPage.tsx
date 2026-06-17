import { zodResolver } from "@hookform/resolvers/zod";
import { IconPencil, IconPlus, IconTrash } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
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
import { BUILT_IN_PROVIDERS, fetchProviders, providerRequiresApiEndpoint, type Provider } from "@/api/providers";
import { ApiClientError } from "@/api/client";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { useToast } from "@/hooks/useToast";
/** Static fallback — used when GET /settings/providers is unavailable. */
const FALLBACK_PROVIDER_OPTIONS = BUILT_IN_PROVIDERS.map((p) => ({
  value: p.slug as ToolProvider,
  label: p.label,
}));

const toolFormSchema = z.object({
  name: z.string().min(1, "Name is required").max(80),
  provider: z.string().min(1, "Provider is required"),
  description: z.string().max(200),
  apiEndpoint: z
    .string()
    .max(512)
    .optional()
    .refine(
      (val) => !val || val.startsWith("https://"),
      "API Endpoint URL must start with https://",
    ),
});

type FormValues = z.infer<typeof toolFormSchema>;

function defaultFormValues(): FormValues {
  return {
    name: "",
    provider: "openai",
    description: "",
    apiEndpoint: "",
  };
}

function formatProviderLabel(provider: ToolProvider): string {
  return provider
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function resolveProviderLabel(
  slug: string,
  options: Array<{ value: string; label: string }>,
): string {
  const match = options.find((option) => option.value === slug);
  return match?.label ?? formatProviderLabel(slug as ToolProvider);
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
    queryKey: ["settings", "providers"],
    queryFn: () => fetchProviders(true),
    staleTime: 5 * 60 * 1000,
  });

  const providerOptions =
    providersQuery.data && providersQuery.data.length > 0
      ? providersQuery.data.map((p: Provider) => ({ value: p.slug, label: p.label }))
      : FALLBACK_PROVIDER_OPTIONS;

  const allProviders = providersQuery.data ?? BUILT_IN_PROVIDERS;

  const createMutation = useMutation({    mutationFn: createTool,
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

  const isEditMode = slideOver.tool !== null;  const savePending = createMutation.isPending || updateMutation.isPending;

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

  const selectedProvider = watch("provider");
  const apiEndpointRequired = providerRequiresApiEndpoint(
    selectedProvider,
    allProviders,
  );

  useEffect(() => {
    if (!slideOver.open) {
      reset(defaultFormValues());
      setSaveError(null);
      return;
    }

    if (slideOver.tool) {
      reset({
        name: slideOver.tool.name,
        provider: slideOver.tool.provider,
        description: slideOver.tool.description,
        apiEndpoint: slideOver.tool.apiEndpoint ?? "",
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
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {row.name}
          </Typography>
        ),
      },
      {
        key: "provider",
        header: "Provider",
        sortable: true,
        render: (row) => (
          <Typography variant="body2">
            {resolveProviderLabel(row.provider, providerOptions)}
          </Typography>
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
    [providerOptions],
  );
  const onSubmit = (data: FormValues) => {
    setSaveError(null);

    if (
      providerRequiresApiEndpoint(data.provider, allProviders) &&
      !data.apiEndpoint?.trim()
    ) {
      setSaveError("API Endpoint URL is required for this provider.");
      return;
    }

    const formBody = {
      name: data.name,
      provider: data.provider as ToolProvider,
      description: data.description,
      apiEndpoint: data.apiEndpoint?.trim() || null,
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
              Manage your connected AI provider integrations
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="small"
            startIcon={<IconPlus size={15} />}
            onClick={() => setSlideOver({ open: true, tool: null })}
          >
            Add Tool
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
          emptyTitle="No tools added"
          emptyDescription="Register AI tools your organization uses. Connect API keys separately under Credentials."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, tool: null })}
          title={isEditMode ? "Edit Tool" : "Add Tool"}
          subtitle={
            isEditMode
              ? "Update tool configuration"
              : "Register an AI provider tool"
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
            {saveError && (
              <Alert severity="error" onClose={() => setSaveError(null)}>
                {saveError}
              </Alert>
            )}

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
                <FormControl fullWidth size="small" error={Boolean(errors.provider)}>
                  <InputLabel id="tool-provider-label">Provider</InputLabel>
                  <Select
                    {...field}
                    labelId="tool-provider-label"
                    label="Provider"
                  >
                    {providerOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
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

            <TextField
              {...register("apiEndpoint")}
              fullWidth
              label="API Endpoint URL"
              size="small"
              placeholder="https://api.example.com/v1/chat/completions"
              error={Boolean(errors.apiEndpoint)}
              helperText={
                errors.apiEndpoint?.message ??
                (apiEndpointRequired
                  ? "Required — GET endpoint used to validate the API key (Bearer auth)."
                  : "Optional. Override the provider default base URL if needed.")
              }
            />

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

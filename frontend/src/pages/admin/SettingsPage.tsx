import { zodResolver } from "@hookform/resolvers/zod";
import { IconPencil, IconPlus, IconTrash } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  IconButton,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { ApiClientError } from "@/api/client";
import {
  BUILT_IN_PROVIDERS,
  createProvider,
  deleteProvider,
  fetchProviders,
  updateProvider,
  type Provider,
} from "@/api/providers";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { useToast } from "@/hooks/useToast";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";

const createSchema = z.object({
  slug: z
    .string()
    .min(1, "Slug is required")
    .max(64)
    .regex(/^[a-z0-9_]+$/, "Use lowercase letters, numbers, and underscores only"),
  label: z.string().min(1, "Label is required").max(200),
  description: z.string().max(500).default(""),
});

const editSchema = z.object({
  label: z.string().min(1, "Label is required").max(200),
  description: z.string().max(500).default(""),
  active: z.boolean(),
});

type CreateFormValues = z.infer<typeof createSchema>;
type EditFormValues = z.infer<typeof editSchema>;

interface SlideOverState {
  open: boolean;
  provider: Provider | null;
}

function defaultCreateValues(): CreateFormValues {
  return { slug: "", label: "", description: "" };
}

function providerToEditValues(provider: Provider): EditFormValues {
  return {
    label: provider.label,
    description: provider.description ?? "",
    active: provider.active,
  };
}

function getApiErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.apiError.detail;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    provider: null,
  });
  const [deleteTarget, setDeleteTarget] = useState<Provider | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const providersQuery = useQuery({
    queryKey: ["settings", "providers", "all"],
    queryFn: () => fetchProviders(false),
  });

  const isEditMode = slideOver.provider !== null;
  const activeSchema = isEditMode ? editSchema : createSchema;

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateFormValues | EditFormValues>({
    resolver: zodResolver(activeSchema),
    defaultValues: defaultCreateValues(),
  });

  useEffect(() => {
    if (!slideOver.open) {
      reset(defaultCreateValues());
      setSaveError(null);
      return;
    }
    if (slideOver.provider) {
      reset(providerToEditValues(slideOver.provider));
      return;
    }
    reset(defaultCreateValues());
  }, [reset, slideOver]);

  const createMutation = useMutation({
    mutationFn: createProvider,
    onSuccess: async () => {
      showToast("Provider added.", "success");
      setSaveError(null);
      await queryClient.invalidateQueries({ queryKey: ["settings", "providers"] });
      setSlideOver({ open: false, provider: null });
    },
    onError: (error) => {
      const message = getApiErrorMessage(error);
      setSaveError(message);
      showToast(message, "error");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ slug, body }: { slug: string; body: EditFormValues }) =>
      updateProvider(slug, body),
    onSuccess: async () => {
      showToast("Provider updated.", "success");
      setSaveError(null);
      await queryClient.invalidateQueries({ queryKey: ["settings", "providers"] });
      setSlideOver({ open: false, provider: null });
    },
    onError: (error) => {
      const message = getApiErrorMessage(error);
      setSaveError(message);
      showToast(message, "error");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProvider,
    onSuccess: async () => {
      showToast("Provider deleted.", "success");
      await queryClient.invalidateQueries({ queryKey: ["settings", "providers"] });
      setDeleteTarget(null);
    },
    onError: (error) => {
      showToast(getApiErrorMessage(error), "error");
    },
  });

  const savePending = createMutation.isPending || updateMutation.isPending;
  const rows = providersQuery.data ?? BUILT_IN_PROVIDERS;

  const columns: Column<Provider>[] = useMemo(
    () => [
      {
        key: "label",
        header: "Provider",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.label}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted, fontFamily: "monospace" }}>
              {row.slug}
            </Typography>
          </Box>
        ),
      },
      {
        key: "active",
        header: "Active",
        render: (row) => (
          <Chip
            size="small"
            label={row.active ? "Active" : "Inactive"}
            sx={{
              backgroundColor: row.active ? "#ECFDF5" : "#F1F5F9",
              color: row.active ? "#059669" : tokens.textMuted,
              fontWeight: 500,
              fontSize: "0.6875rem",
              height: 22,
            }}
          />
        ),
      },
      {
        key: "built_in",
        header: "Type",
        render: (row) => (
          <Typography variant="body2" sx={{ color: tokens.textMuted }}>
            {row.built_in ? "Built-in" : "Custom"}
          </Typography>
        ),
      },
      {
        key: "actions",
        header: "",
        align: "right",
        render: (row) => (
          <Box sx={{ display: "inline-flex", gap: "4px" }}>
            <IconButton
              size="small"
              aria-label={`Edit ${row.label}`}
              onClick={(event) => {
                event.stopPropagation();
                setSlideOver({ open: true, provider: row });
              }}
            >
              <IconPencil size={15} />
            </IconButton>
            <IconButton
              size="small"
              aria-label={`Delete ${row.label}`}
              disabled={row.built_in}
              onClick={(event) => {
                event.stopPropagation();
                setDeleteTarget(row);
              }}
              sx={{ color: row.built_in ? tokens.textMuted : tokens.critical }}
            >
              <IconTrash size={15} />
            </IconButton>
          </Box>
        ),
      },
    ],
    [],
  );

  const onSubmit = (data: CreateFormValues | EditFormValues) => {
    setSaveError(null);
    if (slideOver.provider) {
      updateMutation.mutate({
        slug: slideOver.provider.slug,
        body: data as EditFormValues,
      });
      return;
    }
    createMutation.mutate(data as CreateFormValues);
  };

  return (
    <RoleGuard
      roles={[Role.SuperAdmin]}
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to manage settings."
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
              Settings
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Manage AI provider lookup keys used when adding tools
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="small"
            startIcon={<IconPlus size={15} />}
            onClick={() => setSlideOver({ open: true, provider: null })}
          >
            Add Provider
          </Button>
        </Box>

        {providersQuery.isError && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            Could not load providers from the server. Showing built-in fallback list.
          </Alert>
        )}

        <Alert severity="info" sx={{ mb: 2 }}>
          Custom providers use the generic HTTP adapter. When adding a tool for a custom provider,
          set the API Endpoint URL to a GET endpoint that accepts Bearer auth (returns non-401 when
          the key is valid).
        </Alert>

        <DataTable
          columns={columns}
          rows={rows}
          rowKey={(row) => row.slug}
          loading={providersQuery.isPending}
          emptyTitle="No providers"
          emptyDescription="Add a provider to use it in the Tools catalogue."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, provider: null })}
          title={isEditMode ? "Edit Provider" : "Add Provider"}
          subtitle={
            isEditMode
              ? "Update display name and availability"
              : "Create a provider slug for dynamic tool registration"
          }
          width={480}
          footer={
            <>
              <Button
                variant="text"
                onClick={() => setSlideOver({ open: false, provider: null })}
                disabled={savePending}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleSubmit(onSubmit)}
                disabled={savePending}
                startIcon={
                  savePending ? <CircularProgress size={14} color="inherit" /> : undefined
                }
              >
                {isEditMode ? "Save" : "Add Provider"}
              </Button>
            </>
          }
        >
          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            {saveError && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setSaveError(null)}>
                {saveError}
              </Alert>
            )}

            {!isEditMode && (
              <TextField
                {...register("slug" as keyof CreateFormValues)}
                fullWidth
                label="Slug"
                size="small"
                placeholder="my_internal_llm"
                error={Boolean((errors as Partial<Record<keyof CreateFormValues, { message?: string }>>).slug)}
                helperText={
                  (errors as Partial<Record<keyof CreateFormValues, { message?: string }>>).slug
                    ?.message ?? "Lowercase identifier used in tools and credentials"
                }
                sx={{ mb: 2 }}
              />
            )}

            <TextField
              {...register("label")}
              fullWidth
              label="Display name"
              size="small"
              error={Boolean(errors.label)}
              helperText={errors.label?.message}
              sx={{ mb: 2 }}
            />

            <TextField
              {...register("description")}
              fullWidth
              label="Description"
              size="small"
              multiline
              rows={2}
              error={Boolean(errors.description)}
              helperText={errors.description?.message}
              sx={{ mb: 2 }}
            />

            {isEditMode && (
              <Controller
                name="active"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={
                      <Switch
                        checked={field.value}
                        onChange={(_, checked) => field.onChange(checked)}
                      />
                    }
                    label="Active (shown in tool provider dropdowns)"
                  />
                )}
              />
            )}
          </Box>
        </SlideOver>

        <ConfirmDialog
          open={deleteTarget !== null}
          title="Delete provider?"
          description={`Tools using "${deleteTarget?.slug ?? ""}" will fail validation until reassigned.`}
          dangerous
          confirmLabel="Delete"
          loading={deleteMutation.isPending}
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => {
            if (deleteTarget) {
              deleteMutation.mutate(deleteTarget.slug);
            }
          }}
        />
      </Box>
    </RoleGuard>
  );
}

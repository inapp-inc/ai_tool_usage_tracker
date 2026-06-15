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
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  createProvider,
  deleteProvider,
  fetchProviders,
  updateProvider,
  type Provider,
} from "@/api/providers";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { LIVE_DATA_POLL_MS } from "@/config/apiPolling";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";

const slugPattern = /^[a-z][a-z0-9_]{1,62}$/;

const createSchema = z.object({
  slug: z
    .string()
    .min(2, "Slug is required")
    .max(64)
    .regex(
      slugPattern,
      "Lowercase letters, numbers, underscores; must start with a letter",
    ),
  name: z.string().min(1, "Name is required").max(100),
  usageApiUrl: z
    .string()
    .url("Enter a valid URL")
    .min(8, "Usage API URL is required"),
  description: z.string().max(500).default(""),
});

const editSchema = createSchema.omit({ slug: true }).extend({
  active: z.boolean(),
});

type CreateFormValues = z.infer<typeof createSchema>;
type EditFormValues = z.infer<typeof editSchema>;
type FormValues = CreateFormValues | EditFormValues;

interface SlideOverState {
  open: boolean;
  provider: Provider | null;
}

function defaultCreateValues(): CreateFormValues {
  return {
    slug: "",
    name: "",
    usageApiUrl: "",
    description: "",
  };
}

function truncateUrl(url: string, maxLength = 48): string {
  if (url.length <= maxLength) {
    return url;
  }
  return `${url.slice(0, maxLength)}…`;
}

export function ProvidersPage() {
  const queryClient = useQueryClient();
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    provider: null,
  });
  const [deleteTarget, setDeleteTarget] = useState<Provider | null>(null);

  const providersQuery = useQuery({
    queryKey: ["providers"],
    queryFn: () => fetchProviders(),
    refetchInterval: LIVE_DATA_POLL_MS,
  });

  const createMutation = useMutation({
    mutationFn: createProvider,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["providers"] });
      setSlideOver({ open: false, provider: null });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: Parameters<typeof updateProvider>[1];
    }) => updateProvider(id, body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["providers"] });
      setSlideOver({ open: false, provider: null });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProvider,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["providers"] });
      setDeleteTarget(null);
    },
  });

  const isEditMode = slideOver.provider !== null;
  const savePending = createMutation.isPending || updateMutation.isPending;

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(isEditMode ? editSchema : createSchema),
    defaultValues: defaultCreateValues(),
  });

  const activeValue = watch("active" as keyof FormValues);

  useEffect(() => {
    if (!slideOver.open) {
      reset(defaultCreateValues());
      return;
    }

    if (slideOver.provider) {
      reset({
        name: slideOver.provider.name,
        usageApiUrl: slideOver.provider.usageApiUrl,
        description: slideOver.provider.description,
        active: slideOver.provider.active,
      });
      return;
    }

    reset(defaultCreateValues());
  }, [reset, slideOver]);

  const columns: Column<Provider>[] = useMemo(
    () => [
      {
        key: "name",
        header: "Provider",
        sortable: true,
        render: (row) => (
          <Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {row.name}
              </Typography>
              {row.isSystem && (
                <Chip
                  size="small"
                  label="Built-in"
                  sx={{
                    height: 20,
                    fontSize: "0.625rem",
                    backgroundColor: "#EFF6FF",
                    color: "#2563EB",
                  }}
                />
              )}
            </Box>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {row.slug}
            </Typography>
          </Box>
        ),
      },
      {
        key: "usageApiUrl",
        header: "Usage API URL",
        render: (row) => (
          <Typography
            variant="caption"
            sx={{ color: tokens.textSecondary, fontFamily: "monospace" }}
          >
            {truncateUrl(row.usageApiUrl)}
          </Typography>
        ),
      },
      {
        key: "active",
        header: "Status",
        render: (row) => (
          <StatusBadge status={row.active ? "active" : "inactive"} />
        ),
      },
      {
        key: "actions",
        header: "",
        width: 96,
        render: (row) => (
          <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 0.5 }}>
            <IconButton
              size="small"
              aria-label={`Edit ${row.name}`}
              onClick={() => setSlideOver({ open: true, provider: row })}
            >
              <IconPencil size={16} />
            </IconButton>
            {!row.isSystem && (
              <IconButton
                size="small"
                aria-label={`Delete ${row.name}`}
                onClick={() => setDeleteTarget(row)}
              >
                <IconTrash size={16} />
              </IconButton>
            )}
          </Box>
        ),
      },
    ],
    [],
  );

  const onSubmit = (data: FormValues) => {
    if (slideOver.provider) {
      updateMutation.mutate({
        id: slideOver.provider.id,
        body: {
          name: data.name,
          usageApiUrl: data.usageApiUrl,
          description: data.description,
          active: "active" in data ? data.active : slideOver.provider.active,
        },
      });
      return;
    }

    createMutation.mutate({
      slug: (data as CreateFormValues).slug.toLowerCase(),
      name: data.name,
      usageApiUrl: data.usageApiUrl,
      description: data.description,
    });
  };

  return (
    <RoleGuard
      roles={[Role.SuperAdmin]}
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to manage providers."
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
              Providers
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Configure AI vendors and usage API endpoints for the connect flow
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
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load providers. Please refresh.
          </Alert>
        )}

        <DataTable
          columns={columns}
          rows={providersQuery.data ?? []}
          rowKey={(row) => row.id}
          loading={providersQuery.isPending}
          emptyTitle="No providers configured"
          emptyDescription="Add a provider to make it available when connecting tools."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, provider: null })}
          title={isEditMode ? "Edit provider" : "Add provider"}
          subtitle={
            isEditMode
              ? "Update display name, usage URL, or availability"
              : "New providers appear in the Connect Tool provider list"
          }
          width={520}
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
            {!isEditMode && (
              <TextField
                {...register("slug")}
                fullWidth
                label="Slug"
                size="small"
                placeholder="my_custom_provider"
                error={Boolean(errors.slug)}
                helperText={
                  errors.slug?.message ??
                  "Unique identifier used when connecting tools"
                }
              />
            )}

            <TextField
              {...register("name")}
              fullWidth
              label="Display name"
              size="small"
              placeholder="My Custom Provider"
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
            />

            <TextField
              {...register("usageApiUrl")}
              fullWidth
              label="Usage API URL"
              size="small"
              placeholder="https://api.example.com/v1/usage"
              error={Boolean(errors.usageApiUrl)}
              helperText={
                errors.usageApiUrl?.message ??
                "Endpoint used to fetch usage data from this vendor"
              }
            />

            <TextField
              {...register("description")}
              fullWidth
              label="Description"
              size="small"
              multiline
              rows={2}
              placeholder="Optional notes about this provider"
              error={Boolean(errors.description)}
              helperText={errors.description?.message}
            />

            {isEditMode && (
              <FormControlLabel
                control={
                  <Switch
                    checked={Boolean(activeValue)}
                    onChange={(_, checked) =>
                      setValue("active" as keyof FormValues, checked as never)
                    }
                  />
                }
                label="Active (visible in Connect Tool list)"
              />
            )}

            {(createMutation.isError || updateMutation.isError) && (
              <Alert severity="error">
                Failed to save provider. Check the slug is unique and the URL is
                valid.
              </Alert>
            )}
          </Box>
        </SlideOver>

        <ConfirmDialog
          open={deleteTarget !== null}
          title="Delete provider"
          description={
            deleteTarget
              ? `Remove "${deleteTarget.name}"? This cannot be undone. Providers in use by tools cannot be deleted.`
              : ""
          }
          confirmLabel="Delete"
          confirmColor="error"
          loading={deleteMutation.isPending}
          onConfirm={() => {
            if (deleteTarget) {
              deleteMutation.mutate(deleteTarget.id);
            }
          }}
          onCancel={() => setDeleteTarget(null)}
        />
      </Box>
    </RoleGuard>
  );
}

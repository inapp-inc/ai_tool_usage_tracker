import { zodResolver } from "@hookform/resolvers/zod";
import {
  IconAlertTriangle,
  IconCheck,
  IconCircleCheck,
  IconCopy,
  IconPencil,
  IconPlus,
  IconTrash,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
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
import { differenceInDays, parseISO } from "date-fns";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import {
  createCredential,
  fetchCredentials,
  revealCredentialSecret,
  deleteCredential,
  syncScheduleLabel,
  updateCredential,
  type Credential,
  type SyncSchedule,
} from "@/api/credentials";
import { ApiClientError } from "@/api/client";
import { fetchToolOptions } from "@/api/tools";
import { providerRequiresAnthropicAdminKey, providerRequiresGcpMonitoring, providerRequiresOpenAiAdminKey, providerRequiresOrganizationId } from "@/api/providers";
import { fetchTeams } from "@/api/teams";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { formatDate } from "@/utils/formatters";

const createSchema = z.object({
  label: z.string().min(1, "Label is required").max(100),
  description: z.string().max(200).default(""),
  catalogueToolId: z.string().min(1, "Select a tool"),
  teamId: z.string().min(1, "Select a team"),
  syncSchedule: z.enum(["hourly", "daily"]),
  apiKey: z.string().min(1, "API key is required"),
  organizationId: z.string().max(100).optional(),
  gcpProjectId: z.string().max(100).optional(),
  gcpServiceAccountJson: z.string().max(16384).optional(),
  rotationReminderDays: z.number().int().positive().nullable(),
  expiresAt: z.string().nullable(),
});

const editSchema = createSchema
  .omit({ apiKey: true, catalogueToolId: true })
  .extend({
    apiKey: z.string().optional(),
  });

type CreateFormValues = z.infer<typeof createSchema>;
type EditFormValues = z.infer<typeof editSchema>;
type FormValues = CreateFormValues;

interface SlideOverState {
  open: boolean;
  credential: Credential | null;
}

function defaultFormValues(): CreateFormValues {
  return {
    label: "",
    description: "",
    catalogueToolId: "",
    teamId: "",
    syncSchedule: "hourly",
    apiKey: "",
    organizationId: "",
    gcpProjectId: "",
    gcpServiceAccountJson: "",
    rotationReminderDays: null,
    expiresAt: null,
  };
}

function credentialToFormValues(credential: Credential): EditFormValues {
  return {
    label: credential.label,
    description: credential.description,
    teamId: credential.teamId,
    syncSchedule: credential.syncSchedule,
    rotationReminderDays: credential.rotationReminderDays,
    expiresAt: toDateInputValue(credential.expiresAt),
    apiKey: credential.keyMasked,
  };
}

function daysUntilExpiry(iso: string): number {
  return differenceInDays(parseISO(iso), new Date());
}

function isExpired(expiresAt: string | null): boolean {
  if (!expiresAt) {
    return false;
  }
  return daysUntilExpiry(expiresAt) < 0;
}

function isExpiringSoon(expiresAt: string | null): boolean {
  if (!expiresAt) {
    return false;
  }
  const days = daysUntilExpiry(expiresAt);
  return days >= 0 && days <= 14;
}

function parseNullableNumber(value: unknown): number | null {
  if (value === "" || value == null) {
    return null;
  }
  const parsed = Number(value);
  if (Number.isNaN(parsed)) {
    return null;
  }
  return parsed;
}

function parseExpiryDate(value: string | null): string | null {
  if (!value) {
    return null;
  }
  return new Date(`${value}T23:59:59`).toISOString();
}

function toDateInputValue(iso: string | null): string {
  if (!iso) {
    return "";
  }
  return iso.slice(0, 10);
}

export function CredentialsPage() {
  const queryClient = useQueryClient();
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    credential: null,
  });
  const [connectSuccess, setConnectSuccess] = useState(false);
  const [connectedSchedule, setConnectedSchedule] = useState<SyncSchedule>("hourly");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [copyingId, setCopyingId] = useState<string | null>(null);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Credential | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const credentialsQuery = useQuery({
    queryKey: ["credentials"],
    queryFn: fetchCredentials,
  });

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const catalogueToolsQuery = useQuery({
    queryKey: ["catalogue-tool-options"],
    queryFn: fetchToolOptions,
  });

  const isEditMode = slideOver.credential !== null;

  const activeSchema = useMemo(
    () => (isEditMode ? editSchema : createSchema),
    [isEditMode],
  );

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(activeSchema),
    defaultValues: defaultFormValues(),
  });

  const closeSlideOver = useCallback(() => {
    setConnectSuccess(false);
    setSlideOver({ open: false, credential: null });
    reset(defaultFormValues());
  }, [reset]);

  const createMutation = useMutation({
    mutationFn: createCredential,
    onSuccess: (response) => {
      setSaveError(null);
      setConnectedSchedule(response.credential.syncSchedule);
      setConnectSuccess(true);
    },
    onError: (error) => {
      const message =
        error instanceof ApiClientError
          ? error.apiError.detail
          : "Could not connect tool. Please try again.";
      setSaveError(message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: Parameters<typeof updateCredential>[1];
    }) => updateCredential(id, body),
    onSuccess: async () => {
      setSaveError(null);
      await queryClient.invalidateQueries({ queryKey: ["credentials"] });
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      await queryClient.invalidateQueries({ queryKey: ["team-tool-usage"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      closeSlideOver();
    },
    onError: (error) => {
      const message =
        error instanceof ApiClientError
          ? error.apiError.detail
          : "Could not update credential. Please try again.";
      setSaveError(message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCredential,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["credentials"] });
      await queryClient.invalidateQueries({ queryKey: ["tools"] });
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      setDeleteTarget(null);
    },
  });

  const savePending = createMutation.isPending || updateMutation.isPending;

  const rotationReminderDays = watch("rotationReminderDays");
  const selectedCatalogueToolId = watch("catalogueToolId");
  const teams = teamsQuery.data ?? [];
  const catalogueTools = catalogueToolsQuery.data ?? [];
  const selectedCatalogueTool = catalogueTools.find(
    (tool) => tool.id === selectedCatalogueToolId,
  );
  const showOrganizationId =
    !isEditMode && providerRequiresOrganizationId(selectedCatalogueTool?.provider ?? "");
  const showOpenAiAdminKeyHint =
    !isEditMode && providerRequiresOpenAiAdminKey(selectedCatalogueTool?.provider ?? "");
  const showAnthropicAdminKeyHint =
    !isEditMode && providerRequiresAnthropicAdminKey(selectedCatalogueTool?.provider ?? "");
  const showGcpMonitoring =
    !isEditMode && providerRequiresGcpMonitoring(selectedCatalogueTool?.provider ?? "");

  const handleCopyCredential = useCallback(async (credentialId: string) => {
    setCopyError(null);
    setCopyingId(credentialId);
    try {
      const secret = await revealCredentialSecret(credentialId);
      await navigator.clipboard.writeText(secret);
      setCopiedId(credentialId);
    } catch {
      setCopyError(
        "Could not copy the API key. Refresh and try again, or rotate the key in Edit.",
      );
    } finally {
      setCopyingId(null);
    }
  }, []);

  useEffect(() => {
    if (!copiedId) {
      return;
    }
    const timer = window.setTimeout(() => setCopiedId(null), 2000);
    return () => window.clearTimeout(timer);
  }, [copiedId]);

  useEffect(() => {
    if (!slideOver.open) {
      reset(defaultFormValues());
      setSaveError(null);
      return;
    }

    if (slideOver.credential) {
      reset(credentialToFormValues(slideOver.credential));
      return;
    }

    reset(defaultFormValues());
  }, [reset, slideOver]);

  useEffect(() => {
    if (!slideOver.open || isEditMode || !selectedCatalogueTool?.organizationId) {
      return;
    }
    reset((current) => ({
      ...current,
      organizationId: selectedCatalogueTool.organizationId ?? "",
    }));
  }, [isEditMode, reset, selectedCatalogueTool?.organizationId, slideOver.open]);

  const handleSlideOverClose = () => {
    closeSlideOver();
  };

  const handleDone = async () => {
    await queryClient.invalidateQueries({ queryKey: ["credentials"] });
    await queryClient.invalidateQueries({ queryKey: ["tools"] });
    await queryClient.invalidateQueries({ queryKey: ["tool-options"] });
    await queryClient.invalidateQueries({ queryKey: ["catalogue-tool-options"] });
    await queryClient.invalidateQueries({ queryKey: ["teams"] });
    await queryClient.invalidateQueries({ queryKey: ["team-tool-usage"] });
    await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    closeSlideOver();
  };

  const openAddSlideOver = () => {
    setConnectSuccess(false);
    setSlideOver({ open: true, credential: null });
  };

  const openEditSlideOver = (credential: Credential) => {
    setConnectSuccess(false);
    setSlideOver({ open: true, credential });
  };

  const buildPayload = (data: FormValues) => ({
    label: data.label,
    description: data.description,
    teamId: data.teamId,
    syncSchedule: data.syncSchedule,
    rotationReminderDays: data.rotationReminderDays,
    expiresAt: parseExpiryDate(data.expiresAt),
  });

  const onSubmit = (data: FormValues) => {
    setSaveError(null);

    if (slideOver.credential) {
      const apiKeyChanged =
        Boolean(data.apiKey?.trim()) &&
        data.apiKey.trim() !== slideOver.credential.keyMasked;

      updateMutation.mutate({
        id: slideOver.credential.id,
        body: {
          ...buildPayload(data),
          ...(apiKeyChanged ? { apiKey: data.apiKey!.trim() } : {}),
        },
      });
      return;
    }

    if (showOrganizationId && !data.organizationId?.trim()) {
      setSaveError("GitHub organization ID is required for Microsoft Copilot.");
      return;
    }

    createMutation.mutate({
      ...buildPayload(data),
      catalogueToolId: (data as CreateFormValues).catalogueToolId,
      apiKey: data.apiKey,
      organizationId: showOrganizationId ? data.organizationId?.trim() || null : null,
      gcpProjectId: showGcpMonitoring ? data.gcpProjectId?.trim() || null : null,
      gcpServiceAccountJson: showGcpMonitoring
        ? data.gcpServiceAccountJson?.trim() || null
        : null,
    });
  };

  const expiringSoonCount = useMemo(() => {
    const credentials = credentialsQuery.data ?? [];
    return credentials.filter(
      (credential) =>
        credential.status === "active" &&
        credential.expiresAt &&
        daysUntilExpiry(credential.expiresAt) <= 14 &&
        daysUntilExpiry(credential.expiresAt) >= 0,
    ).length;
  }, [credentialsQuery.data]);

  const columns: Column<Credential>[] = useMemo(
    () => [
      {
        key: "label",
        header: "Credential",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.label}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: tokens.textMuted,
                fontFamily: "monospace",
                display: "block",
              }}
            >
              {row.keyMasked}
            </Typography>
          </Box>
        ),
      },
      {
        key: "catalogueToolName",
        header: "Tool",
        sortable: true,
        render: (row) => (
          <Typography variant="body2">{row.catalogueToolName || row.toolName}</Typography>
        ),
      },
      {
        key: "teamName",
        header: "Team",
        sortable: true,
        render: (row) => <Typography variant="body2">{row.teamName}</Typography>,
      },
      {
        key: "syncSchedule",
        header: "Sync",
        render: (row) => (
          <Typography variant="body2">{syncScheduleLabel(row.syncSchedule)}</Typography>
        ),
      },
      {
        key: "expiresAt",
        header: "Expires",
        sortable: true,
        render: (row) => {
          if (!row.expiresAt) {
            return (
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                Never
              </Typography>
            );
          }

          if (isExpired(row.expiresAt)) {
            return (
              <Typography variant="body2" sx={{ color: tokens.critical }}>
                Expired
              </Typography>
            );
          }

          if (isExpiringSoon(row.expiresAt)) {
            return (
              <Box>
                <Box sx={{ display: "inline-flex", alignItems: "center", gap: 0.5 }}>
                  <Typography variant="body2" sx={{ color: tokens.warning }}>
                    {formatDate(row.expiresAt)}
                  </Typography>
                  <IconAlertTriangle size={13} color={tokens.warning} />
                </Box>
                <Typography variant="caption" sx={{ color: tokens.warning }}>
                  Expiring soon
                </Typography>
              </Box>
            );
          }

          return (
            <Typography variant="body2">{formatDate(row.expiresAt)}</Typography>
          );
        },
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
                aria-label={`Copy API key for ${row.label}`}
                disabled={copyingId === row.id}
                onClick={(event) => {
                  event.stopPropagation();
                  void handleCopyCredential(row.id);
                }}
              >
                {copyingId === row.id ? (
                  <CircularProgress size={14} />
                ) : copiedId === row.id ? (
                  <IconCheck size={15} color={tokens.success} />
                ) : (
                  <IconCopy size={15} />
                )}
              </IconButton>
              <IconButton
                size="small"
                aria-label={`Edit ${row.label}`}
                onClick={(event) => {
                  event.stopPropagation();
                  openEditSlideOver(row);
                }}
              >
                <IconPencil size={15} />
              </IconButton>
              <IconButton
                size="small"
                aria-label={`Delete ${row.label}`}
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
    [copiedId, copyingId, handleCopyCredential],
  );

  return (
    <RoleGuard
      roles={[Role.SuperAdmin]}
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to manage API credentials."
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
              API Credentials
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Connect live API keys to providers — separate from the Tools catalogue
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="small"
            startIcon={<IconPlus size={15} />}
            onClick={openAddSlideOver}
          >
            Connect Tool
          </Button>
        </Box>

        {credentialsQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load credentials. Please refresh.
          </Alert>
        )}

        {copyError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setCopyError(null)}>
            {copyError}
          </Alert>
        )}

        {!credentialsQuery.isPending && expiringSoonCount > 0 && (
          <Alert
            severity="warning"
            sx={{ mb: 2 }}
            icon={<IconAlertTriangle size={16} />}
          >
            {expiringSoonCount} credential{expiringSoonCount > 1 ? "s are" : " is"}{" "}
            expiring within 14 days. Review and rotate as needed.
          </Alert>
        )}

        <DataTable
          columns={columns}
          rows={credentialsQuery.data ?? []}
          rowKey={(row) => row.id}
          loading={credentialsQuery.isPending}
          emptyTitle="No connections yet"
          emptyDescription="Add tools under Tools first, then connect them here with an API key."
        />

        <SlideOver
          open={slideOver.open}
          onClose={handleSlideOverClose}
          title={
            connectSuccess
              ? "Connected successfully"
              : isEditMode
                ? "Edit Credential"
                : "Connect Tool"
          }
          {...(connectSuccess || isEditMode
            ? {}
            : { subtitle: "Verify your API key and sync usage in the background" })}
          width={520}
          footer={
            connectSuccess ? undefined : (
              <>
                <Button
                  variant="text"
                  onClick={handleSlideOverClose}
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
                  {isEditMode ? "Save" : "Connect Tool"}
                </Button>
              </>
            )
          }
        >
          {connectSuccess ? (
            <Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <IconCircleCheck size={24} color={tokens.success} />
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  Connected successfully
                </Typography>
              </Box>

              <Alert severity="success" sx={{ mb: 2 }}>
                Your API key was verified. Usage data will sync{" "}
                {connectedSchedule === "daily" ? "daily" : "hourly"} in the background — use
                Refresh on the Teams page to pull the latest data anytime.
              </Alert>

              <Button variant="contained" fullWidth onClick={() => void handleDone()}>
                Done
              </Button>
            </Box>
          ) : (
            <Box
              component="form"
              onSubmit={handleSubmit(onSubmit)}
              sx={{ display: "flex", flexDirection: "column" }}
            >
              {saveError && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setSaveError(null)}>
                  {saveError}
                </Alert>
              )}

              <TextField
                {...register("label")}
                fullWidth
                label="Label"
                size="small"
                placeholder="e.g. GPT-4o – Engineering"
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

              {isEditMode && slideOver.credential && (
                <TextField
                  fullWidth
                  label="Tool"
                  size="small"
                  value={slideOver.credential.catalogueToolName || slideOver.credential.toolName}
                  disabled
                  sx={{ mb: 2 }}
                />
              )}

              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: isEditMode ? "1fr" : "1fr 1fr",
                  gap: 2,
                  mb: 2,
                }}
              >
                {!isEditMode && (
                  <Controller
                    name="catalogueToolId"
                    control={control}
                    render={({ field }) => (
                      <FormControl
                        fullWidth
                        size="small"
                        error={Boolean(errors.catalogueToolId)}
                      >
                        <InputLabel id="credential-tool-label">Tool</InputLabel>
                        <Select
                          {...field}
                          labelId="credential-tool-label"
                          label="Tool"
                          disabled={catalogueToolsQuery.isPending}
                        >
                          {catalogueTools.length === 0 ? (
                            <MenuItem disabled value="">
                              No tools in catalogue — add one under Tools first
                            </MenuItem>
                          ) : (
                            catalogueTools.map((tool) => (
                              <MenuItem key={tool.id} value={tool.id}>
                                {tool.name}
                              </MenuItem>
                            ))
                          )}
                        </Select>
                        {errors.catalogueToolId && (
                          <FormHelperText>{errors.catalogueToolId.message}</FormHelperText>
                        )}
                      </FormControl>
                    )}
                  />
                )}

                <Controller
                  name="teamId"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth size="small" error={Boolean(errors.teamId)}>
                      <InputLabel id="credential-team-label">Team</InputLabel>
                      <Select
                        {...field}
                        labelId="credential-team-label"
                        label="Team"
                        disabled={teamsQuery.isPending}
                      >
                        {teams.map((team) => (
                          <MenuItem key={team.id} value={team.id}>
                            {team.name}
                          </MenuItem>
                        ))}
                      </Select>
                      {errors.teamId && (
                        <FormHelperText>{errors.teamId.message}</FormHelperText>
                      )}
                    </FormControl>
                  )}
                />
              </Box>

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
                    "Required for Copilot — bound into the GitHub API URL for usage collection."
                  }
                  sx={{ mb: 2 }}
                />
              )}

              {showGcpMonitoring && (
                <>
                  <TextField
                    {...register("gcpProjectId")}
                    fullWidth
                    label="GCP project ID"
                    size="small"
                    placeholder="my-gemini-project"
                    error={Boolean(errors.gcpProjectId)}
                    helperText={
                      errors.gcpProjectId?.message ??
                      "Google Cloud project linked to your Gemini API key (for token usage sync)."
                    }
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    {...register("gcpServiceAccountJson")}
                    fullWidth
                    label="GCP service account JSON"
                    size="small"
                    multiline
                    minRows={4}
                    placeholder='{"type":"service_account",...}'
                    error={Boolean(errors.gcpServiceAccountJson)}
                    helperText={
                      errors.gcpServiceAccountJson?.message ??
                      "Service account with roles/monitoring.viewer — used to pull token usage from Cloud Monitoring."
                    }
                    sx={{ mb: 2 }}
                  />
                </>
              )}

              <Controller
                name="syncSchedule"
                control={control}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={Boolean(errors.syncSchedule)}
                    sx={{ mb: 2 }}
                  >
                    <InputLabel id="credential-sync-label">Data sync schedule</InputLabel>
                    <Select
                      {...field}
                      labelId="credential-sync-label"
                      label="Data sync schedule"
                    >
                      <MenuItem value="hourly">Hourly</MenuItem>
                      <MenuItem value="daily">Daily</MenuItem>
                    </Select>
                    <FormHelperText>
                      How often usage data is pulled from the provider for this team.
                    </FormHelperText>
                  </FormControl>
                )}
              />

              {isEditMode ? (
                <TextField
                  {...register("apiKey")}
                  fullWidth
                  label="API Key"
                  size="small"
                  type="text"
                  error={Boolean(errors.apiKey) || Boolean(saveError)}
                  helperText={
                    errors.apiKey?.message ??
                    (saveError
                      ? saveError
                      : "Leave as the masked value to keep the current key, or enter a new key to rotate and re-verify.")
                  }
                  sx={{ mb: 2 }}
                />
              ) : (
                <TextField
                  {...register("apiKey")}
                  fullWidth
                  label="API Key"
                  size="small"
                  type="password"
                  error={Boolean(errors.apiKey) || Boolean(saveError)}
                  helperText={
                    errors.apiKey?.message ??
                    (saveError
                      ? saveError
                      : showOpenAiAdminKeyHint
                        ? "Paste an Organization Admin API key (starts with sk-admin-). It is verified against OpenAI organization endpoints before saving."
                        : showAnthropicAdminKeyHint
                          ? "Paste an Anthropic Admin API key (starts with sk-ant-admin-). Standard Messages API keys cannot pull organization usage."
                          : showGcpMonitoring
                            ? "Paste your Gemini API key from Google AI Studio. Add GCP project + service account below to sync historical token usage."
                            : "The key is verified with the provider before saving. Usage syncs in the background.")
                  }
                  sx={{ mb: 2 }}
                />
              )}

              <Typography
                variant="caption"
                sx={{
                  color: tokens.textMuted,
                  textTransform: "uppercase",
                  mt: 1,
                  mb: 1,
                  display: "block",
                }}
              >
                Rotation & expiry
              </Typography>

              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 2,
                  mb: 2,
                }}
              >
                <TextField
                  {...register("expiresAt", {
                    setValueAs: (value: string) => (value === "" ? null : value),
                  })}
                  fullWidth
                  label="Expiry date"
                  size="small"
                  type="date"
                  slotProps={{ inputLabel: { shrink: true } }}
                />
                <TextField
                  {...register("rotationReminderDays", {
                    setValueAs: parseNullableNumber,
                  })}
                  fullWidth
                  label="Rotation reminder (days before)"
                  size="small"
                  type="number"
                  placeholder="e.g. 14"
                />
              </Box>

              {rotationReminderDays != null && rotationReminderDays > 0 && (
                <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                  A reminder will appear in the dashboard {rotationReminderDays}{" "}
                  days before the key expires
                </Typography>
              )}
            </Box>
          )}
        </SlideOver>

        <ConfirmDialog
          open={deleteTarget !== null}
          title="Delete credential?"
          description={`Permanently delete "${deleteTarget?.label ?? ""}" for "${deleteTarget?.catalogueToolName ?? deleteTarget?.toolName ?? ""}" on "${deleteTarget?.teamName ?? ""}"? This removes the connection and stops all sync for this team.`}
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

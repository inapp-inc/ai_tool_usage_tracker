import { zodResolver } from "@hookform/resolvers/zod";
import {
  IconAlertTriangle,
  IconBan,
  IconCheck,
  IconCircleCheck,
  IconCopy,
  IconPencil,
  IconPlus,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  FormHelperText,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
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
  revokeCredential,
  updateCredential,
  type Credential,
  type CredentialEnvironment,
} from "@/api/credentials";
import { ApiClientError } from "@/api/client";
import { fetchTeams } from "@/api/teams";
import { fetchToolOptions } from "@/api/usage";
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
  toolId: z.string().min(1, "Select a tool"),
  teamId: z.string().min(1, "Select a team"),
  environment: z.enum(["production", "sandbox"]),
  apiKey: z.string().min(1, "API key is required"),
  rotationReminderDays: z.number().int().positive().nullable(),
  expiresAt: z.string().nullable(),
});

const editSchema = createSchema.omit({ apiKey: true }).extend({
  apiKey: z.string().optional(),
});

type CreateFormValues = z.infer<typeof createSchema>;
type EditFormValues = z.infer<typeof editSchema>;
type FormValues = CreateFormValues;

interface SlideOverState {
  open: boolean;
  credential: Credential | null;
}

const ENV_CHIP_COLORS: Record<
  CredentialEnvironment,
  { background: string; color: string; label: string }
> = {
  production: {
    background: "#ECFDF5",
    color: "#059669",
    label: "Production",
  },
  sandbox: {
    background: "#FFF7ED",
    color: "#C2410C",
    label: "Sandbox",
  },
};

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

function EnvironmentChip({ environment }: { environment: CredentialEnvironment }) {
  const colors = ENV_CHIP_COLORS[environment];
  return (
    <Chip
      size="small"
      label={colors.label}
      sx={{
        backgroundColor: colors.background,
        color: colors.color,
        fontWeight: 500,
        fontSize: "0.6875rem",
        height: 22,
        "& .MuiChip-label": { px: 1 },
      }}
    />
  );
}

function defaultFormValues(): CreateFormValues {
  return {
    label: "",
    description: "",
    toolId: "",
    teamId: "",
    environment: "production",
    apiKey: "",
    rotationReminderDays: null,
    expiresAt: null,
  };
}

function credentialToFormValues(credential: Credential): EditFormValues {
  return {
    label: credential.label,
    description: credential.description,
    toolId: credential.toolId,
    teamId: credential.teamId,
    environment: credential.environment,
    rotationReminderDays: credential.rotationReminderDays,
    expiresAt: toDateInputValue(credential.expiresAt),
    apiKey: credential.keyMasked,
  };
}

export function CredentialsPage() {
  const queryClient = useQueryClient();
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    credential: null,
  });
  const [plainKey, setPlainKey] = useState<string | null>(null);
  const [showCloseWarning, setShowCloseWarning] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [copyingId, setCopyingId] = useState<string | null>(null);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<Credential | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const credentialsQuery = useQuery({
    queryKey: ["credentials"],
    queryFn: fetchCredentials,
  });

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const toolOptionsQuery = useQuery({
    queryKey: ["tool-options"],
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
    setPlainKey(null);
    setShowCloseWarning(false);
    setSlideOver({ open: false, credential: null });
    reset(defaultFormValues());
  }, [reset]);

  const createMutation = useMutation({
    mutationFn: createCredential,
    onSuccess: (response) => {
      setSaveError(null);
      setPlainKey(response.plainKey);
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

  const revokeMutation = useMutation({
    mutationFn: revokeCredential,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["credentials"] });
      setRevokeTarget(null);
    },
  });

  const savePending = createMutation.isPending || updateMutation.isPending;

  const rotationReminderDays = watch("rotationReminderDays");
  const teams = teamsQuery.data ?? [];
  const toolOptions = toolOptionsQuery.data ?? [];

  const handleCopyPlainText = useCallback(async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
  }, []);

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

  const handleSlideOverClose = () => {
    if (plainKey) {
      setShowCloseWarning(true);
      return;
    }
    closeSlideOver();
  };

  const handleDone = async () => {
    await queryClient.invalidateQueries({ queryKey: ["credentials"] });
    await queryClient.invalidateQueries({ queryKey: ["tools"] });
    closeSlideOver();
  };

  const openAddSlideOver = () => {
    setPlainKey(null);
    setShowCloseWarning(false);
    setSlideOver({ open: true, credential: null });
  };

  const openEditSlideOver = (credential: Credential) => {
    setPlainKey(null);
    setShowCloseWarning(false);
    setSlideOver({ open: true, credential });
  };

  const buildPayload = (data: FormValues) => ({
    label: data.label,
    description: data.description,
    toolId: data.toolId,
    teamId: data.teamId,
    environment: data.environment,
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

    createMutation.mutate({
      ...buildPayload(data),
      apiKey: data.apiKey,
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
        key: "toolName",
        header: "Tool",
        sortable: true,
        render: (row) => <Typography variant="body2">{row.toolName}</Typography>,
      },
      {
        key: "teamName",
        header: "Team",
        sortable: true,
        render: (row) => <Typography variant="body2">{row.teamName}</Typography>,
      },
      {
        key: "environment",
        header: "Env",
        render: (row) => <EnvironmentChip environment={row.environment} />,
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
        render: (row) => {
          const inactive = row.status === "inactive";
          return (
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
                aria-label={`Revoke ${row.label}`}
                disabled={inactive}
                onClick={(event) => {
                  event.stopPropagation();
                  setRevokeTarget(row);
                }}
                sx={{
                  color: inactive ? tokens.textMuted : tokens.critical,
                }}
              >
                <IconBan size={15} />
              </IconButton>
            </Box>
          );
        },
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
              API keys for connected AI tools — masked, expiry, and status
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
          emptyTitle="No credentials yet"
          emptyDescription="Connect an AI tool under Tools, then manage its API key here."
        />

        <SlideOver
          open={slideOver.open}
          onClose={handleSlideOverClose}
          title={
            plainKey
              ? "Tool connected"
              : isEditMode
                ? "Edit Credential"
                : "Connect Tool"
          }
          {...(plainKey || isEditMode
            ? {}
            : { subtitle: "Verify your API key and sync usage in the background" })}
          width={520}
          footer={
            plainKey ? undefined : (
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
          {plainKey ? (
            <Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <IconCircleCheck size={24} color={tokens.success} />
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  Tool connected
                </Typography>
              </Box>

              <Alert severity="success" sx={{ mb: 2 }}>
                Your API key was verified. Usage data is syncing in the background — check
                the Tools page in a moment for updated stats.
              </Alert>

              <Alert severity="warning" sx={{ mb: 2 }}>
                Copy your key now if you need it — it won&apos;t be shown again.
              </Alert>

              <Box
                sx={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 1,
                  backgroundColor: tokens.bgDefault,
                  border: `0.5px solid ${tokens.border}`,
                  borderRadius: "6px",
                  p: 1.5,
                  mb: 2,
                }}
              >
                <Typography
                  sx={{
                    flex: 1,
                    fontFamily: "monospace",
                    fontSize: "0.8125rem",
                    wordBreak: "break-all",
                  }}
                >
                  {plainKey}
                </Typography>
                <IconButton
                  size="small"
                  aria-label="Copy API key"
                  onClick={() => void handleCopyPlainText(plainKey, "reveal")}
                >
                  {copiedId === "reveal" ? (
                    <IconCheck size={16} color={tokens.success} />
                  ) : (
                    <IconCopy size={16} />
                  )}
                </IconButton>
              </Box>

              {showCloseWarning && (
                <Box
                  sx={{
                    mb: 2,
                    p: 1.5,
                    borderRadius: "6px",
                    border: `0.5px solid ${tokens.border}`,
                    backgroundColor: tokens.bgDefault,
                  }}
                >
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Have you copied your key?
                  </Typography>
                  <Box sx={{ display: "flex", gap: 1 }}>
                    <Button
                      size="small"
                      variant="text"
                      onClick={() => setShowCloseWarning(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="small"
                      variant="contained"
                      color="warning"
                      onClick={() => void handleDone()}
                    >
                      Confirm
                    </Button>
                  </Box>
                </Box>
              )}

              <Button variant="contained" fullWidth onClick={() => void handleDone()}>
                I&apos;ve copied my key — Done
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
                placeholder="e.g. GPT-4o Production – Engineering"
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

              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 2,
                  mb: 2,
                }}
              >
                <Controller
                  name="toolId"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth size="small" error={Boolean(errors.toolId)}>
                      <InputLabel id="credential-tool-label">AI Tool</InputLabel>
                      <Select
                        {...field}
                        labelId="credential-tool-label"
                        label="AI Tool"
                        disabled={toolOptionsQuery.isPending || isEditMode}
                      >
                        {toolOptions.map((tool) => (
                          <MenuItem key={tool.id} value={tool.id}>
                            {tool.name}
                          </MenuItem>
                        ))}
                      </Select>
                      {errors.toolId && (
                        <FormHelperText>{errors.toolId.message}</FormHelperText>
                      )}
                    </FormControl>
                  )}
                />

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

              <Controller
                name="environment"
                control={control}
                render={({ field }) => (
                  <ToggleButtonGroup
                    exclusive
                    fullWidth
                    size="small"
                    value={field.value}
                    onChange={(_, value: CredentialEnvironment | null) => {
                      if (value) {
                        field.onChange(value);
                      }
                    }}
                    sx={{ mb: 2 }}
                  >
                    <ToggleButton
                      value="production"
                      sx={{
                        "&.Mui-selected": {
                          backgroundColor: "#059669",
                          color: "#fff",
                          "&:hover": { backgroundColor: "#047857" },
                        },
                      }}
                    >
                      Production
                    </ToggleButton>
                    <ToggleButton
                      value="sandbox"
                      sx={{
                        "&.Mui-selected": {
                          backgroundColor: "#C2410C",
                          color: "#fff",
                          "&:hover": { backgroundColor: "#9A3412" },
                        },
                      }}
                    >
                      Sandbox
                    </ToggleButton>
                  </ToggleButtonGroup>
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
          open={revokeTarget !== null}
          title="Revoke credential?"
          description={`The key for "${revokeTarget?.toolName ?? ""}" on "${revokeTarget?.teamName ?? ""}" will stop working immediately.`}
          dangerous
          confirmLabel="Revoke"
          loading={revokeMutation.isPending}
          onClose={() => setRevokeTarget(null)}
          onConfirm={() => {
            if (revokeTarget) {
              revokeMutation.mutate(revokeTarget.id);
            }
          }}
        />
      </Box>
    </RoleGuard>
  );
}

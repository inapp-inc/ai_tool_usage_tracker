import { zodResolver } from "@hookform/resolvers/zod";
import {
  IconMail,
  IconPencil,
  IconPlus,
  IconTrash,
  IconWebhook,
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
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, type SyntheticEvent } from "react";
import { Controller, useForm } from "react-hook-form";
import { useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import {
  acknowledgeAlert,
  createAlertRule,
  deleteAlertRule,
  fetchAlertHistory,
  fetchAlertRules,
  updateAlertRule,
  type AlertChannel,
  type AlertEvent,
  type AlertRule,
  type AlertSeverity,
  type ThresholdScope,
  type ThresholdType,
} from "@/api/alerts";
import { fetchMembers, type Member } from "@/api/members";
import { fetchTeams, type Team } from "@/api/teams";
import { fetchToolOptions } from "@/api/usage";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { formatCost, formatRelativeTime, formatTokens } from "@/utils/formatters";

const EMPTY_TEAMS: Team[] = [];
const EMPTY_MEMBERS: Member[] = [];
const EMPTY_TOOL_OPTIONS: Array<{ id: string; name: string }> = [];

const SEVERITY_CHIP_COLORS: Record<
  AlertSeverity,
  { background: string; color: string }
> = {
  critical: { background: "#FEE2E2", color: "#DC2626" },
  warning: { background: "#FEF9C3", color: "#A16207" },
  info: { background: "#EFF6FF", color: "#2563EB" },
};

const SEVERITY_DOT_COLORS: Record<AlertSeverity, string> = {
  critical: tokens.critical,
  warning: tokens.warning,
  info: "#3B82F6",
};

const SEVERITY_OPTIONS: Array<{ value: AlertSeverity; label: string }> = [
  { value: "critical", label: "Critical" },
  { value: "warning", label: "Warning" },
  { value: "info", label: "Info" },
];

const THRESHOLD_TYPE_OPTIONS: Array<{ value: ThresholdType; label: string }> = [
  { value: "token_count", label: "Token Count" },
  { value: "cost_usd", label: "Cost (USD)" },
  { value: "budget_percent", label: "Budget %" },
];

const SCOPE_OPTIONS: Array<{ value: ThresholdScope; label: string }> = [
  { value: "organization", label: "Organization" },
  { value: "team", label: "Group" },
  { value: "tool", label: "Team" },
  { value: "user", label: "User" },
];

function getScopeTargetMeta(scope: ThresholdScope): {
  label: string;
  placeholder: string;
} {
  switch (scope) {
    case "team":
      return { label: "Group", placeholder: "Select group" };
    case "tool":
      return { label: "Team", placeholder: "Select team" };
    case "user":
      return { label: "User", placeholder: "Select user" };
    default:
      return { label: "Target", placeholder: "" };
  }
}

const CHANNEL_OPTIONS: Array<{ value: AlertChannel; label: string }> = [
  { value: "email", label: "Email" },
  { value: "webhook", label: "Webhook" },
  { value: "both", label: "Both" },
];

const schema = z
  .object({
    name: z.string().min(1, "Name is required").max(100),
    severity: z.enum(["critical", "warning", "info"]),
    thresholdType: z.enum(["token_count", "cost_usd", "budget_percent"]),
    thresholdValue: z.coerce.number().positive("Must be greater than 0"),
    scope: z.enum(["organization", "team", "tool", "user"]),
    teamId: z.string().nullable(),
    channel: z.enum(["email", "webhook", "both"]),
    webhookUrl: z
      .union([z.string().url("Enter a valid URL"), z.literal("")])
      .nullable(),
    emailRecipients: z.string(),
  })
  .superRefine((data, ctx) => {
    if (data.scope === "team" && !data.teamId) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Group is required",
        path: ["teamId"],
      });
    }
    if (data.scope === "tool" && !data.teamId) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Team is required",
        path: ["teamId"],
      });
    }
    if (data.scope === "user" && !data.teamId) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "User is required",
        path: ["teamId"],
      });
    }
    if (
      (data.channel === "webhook" || data.channel === "both") &&
      !data.webhookUrl
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Webhook URL is required",
        path: ["webhookUrl"],
      });
    }
    if (
      (data.channel === "email" || data.channel === "both") &&
      !data.emailRecipients.trim()
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "At least one email is required",
        path: ["emailRecipients"],
      });
    }
  });

type FormValues = z.infer<typeof schema>;

interface SlideOverState {
  open: boolean;
  rule: AlertRule | null;
}

function formatThresholdDescription(rule: AlertRule): string {
  switch (rule.thresholdType) {
    case "token_count":
      return `Token count > ${formatTokens(rule.thresholdValue)}`;
    case "cost_usd":
      return `Cost > ${formatCost(rule.thresholdValue)}`;
    case "budget_percent":
      return `Budget usage > ${rule.thresholdValue}%`;
  }
}

function SeverityChip({ severity }: { severity: AlertSeverity }) {
  const colors = SEVERITY_CHIP_COLORS[severity];
  return (
    <Chip
      size="small"
      label={severity.charAt(0).toUpperCase() + severity.slice(1)}
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

function ChannelIcons({ channel }: { channel: AlertChannel }) {
  return (
    <Box sx={{ display: "inline-flex", alignItems: "center", gap: 0.5 }}>
      {(channel === "email" || channel === "both") && <IconMail size={14} />}
      {(channel === "webhook" || channel === "both") && (
        <IconWebhook size={14} />
      )}
    </Box>
  );
}

function getThresholdFieldMeta(thresholdType: ThresholdType): {
  label: string;
  helperText: string;
} {
  switch (thresholdType) {
    case "token_count":
      return {
        label: "Token count",
        helperText: "Alert when total tokens exceed this value",
      };
    case "cost_usd":
      return {
        label: "Cost (USD)",
        helperText: "Alert when spend exceeds this amount",
      };
    case "budget_percent":
      return {
        label: "Threshold (%)",
        helperText: "Percentage of monthly token or cost budget",
      };
  }
}

function parseEmailRecipients(value: string): string[] {
  return value
    .split(",")
    .map((email) => email.trim())
    .filter(Boolean);
}

function toFormValues(rule: AlertRule | null): FormValues {
  if (!rule) {
    return {
      name: "",
      severity: "warning",
      thresholdType: "token_count",
      thresholdValue: 1,
      scope: "organization",
      teamId: null,
      channel: "email",
      webhookUrl: "",
      emailRecipients: "",
    };
  }

  return {
    name: rule.name,
    severity: rule.severity,
    thresholdType: rule.thresholdType,
    thresholdValue: rule.thresholdValue,
    scope: rule.scope,
    teamId: rule.teamId,
    channel: rule.channel,
    webhookUrl: rule.webhookUrl ?? "",
    emailRecipients: rule.emailRecipients.join(", "),
  };
}

function resolveScopeTargetName(
  scope: ThresholdScope,
  targetId: string | null,
  groups: Team[],
  tools: Array<{ id: string; name: string }>,
  members: Member[],
): string | null {
  if (!targetId) {
    return null;
  }
  switch (scope) {
    case "team":
      return groups.find((group) => group.id === targetId)?.name ?? null;
    case "tool":
      return tools.find((tool) => tool.id === targetId)?.name ?? null;
    case "user":
      return members.find((member) => member.id === targetId)?.name ?? null;
    default:
      return null;
  }
}

function toRequestBody(
  data: FormValues,
  groups: Team[],
  tools: Array<{ id: string; name: string }>,
  members: Member[],
) {
  const teamId = data.scope === "organization" ? null : data.teamId;
  return {
    name: data.name,
    severity: data.severity,
    thresholdType: data.thresholdType,
    thresholdValue: data.thresholdValue,
    scope: data.scope,
    teamId,
    teamName: resolveScopeTargetName(data.scope, teamId, groups, tools, members),
    channel: data.channel,
    webhookUrl:
      data.webhookUrl && data.webhookUrl !== "" ? data.webhookUrl : null,
    emailRecipients: parseEmailRecipients(data.emailRecipients),
  };
}

export function AlertsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  const activeTab = location.pathname === "/alerts/history" ? 1 : 0;

  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    rule: null,
  });
  const [deleteTarget, setDeleteTarget] = useState<AlertRule | null>(null);
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const rulesQuery = useQuery({
    queryKey: ["alerts", "rules"],
    queryFn: fetchAlertRules,
  });

  const historyQuery = useQuery({
    queryKey: ["alerts", "history"],
    queryFn: fetchAlertHistory,
  });

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const toolOptionsQuery = useQuery({
    queryKey: ["tool-options"],
    queryFn: fetchToolOptions,
  });

  const membersQuery = useQuery({
    queryKey: ["members"],
    queryFn: fetchMembers,
  });

  const createMutation = useMutation({
    mutationFn: createAlertRule,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["alerts", "rules"] });
      setSlideOver({ open: false, rule: null });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: Parameters<typeof updateAlertRule>[1];
    }) => updateAlertRule(id, body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["alerts", "rules"] });
      setSlideOver({ open: false, rule: null });
    },
  });

  const statusToggleMutation = useMutation({
    mutationFn: ({
      id,
      status,
    }: {
      id: string;
      status: "active" | "inactive";
    }) => updateAlertRule(id, { status }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["alerts", "rules"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAlertRule,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["alerts", "rules"] });
      setDeleteTarget(null);
    },
  });

  const acknowledgeMutation = useMutation({
    mutationFn: acknowledgeAlert,
    onMutate: (id) => {
      setAcknowledgingId(id);
    },
    onSettled: () => {
      setAcknowledgingId(null);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["alerts", "history"] });
    },
  });

  const isEditMode = slideOver.rule !== null;
  const savePending = createMutation.isPending || updateMutation.isPending;
  const teams = teamsQuery.data ?? EMPTY_TEAMS;
  const toolOptions = toolOptionsQuery.data ?? EMPTY_TOOL_OPTIONS;
  const members = membersQuery.data ?? EMPTY_MEMBERS;

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: toFormValues(null),
  });

  const watchedChannel = watch("channel");
  const watchedScope = watch("scope");
  const watchedThresholdType = watch("thresholdType");
  const watchedThresholdValue = watch("thresholdValue");
  const thresholdFieldMeta = getThresholdFieldMeta(watchedThresholdType);
  const scopeTargetMeta = getScopeTargetMeta(watchedScope);

  const scopeTargetOptions = useMemo(() => {
    switch (watchedScope) {
      case "team":
        return teams.map((team) => ({ id: team.id, label: team.name }));
      case "tool":
        return toolOptions.map((tool) => ({ id: tool.id, label: tool.name }));
      case "user":
        return members.map((member) => ({
          id: member.id,
          label: member.name,
        }));
      default:
        return [];
    }
  }, [watchedScope, teams, toolOptions, members]);

  const showWebhookField =
    watchedChannel === "webhook" || watchedChannel === "both";
  const showEmailField =
    watchedChannel === "email" || watchedChannel === "both";
  const teamSelectDisabled = watchedScope === "organization";

  useEffect(() => {
    if (!slideOver.open) {
      reset(toFormValues(null));
      return;
    }
    reset(toFormValues(slideOver.rule));
  }, [reset, slideOver]);

  const ruleColumns: Column<AlertRule>[] = useMemo(
    () => [
      {
        key: "name",
        header: "Alert",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.name}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {formatThresholdDescription(row)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "severity",
        header: "Severity",
        render: (row) => <SeverityChip severity={row.severity} />,
      },
      {
        key: "scope",
        header: "Applies to",
        render: (row) => (
          <Typography variant="caption">
            {row.scope === "organization"
              ? "Organization"
              : (row.teamName ?? "—")}
          </Typography>
        ),
      },
      {
        key: "channel",
        header: "Channel",
        render: (row) => <ChannelIcons channel={row.channel} />,
      },
      {
        key: "triggerCount",
        header: "Triggered",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2">{row.triggerCount}</Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {row.lastTriggeredAt
                ? formatRelativeTime(row.lastTriggeredAt)
                : "Never"}
            </Typography>
          </Box>
        ),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => (
          <Switch
            size="small"
            checked={row.status === "active"}
            onChange={(event) => {
              event.stopPropagation();
              statusToggleMutation.mutate({
                id: row.id,
                status: event.target.checked ? "active" : "inactive",
              });
            }}
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
              aria-label={`Edit ${row.name}`}
              onClick={(event) => {
                event.stopPropagation();
                setSlideOver({ open: true, rule: row });
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
    [statusToggleMutation],
  );

  const historyColumns: Column<AlertEvent>[] = useMemo(
    () => [
      {
        key: "severity",
        header: "",
        render: (row) => (
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: SEVERITY_DOT_COLORS[row.severity],
              flexShrink: 0,
            }}
          />
        ),
      },
      {
        key: "ruleName",
        header: "Alert",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.ruleName}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {row.message}
            </Typography>
          </Box>
        ),
      },
      {
        key: "teamName",
        header: "Group",
        render: (row) => (
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {row.teamName ?? "Organization"}
          </Typography>
        ),
      },
      {
        key: "triggeredAt",
        header: "Triggered",
        sortable: true,
        render: (row) => formatRelativeTime(row.triggeredAt),
      },
      {
        key: "acknowledgedAt",
        header: "Acknowledged",
        render: (row) =>
          row.acknowledgedAt ? (
            <Box>
              <Typography variant="body2">
                {formatRelativeTime(row.acknowledgedAt)}
              </Typography>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                by {row.acknowledgedBy}
              </Typography>
            </Box>
          ) : (
            <Button
              size="small"
              variant="outlined"
              disabled={acknowledgingId === row.id}
              onClick={(event) => {
                event.stopPropagation();
                acknowledgeMutation.mutate(row.id);
              }}
              startIcon={
                acknowledgingId === row.id ? (
                  <CircularProgress size={12} />
                ) : undefined
              }
            >
              Acknowledge
            </Button>
          ),
      },
    ],
    [acknowledgeMutation, acknowledgingId],
  );

  const onSubmit = (data: FormValues) => {
    const body = toRequestBody(data, teams, toolOptions, members);
    if (slideOver.rule) {
      updateMutation.mutate({ id: slideOver.rule.id, body });
      return;
    }
    createMutation.mutate(body);
  };

  const handleTabChange = (_event: SyntheticEvent, newValue: number) => {
    navigate(newValue === 1 ? "/alerts/history" : "/alerts");
  };

  const rules = rulesQuery.data ?? [];
  const history = historyQuery.data ?? [];

  return (
    <RoleGuard
      roles={[Role.SuperAdmin, Role.TeamAdmin]}
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to manage alerts."
        />
      }
    >
      <Box>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            mb: 2,
          }}
        >
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Alerts
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Set thresholds and get notified when limits are hit
            </Typography>
          </Box>
          {activeTab === 0 && (
            <Button
              variant="contained"
              size="small"
              startIcon={<IconPlus size={15} />}
              onClick={() => setSlideOver({ open: true, rule: null })}
            >
              New Alert
            </Button>
          )}
        </Box>

        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          sx={{ mb: 2, borderBottom: `1px solid ${tokens.border}` }}
        >
          <Tab label="Alert Rules" />
          <Tab label="History" />
        </Tabs>

        {activeTab === 0 && rulesQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load alert rules. Please refresh.
          </Alert>
        )}

        {activeTab === 1 && historyQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load alert history. Please refresh.
          </Alert>
        )}

        {activeTab === 0 ? (
          <DataTable
            columns={ruleColumns}
            rows={rules}
            rowKey={(row) => row.id}
            loading={rulesQuery.isPending}
            emptyTitle="No alert rules yet"
            emptyDescription="Create your first alert to get notified when usage crosses a threshold."
          />
        ) : (
          <DataTable
            columns={historyColumns}
            rows={history}
            rowKey={(row) => row.id}
            loading={historyQuery.isPending}
            emptyTitle="No alerts triggered"
            emptyDescription="Triggered alerts will appear here when rules fire."
          />
        )}

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, rule: null })}
          title={isEditMode ? "Edit Alert" : "New Alert"}
          subtitle="Get notified when usage crosses a threshold"
          footer={
            <>
              <Button
                variant="text"
                onClick={() => setSlideOver({ open: false, rule: null })}
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
                {isEditMode ? "Save Changes" : "Create Alert"}
              </Button>
            </>
          }
        >
          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <TextField
              {...register("name")}
              label="Alert name"
              size="small"
              fullWidth
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
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
                name="severity"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth size="small">
                    <InputLabel id="alert-severity-label">Severity</InputLabel>
                    <Select
                      {...field}
                      labelId="alert-severity-label"
                      label="Severity"
                    >
                      {SEVERITY_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />

              <Controller
                name="thresholdType"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth size="small">
                    <InputLabel id="alert-threshold-type-label">
                      Threshold type
                    </InputLabel>
                    <Select
                      {...field}
                      labelId="alert-threshold-type-label"
                      label="Threshold type"
                    >
                      {THRESHOLD_TYPE_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />
            </Box>

            {watchedThresholdType === "budget_percent" && (
              <Box sx={{ display: "flex", gap: 1, mb: 1 }}>
                {[80, 90, 95].map((preset) => {
                  const isSelected = watchedThresholdValue === preset;
                  return (
                    <Chip
                      key={preset}
                      label={`${preset}%`}
                      size="small"
                      onClick={() =>
                        setValue("thresholdValue", preset, { shouldValidate: true })
                      }
                      sx={{
                        cursor: "pointer",
                        fontSize: "0.75rem",
                        fontWeight: isSelected ? 600 : 400,
                        backgroundColor: isSelected ? tokens.primary : tokens.bgDefault,
                        color: isSelected ? "#fff" : tokens.textMuted,
                        border: `0.5px solid ${isSelected ? tokens.primary : tokens.border}`,
                        "&:hover": {
                          backgroundColor: isSelected ? tokens.primary : "#E2E8F0",
                        },
                      }}
                    />
                  );
                })}
                <Typography
                  sx={{
                    fontSize: "0.75rem",
                    color: "text.secondary",
                    alignSelf: "center",
                    ml: 0.5,
                  }}
                >
                  or enter custom value below
                </Typography>
              </Box>
            )}

            <TextField
              {...register("thresholdValue", { valueAsNumber: true })}
              type="number"
              label={thresholdFieldMeta.label}
              size="small"
              fullWidth
              error={Boolean(errors.thresholdValue)}
              helperText={
                errors.thresholdValue?.message ?? thresholdFieldMeta.helperText
              }
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
                name="scope"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth size="small">
                    <InputLabel id="alert-scope-label">Scope</InputLabel>
                    <Select
                      {...field}
                      labelId="alert-scope-label"
                      label="Scope"
                      onChange={(event) => {
                        field.onChange(event);
                        setValue("teamId", null);
                      }}
                    >
                      {SCOPE_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />

              <Controller
                name="teamId"
                control={control}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={Boolean(errors.teamId)}
                    disabled={teamSelectDisabled}
                  >
                    <InputLabel id="alert-target-label">
                      {scopeTargetMeta.label}
                    </InputLabel>
                    <Select
                      {...field}
                      value={field.value ?? ""}
                      onChange={(event) => {
                        const value = event.target.value;
                        field.onChange(value === "" ? null : value);
                      }}
                      labelId="alert-target-label"
                      label={scopeTargetMeta.label}
                    >
                      <MenuItem value="">
                        <em>
                          {teamSelectDisabled ? "" : scopeTargetMeta.placeholder}
                        </em>
                      </MenuItem>
                      {scopeTargetOptions.map((option) => (
                        <MenuItem key={option.id} value={option.id}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.teamId && (
                      <Typography
                        variant="caption"
                        sx={{ color: tokens.critical, mt: 0.5, ml: 1.75 }}
                      >
                        {errors.teamId.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            </Box>

            <Controller
              name="channel"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel id="alert-channel-label">
                    Notification channel
                  </InputLabel>
                  <Select
                    {...field}
                    labelId="alert-channel-label"
                    label="Notification channel"
                  >
                    {CHANNEL_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />

            <Collapse in={showWebhookField}>
              <TextField
                {...register("webhookUrl")}
                label="Webhook URL"
                placeholder="https://..."
                size="small"
                fullWidth
                error={Boolean(errors.webhookUrl)}
                helperText={errors.webhookUrl?.message}
                sx={{ mb: 2 }}
              />
            </Collapse>

            <Collapse in={showEmailField}>
              <TextField
                {...register("emailRecipients")}
                label="Email recipients"
                placeholder="alice@co.com, bob@co.com"
                size="small"
                fullWidth
                error={Boolean(errors.emailRecipients)}
                helperText={
                  errors.emailRecipients?.message ?? "Comma-separated"
                }
                sx={{ mb: 2 }}
              />
            </Collapse>
          </Box>
        </SlideOver>

        <ConfirmDialog
          open={deleteTarget !== null}
          title="Delete alert rule?"
          description={`"${deleteTarget?.name ?? ""}" will be removed and will no longer trigger notifications.`}
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

import {
  Alert,
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  FormControl,
  FormHelperText,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { IconChevronDown, IconPencil, IconPlus, IconRefresh, IconTrash, IconUsers } from "@tabler/icons-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Link as RouterLink } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { emptyTeamToolPricing } from "@/api/adapters/teamTools";
import type { ToolPricing, ToolProvider } from "@/api/adapters/tools";
import { fetchTools } from "@/api/tools";
import { syncTeamToolAssignments, fetchTeamTools } from "@/api/teamTools";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { TeamToolDetailSlideOver } from "@/components/teams/TeamToolDetailSlideOver";
import { ToolPricingFields } from "@/components/tools/ToolPricingFields";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { formatCost, formatRelativeTime, formatTokens } from "@/utils/formatters";
import {
  createTeam,
  deleteTeam,
  fetchTeams,
  refreshTeamData,
  updateTeam,
  type Team,
} from "@/api/teams";
import { useToast } from "@/hooks/useToast";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  description: z.string().max(200),
  tokenBudget: z.number().int().positive().nullable(),
  costBudget: z.number().positive().nullable(),
  toolIds: z.array(z.string()),
});

type FormValues = z.infer<typeof schema>;

interface SlideOverState {
  open: boolean;
  team: Team | null;
}

interface ToolDetailState {
  open: boolean;
  team: Team | null;
  toolId: string | null;
  toolName: string;
}

function truncateDescription(text: string, maxLength = 60): string {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength)}…`;
}

function parseBudgetValue(value: unknown): number | null {
  if (value === "" || value == null) {
    return null;
  }
  const parsed = Number(value);
  if (Number.isNaN(parsed)) {
    return null;
  }
  return parsed;
}

function TeamToolsCell({
  team,
  toolIds,
  toolNameById,
  onToolClick,
}: {
  team: Team;
  toolIds: string[];
  toolNameById: Map<string, string>;
  onToolClick: (team: Team, toolId: string, toolName: string) => void;
}) {
  if (toolIds.length === 0) {
    return (
      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
        None assigned
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", alignItems: "center" }}>
      {toolIds.map((toolId) => {
        const toolName = toolNameById.get(toolId) ?? toolId;
        return (
          <Chip
            key={toolId}
            size="small"
            variant="outlined"
            label={toolName}
            clickable
            onClick={(event) => {
              event.stopPropagation();
              onToolClick(team, toolId, toolName);
            }}
            sx={{
              fontSize: "0.6875rem",
              height: 20,
              mr: 0.5,
              mb: 0.25,
              cursor: "pointer",
              "&:hover": {
                borderColor: tokens.primary,
                backgroundColor: tokens.bgDefault,
              },
            }}
          />
        );
      })}
    </Box>
  );
}

export function TeamsPage() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    team: null,
  });
  const [toolDetail, setToolDetail] = useState<ToolDetailState>({
    open: false,
    team: null,
    toolId: null,
    toolName: "",
  });
  const [deleteTarget, setDeleteTarget] = useState<Team | null>(null);
  const [toolPricingById, setToolPricingById] = useState<Record<string, ToolPricing>>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [assignmentsLoading, setAssignmentsLoading] = useState(false);
  const [syncingTeamId, setSyncingTeamId] = useState<string | null>(null);

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const catalogToolsQuery = useQuery({
    queryKey: ["tools", "catalog"],
    queryFn: () => fetchTools(),
  });

  const toolNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const tool of catalogToolsQuery.data ?? []) {
      map.set(tool.id, tool.name);
    }
    return map;
  }, [catalogToolsQuery.data]);

  const providerByToolId = useMemo(() => {
    const map = new Map<string, ToolProvider>();
    for (const tool of catalogToolsQuery.data ?? []) {
      map.set(tool.id, tool.provider);
    }
    return map;
  }, [catalogToolsQuery.data]);

  const toolOptions = useMemo(
    () =>
      (catalogToolsQuery.data ?? []).map((tool) => ({
        id: tool.id,
        name: tool.name,
      })),
    [catalogToolsQuery.data],
  );

  const createMutation = useMutation({
    mutationFn: createTeam,
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: Parameters<typeof updateTeam>[1];
    }) => updateTeam(id, body),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTeam,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      setDeleteTarget(null);
    },
  });

  const isEditMode = slideOver.team !== null;
  const savePending = createMutation.isPending || updateMutation.isPending;

  const {
    register,
    handleSubmit,
    reset,
    control,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      description: "",
      tokenBudget: null,
      costBudget: null,
      toolIds: [],
    },
  });

  useEffect(() => {
    if (!slideOver.open) {
      setToolPricingById({});
      setSaveError(null);
      return;
    }

    if (slideOver.team) {
      reset({
        name: slideOver.team.name,
        description: slideOver.team.description,
        tokenBudget: slideOver.team.tokenBudget,
        costBudget: slideOver.team.costBudget,
        toolIds: [...slideOver.team.toolIds],
      });

      setAssignmentsLoading(true);
      void fetchTeamTools(slideOver.team.id)
        .then((rows) => {
          const pricing: Record<string, ToolPricing> = {};
          for (const row of rows) {
            pricing[row.toolId] = row.pricing;
          }
          for (const toolId of slideOver.team!.toolIds) {
            if (!pricing[toolId]) {
              pricing[toolId] = emptyTeamToolPricing();
            }
          }
          setToolPricingById(pricing);
        })
        .finally(() => setAssignmentsLoading(false));
      return;
    }

    reset({
      name: "",
      description: "",
      tokenBudget: null,
      costBudget: null,
      toolIds: [],
    });
    setToolPricingById({});
  }, [reset, slideOver.open, slideOver.team?.id]);

  const handleToolClick = useCallback((team: Team, toolId: string, toolName: string) => {
    setToolDetail({ open: true, team, toolId, toolName });
  }, []);

  const handleRefreshTeam = useCallback(
    async (team: Team) => {
      setSyncingTeamId(team.id);
      try {
        const result = await refreshTeamData(team.id);
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ["teams"] }),
          queryClient.invalidateQueries({ queryKey: ["tools"] }),
          queryClient.invalidateQueries({ queryKey: ["tool-options"] }),
          queryClient.invalidateQueries({ queryKey: ["team-tool-assignment"] }),
          queryClient.invalidateQueries({ queryKey: ["team-tool-usage"] }),
        ]);

        if (result.syncedCount === 0 && result.failedCount === 0) {
          const skipped = result.results.filter((row) => row.status === "skipped");
          const detail =
            skipped.length > 0 && skipped[0].message
              ? skipped[0].message
              : result.skippedCount > 0
                ? "Connect credentials for this team's tools in Credentials first."
                : `${team.name} has no tools assigned.`;
          showToast(
            result.skippedCount > 0
              ? `No data collected — ${detail}`
              : detail,
            "info",
          );
          return;
        }

        if (result.failedCount > 0) {
          showToast(
            `Collected data for ${result.syncedCount} account(s); ${result.failedCount} failed.`,
            "warning",
          );
          return;
        }

        showToast(
          `Collected usage data for ${result.syncedCount} connected account(s) on ${team.name}.`,
          "success",
        );
      } catch {
        showToast(`Could not refresh data for ${team.name}. Please try again.`, "error");
      } finally {
        setSyncingTeamId(null);
      }
    },
    [queryClient, showToast],
  );

  const columns: Column<Team>[] = useMemo(
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
              {truncateDescription(row.description)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "memberCount",
        header: "Members",
        sortable: true,
        render: (row) => (
          <Box sx={{ display: "inline-flex", alignItems: "center", gap: 0.5 }}>
            <IconUsers size={13} />
            <Typography variant="body2">{row.memberCount}</Typography>
          </Box>
        ),
      },
      {
        key: "toolIds",
        header: "Tools",
        render: (row) => (
          <TeamToolsCell
            team={row}
            toolIds={row.toolIds}
            toolNameById={toolNameById}
            onToolClick={handleToolClick}
          />
        ),
      },
      {
        key: "tokensUsed",
        header: "Tokens used",
        sortable: true,
        render: (row) => (
          <Typography variant="body2">{formatTokens(row.tokensUsed)}</Typography>
        ),
      },
      {
        key: "pricingTotal",
        header: "Pricing total",
        sortable: true,
        render: (row) => (
          <Typography variant="body2">{formatCost(row.pricingTotal)}</Typography>
        ),
      },
      {
        key: "totalCost",
        header: "Total cost",
        sortable: true,
        render: (row) => (
          <Tooltip title="Sum of recorded usage cost this calendar month (UTC)">
            <Typography variant="body2">{formatCost(row.totalCost)}</Typography>
          </Tooltip>
        ),
      },
      {
        key: "lastSyncedAt",
        header: "Last synced",
        render: (row) => (
          <Typography variant="body2" sx={{ color: tokens.textMuted }}>
            {row.lastSyncedAt ? formatRelativeTime(row.lastSyncedAt) : "Never"}
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
            <Tooltip title="Refresh tool data from credentials">
              <span>
                <IconButton
                  size="small"
                  aria-label={`Refresh data for ${row.name}`}
                  disabled={syncingTeamId === row.id}
                  onClick={(event) => {
                    event.stopPropagation();
                    void handleRefreshTeam(row);
                  }}
                >
                  {syncingTeamId === row.id ? (
                    <CircularProgress size={14} />
                  ) : (
                    <IconRefresh size={15} />
                  )}
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title="View members">
              <IconButton
                size="small"
                component={RouterLink}
                to={`/admin/members?team=${encodeURIComponent(row.id)}`}
                aria-label={`View members of ${row.name}`}
                onClick={(event) => event.stopPropagation()}
              >
                <IconUsers size={15} />
              </IconButton>
            </Tooltip>
            <IconButton
              size="small"
              aria-label={`Edit ${row.name}`}
              onClick={(event) => {
                event.stopPropagation();
                setSlideOver({ open: true, team: row });
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
    [toolNameById, handleToolClick, handleRefreshTeam, syncingTeamId],
  );

  const onSubmit = async (data: FormValues) => {
    setSaveError(null);

    const assignments = data.toolIds.map((toolId) => ({
      toolId,
      pricing: toolPricingById[toolId] ?? emptyTeamToolPricing(),
      provider: providerByToolId.get(toolId) ?? "custom",
    }));

    try {
      if (slideOver.team) {
        await updateMutation.mutateAsync({ id: slideOver.team.id, body: data });
        await syncTeamToolAssignments(
          slideOver.team.id,
          assignments,
          slideOver.team.toolIds,
        );
      } else {
        const created = await createMutation.mutateAsync(data);
        await syncTeamToolAssignments(created.id, assignments, []);
      }

      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      setSlideOver({ open: false, team: null });
    } catch {
      setSaveError("Could not save team tool assignments. Please try again.");
    }
  };

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
              Organise members, tools, and usage by team
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              Usage columns reflect the current calendar month (imports + live sync)
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="small"
            startIcon={<IconPlus size={15} />}
            onClick={() => setSlideOver({ open: true, team: null })}
          >
            New Team
          </Button>
        </Box>

        {teamsQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load teams. Please refresh.
          </Alert>
        )}

        <DataTable
          columns={columns}
          rows={teamsQuery.data ?? []}
          rowKey={(row) => row.id}
          loading={teamsQuery.isPending}
          emptyTitle="No teams yet"
          emptyDescription="Create a team to organise members and track tool usage."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, team: null })}
          title={isEditMode ? "Edit Team" : "New Team"}
          subtitle={
            isEditMode
              ? "Update team configuration and tool pricing"
              : "Set budgets and configure per-tool pricing for this team"
          }
          width={560}
          footer={
            <>
              <Button
                variant="text"
                onClick={() => setSlideOver({ open: false, team: null })}
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
            key={slideOver.team?.id ?? "new-team"}
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
              label="Team name"
              size="small"
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
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
            />

            <Accordion defaultExpanded disableGutters elevation={0} sx={{ border: `0.5px solid ${tokens.border}` }}>
              <AccordionSummary expandIcon={<IconChevronDown size={16} />}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  Tools &amp; Pricing
                </Typography>
              </AccordionSummary>
              <AccordionDetails sx={{ pt: 0 }}>
                <Controller
                  name="toolIds"
                  control={control}
                  render={({ field }) => (
                    <FormControl
                      fullWidth
                      size="small"
                      error={Boolean(errors.toolIds)}
                      disabled={catalogToolsQuery.isPending}
                      sx={{ mb: 2 }}
                    >
                      <InputLabel id="team-tools-label">Assigned tools</InputLabel>
                      <Select
                        multiple
                        labelId="team-tools-label"
                        label="Assigned tools"
                        value={field.value}
                        onChange={(event) => {
                          const nextIds = event.target.value as string[];
                          field.onChange(nextIds);
                          setToolPricingById((previous) => {
                            const next = { ...previous };
                            for (const toolId of nextIds) {
                              if (!next[toolId]) {
                                next[toolId] = emptyTeamToolPricing();
                              }
                            }
                            return next;
                          });
                        }}
                        renderValue={(selected) => {
                          const names = (selected as string[])
                            .map((id) => toolNameById.get(id) ?? id)
                            .join(", ");
                          return (
                            <Typography noWrap sx={{ fontSize: "0.8125rem" }}>
                              {names || (catalogToolsQuery.isPending ? "Loading tools…" : "")}
                            </Typography>
                          );
                        }}
                      >
                        {toolOptions.map((tool) => (
                          <MenuItem key={tool.id} value={tool.id}>
                            <Checkbox
                              size="small"
                              checked={field.value.includes(tool.id)}
                              sx={{ mr: 1, p: 0 }}
                            />
                            {tool.name}
                          </MenuItem>
                        ))}
                      </Select>
                      {errors.toolIds ? (
                        <FormHelperText error>{errors.toolIds.message}</FormHelperText>
                      ) : (
                        <FormHelperText>
                          Select tools this team uses, then configure pricing for each below
                        </FormHelperText>
                      )}
                    </FormControl>
                  )}
                />

                {assignmentsLoading && (
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                    <CircularProgress size={14} />
                    <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                      Loading tool pricing…
                    </Typography>
                  </Box>
                )}

                {watch("toolIds").map((toolId) => (
                  <Accordion
                    key={toolId}
                    disableGutters
                    elevation={0}
                    sx={{
                      mb: 1,
                      border: `0.5px solid ${tokens.border}`,
                      "&:before": { display: "none" },
                    }}
                  >
                    <AccordionSummary expandIcon={<IconChevronDown size={14} />}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {toolNameById.get(toolId) ?? toolId}
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <ToolPricingFields
                        value={toolPricingById[toolId] ?? emptyTeamToolPricing()}
                        onChange={(pricing) =>
                          setToolPricingById((previous) => ({
                            ...previous,
                            [toolId]: pricing,
                          }))
                        }
                        disabled={assignmentsLoading || savePending}
                      />
                    </AccordionDetails>
                  </Accordion>
                ))}
              </AccordionDetails>
            </Accordion>

            <Typography
              variant="caption"
              sx={{
                color: tokens.textMuted,
                textTransform: "uppercase",
                mt: 2,
                mb: 1,
                display: "block",
              }}
            >
              Monthly budgets
            </Typography>

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 2,
              }}
            >
              <Controller
                name="tokenBudget"
                control={control}
                render={({ field }) => (
                  <TextField
                    fullWidth
                    label="Token limit"
                    size="small"
                    type="number"
                    placeholder="Unlimited"
                    value={field.value ?? ""}
                    onChange={(event) => {
                      field.onChange(parseBudgetValue(event.target.value));
                    }}
                    error={Boolean(errors.tokenBudget)}
                    helperText={errors.tokenBudget?.message}
                  />
                )}
              />
              <Controller
                name="costBudget"
                control={control}
                render={({ field }) => (
                  <TextField
                    fullWidth
                    label="Cost limit (USD)"
                    size="small"
                    type="number"
                    placeholder="Unlimited"
                    value={field.value ?? ""}
                    onChange={(event) => {
                      field.onChange(parseBudgetValue(event.target.value));
                    }}
                    error={Boolean(errors.costBudget)}
                    helperText={errors.costBudget?.message}
                  />
                )}
              />
            </Box>

            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              Leave blank for unlimited
            </Typography>
          </Box>
        </SlideOver>

        <TeamToolDetailSlideOver
          open={toolDetail.open}
          onClose={() =>
            setToolDetail({ open: false, team: null, toolId: null, toolName: "" })
          }
          team={toolDetail.team}
          toolId={toolDetail.toolId}
          toolName={toolDetail.toolName}
        />

        <ConfirmDialog
          open={deleteTarget !== null}
          title="Delete team?"
          description={`"${deleteTarget?.name ?? ""}" and all its budget configuration will be removed. Members will be unassigned. Usage history is preserved.`}
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

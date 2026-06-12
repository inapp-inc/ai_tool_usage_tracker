import { zodResolver } from "@hookform/resolvers/zod";
import { IconPencil, IconPlus, IconTrash, IconUsers } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  FormControl,
  FormHelperText,
  IconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import {
  createTeam,
  deleteTeam,
  fetchTeams,
  updateTeam,
  type Team,
} from "@/api/teams";
import { fetchToolOptions } from "@/api/usage";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { formatCost, formatTokens } from "@/utils/formatters";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  description: z.string().max(200),
  tokenBudget: z.number().int().positive().nullable(),
  costBudget: z.number().positive().nullable(),
  toolIds: z.array(z.string()).min(1, "Assign at least one tool"),
});

type FormValues = z.infer<typeof schema>;

interface SlideOverState {
  open: boolean;
  team: Team | null;
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
  toolIds,
  toolNameById,
}: {
  toolIds: string[];
  toolNameById: Map<string, string>;
}) {
  if (toolIds.length === 0) {
    return (
      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
        None assigned
      </Typography>
    );
  }

  const visibleIds =
    toolIds.length > 3 ? toolIds.slice(0, 2) : toolIds;
  const overflowCount = toolIds.length > 3 ? toolIds.length - 2 : 0;

  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", alignItems: "center" }}>
      {visibleIds.map((toolId) => (
        <Chip
          key={toolId}
          size="small"
          variant="outlined"
          label={toolNameById.get(toolId) ?? toolId}
          sx={{ fontSize: "0.6875rem", height: 20, mr: 0.5, mb: 0.25 }}
        />
      ))}
      {overflowCount > 0 && (
        <Chip
          size="small"
          variant="outlined"
          label={`+${overflowCount} more`}
          sx={{
            fontSize: "0.6875rem",
            height: 20,
            mr: 0.5,
            mb: 0.25,
            color: tokens.textMuted,
            borderColor: tokens.border,
          }}
        />
      )}
    </Box>
  );
}

function BudgetUsageBar({
  used,
  budget,
  formatValue,
}: {
  used: number;
  budget: number | null;
  formatValue: (value: number) => string;
}) {
  if (budget == null) {
    return (
      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
        Unlimited
      </Typography>
    );
  }

  const percent = Math.min((used / budget) * 100, 100);
  const color = percent >= 90 ? "error" : percent >= 70 ? "warning" : "primary";

  return (
    <Box>
      <LinearProgress
        variant="determinate"
        value={percent}
        color={color}
        sx={{ width: 80 }}
      />
      <Typography
        variant="caption"
        sx={{ color: tokens.textMuted, display: "block", mt: 0.5 }}
      >
        {formatValue(used)} / {formatValue(budget)}
      </Typography>
    </Box>
  );
}

export function TeamsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    team: null,
  });
  const [deleteTarget, setDeleteTarget] = useState<Team | null>(null);

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const toolOptionsQuery = useQuery({
    queryKey: ["tool-options"],
    queryFn: fetchToolOptions,
  });

  const toolNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const tool of toolOptionsQuery.data ?? []) {
      map.set(tool.id, tool.name);
    }
    return map;
  }, [toolOptionsQuery.data]);

  const toolOptions = toolOptionsQuery.data ?? [];

  const createMutation = useMutation({
    mutationFn: createTeam,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      setSlideOver({ open: false, team: null });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: Parameters<typeof updateTeam>[1];
    }) => updateTeam(id, body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      setSlideOver({ open: false, team: null });
    },
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
    watch,
    setValue,
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

  const selectedToolIds = watch("toolIds");

  useEffect(() => {
    if (!slideOver.open) {
      reset({
        name: "",
        description: "",
        tokenBudget: null,
        costBudget: null,
        toolIds: [],
      });
      return;
    }

    if (slideOver.team) {
      reset({
        name: slideOver.team.name,
        description: slideOver.team.description,
        tokenBudget: slideOver.team.tokenBudget,
        costBudget: slideOver.team.costBudget,
        toolIds: slideOver.team.toolIds,
      });
      return;
    }

    reset({
      name: "",
      description: "",
      tokenBudget: null,
      costBudget: null,
      toolIds: [],
    });
  }, [reset, slideOver]);

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
          <TeamToolsCell toolIds={row.toolIds} toolNameById={toolNameById} />
        ),
      },
      {
        key: "tokenBudget",
        header: "Token budget",
        render: (row) => (
          <BudgetUsageBar
            used={row.tokenUsedThisMonth}
            budget={row.tokenBudget}
            formatValue={formatTokens}
          />
        ),
      },
      {
        key: "costBudget",
        header: "Cost budget",
        render: (row) => (
          <BudgetUsageBar
            used={row.costUsedThisMonth}
            budget={row.costBudget}
            formatValue={formatCost}
          />
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
            <Tooltip title="View members">
              <IconButton
                size="small"
                aria-label={`View members of ${row.name}`}
                onClick={(event) => {
                  event.stopPropagation();
                  navigate(`/admin/members?team=${row.id}`);
                }}
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
    [navigate, toolNameById],
  );

  const onSubmit = (data: FormValues) => {
    if (slideOver.team) {
      updateMutation.mutate({ id: slideOver.team.id, body: data });
      return;
    }
    createMutation.mutate(data);
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
              Organise members and set usage budgets
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
          emptyDescription="Create a team to organise members and set usage budgets."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, team: null })}
          title={isEditMode ? "Edit Team" : "New Team"}
          subtitle={
            isEditMode
              ? "Update team configuration"
              : "Set a budget to receive alerts when thresholds are crossed"
          }
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
            component="form"
            onSubmit={handleSubmit(onSubmit)}
            sx={{ display: "flex", flexDirection: "column", gap: 2 }}
          >
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
              Tool access
            </Typography>

            <FormControl
              fullWidth
              size="small"
              error={Boolean(errors.toolIds)}
              disabled={toolOptionsQuery.isPending}
            >
              <InputLabel id="team-tools-label">Assigned tools</InputLabel>
              <Select
                multiple
                labelId="team-tools-label"
                label="Assigned tools"
                value={selectedToolIds}
                onChange={(event) => {
                  setValue("toolIds", event.target.value as string[], {
                    shouldValidate: true,
                  });
                }}
                renderValue={(selected) => {
                  const names = (selected as string[])
                    .map((id) => toolNameById.get(id) ?? id)
                    .join(", ");
                  return (
                    <Typography noWrap sx={{ fontSize: "0.8125rem" }}>
                      {names || (toolOptionsQuery.isPending ? "Loading tools…" : "")}
                    </Typography>
                  );
                }}
              >
                {toolOptions.map((tool) => (
                  <MenuItem key={tool.id} value={tool.id}>
                    <Checkbox
                      size="small"
                      checked={selectedToolIds.includes(tool.id)}
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
                  Members of this team will only be tracked against these tools
                </FormHelperText>
              )}
            </FormControl>

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
              <TextField
                {...register("tokenBudget", {
                  setValueAs: parseBudgetValue,
                })}
                fullWidth
                label="Token limit"
                size="small"
                type="number"
                placeholder="Unlimited"
                error={Boolean(errors.tokenBudget)}
                helperText={errors.tokenBudget?.message}
              />
              <TextField
                {...register("costBudget", {
                  setValueAs: parseBudgetValue,
                })}
                fullWidth
                label="Cost limit (USD)"
                size="small"
                type="number"
                placeholder="Unlimited"
                error={Boolean(errors.costBudget)}
                helperText={errors.costBudget?.message}
              />
            </Box>

            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              Leave blank for unlimited
            </Typography>
          </Box>
        </SlideOver>

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

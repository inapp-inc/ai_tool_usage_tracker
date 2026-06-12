import { zodResolver } from "@hookform/resolvers/zod";
import {
  IconPencil,
  IconPlus,
  IconSearch,
  IconUserMinus,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  ListItemText,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useSearchParams } from "react-router-dom";
import { z } from "zod";

import {
  fetchMembers,
  fetchMembersByTeam,
  inviteMember,
  removeMember,
  updateMember,
  type Member,
} from "@/api/members";
import { fetchTeams } from "@/api/teams";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { formatRelativeTime } from "@/utils/formatters";

const schema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  email: z.string().email("Enter a valid email"),
  platformRole: z.nativeEnum(Role),
  teamIds: z.array(z.string()).min(1, "Assign at least one team"),
});

type FormValues = z.infer<typeof schema>;

interface SlideOverState {
  open: boolean;
  member: Member | null;
}

const ROLE_CHIP_COLORS: Record<
  Role,
  { background: string; color: string }
> = {
  [Role.SuperAdmin]: { background: "#EDE9FE", color: "#7C3AED" },
  [Role.TeamAdmin]: { background: "#EFF6FF", color: "#2563EB" },
  [Role.FinanceViewer]: { background: "#ECFDF5", color: "#059669" },
  [Role.TeamMember]: { background: tokens.bgDefault, color: tokens.textMuted },
  [Role.Auditor]: { background: "#FFF7ED", color: "#C2410C" },
};

const ROLE_OPTIONS = Object.values(Role);

function formatRoleLabel(role: Role): string {
  return role
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function RoleChip({ role }: { role: Role }) {
  const colors = ROLE_CHIP_COLORS[role];
  return (
    <Chip
      size="small"
      label={formatRoleLabel(role)}
      sx={{
        backgroundColor: colors.background,
        color: colors.color,
        fontWeight: 500,
        "& .MuiChip-label": { px: 1 },
      }}
    />
  );
}

export function MembersPage() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    member: null,
  });
  const [removeTarget, setRemoveTarget] = useState<Member | null>(null);

  const teamFilter = searchParams.get("team") ?? "";

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const membersQuery = useQuery({
    queryKey: teamFilter
      ? ["members", "team", teamFilter]
      : ["members"],
    queryFn: () =>
      teamFilter ? fetchMembersByTeam(teamFilter) : fetchMembers(),
  });

  const createMutation = useMutation({
    mutationFn: inviteMember,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["members"] });
      setSlideOver({ open: false, member: null });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: Parameters<typeof updateMember>[1];
    }) => updateMember(id, body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["members"] });
      setSlideOver({ open: false, member: null });
    },
  });

  const removeMutation = useMutation({
    mutationFn: removeMember,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["members"] });
      setRemoveTarget(null);
    },
  });

  const isEditMode = slideOver.member !== null;
  const savePending = createMutation.isPending || updateMutation.isPending;

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      email: "",
      platformRole: Role.TeamMember,
      teamIds: [],
    },
  });

  useEffect(() => {
    if (!slideOver.open) {
      reset({
        name: "",
        email: "",
        platformRole: Role.TeamMember,
        teamIds: teamFilter ? [teamFilter] : [],
      });
      return;
    }

    if (slideOver.member) {
      reset({
        name: slideOver.member.name,
        email: slideOver.member.email,
        platformRole: slideOver.member.platformRole,
        teamIds: slideOver.member.teams.map((team) => team.id),
      });
      return;
    }

    reset({
      name: "",
      email: "",
      platformRole: Role.TeamMember,
      teamIds: teamFilter ? [teamFilter] : [],
    });
  }, [reset, slideOver, teamFilter]);

  const filteredMembers = useMemo(() => {
    const members = membersQuery.data ?? [];
    const query = search.trim().toLowerCase();
    if (!query) {
      return members;
    }
    return members.filter(
      (member) =>
        member.name.toLowerCase().includes(query) ||
        member.email.toLowerCase().includes(query),
    );
  }, [membersQuery.data, search]);

  const teams = teamsQuery.data ?? [];

  const columns: Column<Member>[] = useMemo(
    () => [
      {
        key: "name",
        header: "Member",
        sortable: true,
        render: (row) => (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.25 }}>
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                backgroundColor: "#1E3A5F",
                color: "#60A5FA",
                fontSize: 11,
                fontWeight: 500,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              {getInitials(row.name)}
            </Box>
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {row.name}
              </Typography>
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {row.email}
              </Typography>
            </Box>
          </Box>
        ),
      },
      {
        key: "platformRole",
        header: "Role",
        render: (row) => <RoleChip role={row.platformRole} />,
      },
      {
        key: "teams",
        header: "Teams",
        render: (row) => (
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
            {row.teams.slice(0, 2).map((team) => (
              <Chip key={team.id} size="small" label={team.name} />
            ))}
            {row.teams.length > 2 && (
              <Chip size="small" label={`+${row.teams.length - 2} more`} />
            )}
          </Box>
        ),
      },
      {
        key: "lastActiveAt",
        header: "Last active",
        render: (row) =>
          row.lastActiveAt ? (
            formatRelativeTime(row.lastActiveAt)
          ) : (
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              Never
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
                setSlideOver({ open: true, member: row });
              }}
            >
              <IconPencil size={15} />
            </IconButton>
            <IconButton
              size="small"
              aria-label={`Remove ${row.name}`}
              onClick={(event) => {
                event.stopPropagation();
                setRemoveTarget(row);
              }}
              sx={{ color: tokens.critical }}
            >
              <IconUserMinus size={15} />
            </IconButton>
          </Box>
        ),
      },
    ],
    [],
  );

  const handleTeamFilterChange = (value: string) => {
    if (value) {
      setSearchParams({ team: value });
      return;
    }
    setSearchParams({});
  };

  const onSubmit = (data: FormValues) => {
    if (slideOver.member) {
      updateMutation.mutate({
        id: slideOver.member.id,
        body: {
          name: data.name,
          platformRole: data.platformRole,
          teamIds: data.teamIds,
        },
      });
      return;
    }

    createMutation.mutate({
      name: data.name,
      email: data.email,
      platformRole: data.platformRole,
      teamIds: data.teamIds,
    });
  };

  return (
    <RoleGuard
      roles={[Role.SuperAdmin]}
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to manage members."
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
              Members
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Manage user access and role assignments
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="small"
            startIcon={<IconPlus size={15} />}
            onClick={() => setSlideOver({ open: true, member: null })}
          >
            Invite Member
          </Button>
        </Box>

        <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
          <TextField
            size="small"
            placeholder="Search by name or email…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            sx={{ width: 260 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <IconSearch size={15} />
                  </InputAdornment>
                ),
              },
            }}
          />

          <FormControl size="small" sx={{ width: 200 }}>
            <Select
              value={teamFilter}
              onChange={(event) =>
                handleTeamFilterChange(event.target.value as string)
              }
              displayEmpty
            >
              <MenuItem value="">All teams</MenuItem>
              {teams.map((team) => (
                <MenuItem key={team.id} value={team.id}>
                  {team.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {membersQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load members. Please refresh.
          </Alert>
        )}

        <DataTable
          columns={columns}
          rows={filteredMembers}
          rowKey={(row) => row.id}
          loading={membersQuery.isPending}
          emptyTitle="No members found"
          emptyDescription="Invite a member or adjust your search filters."
        />

        <SlideOver
          open={slideOver.open}
          onClose={() => setSlideOver({ open: false, member: null })}
          title={isEditMode ? "Edit Member" : "Invite Member"}
          subtitle={
            isEditMode
              ? "Update role and team assignments"
              : "They'll receive an email with login instructions"
          }
          footer={
            <>
              <Button
                variant="text"
                onClick={() => setSlideOver({ open: false, member: null })}
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
              label="Full name"
              size="small"
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
            />

            <TextField
              {...register("email")}
              fullWidth
              label="Email address"
              size="small"
              type="email"
              disabled={isEditMode}
              error={Boolean(errors.email)}
              helperText={errors.email?.message}
            />

            <Controller
              name="platformRole"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="member-role-label">Platform role</InputLabel>
                  <Select
                    {...field}
                    labelId="member-role-label"
                    label="Platform role"
                  >
                    {ROLE_OPTIONS.map((role) => (
                      <MenuItem key={role} value={role}>
                        {formatRoleLabel(role)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />

            <Controller
              name="teamIds"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small" error={Boolean(errors.teamIds)}>
                  <InputLabel id="member-teams-label">Teams</InputLabel>
                  <Select
                    {...field}
                    multiple
                    labelId="member-teams-label"
                    label="Teams"
                    renderValue={(selected) =>
                      teams
                        .filter((team) => selected.includes(team.id))
                        .map((team) => team.name)
                        .join(", ")
                    }
                  >
                    {teams.map((team) => (
                      <MenuItem key={team.id} value={team.id}>
                        <Checkbox checked={field.value.includes(team.id)} />
                        <ListItemText primary={team.name} />
                      </MenuItem>
                    ))}
                  </Select>
                  {errors.teamIds?.message && (
                    <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                      {errors.teamIds.message}
                    </Typography>
                  )}
                </FormControl>
              )}
            />
          </Box>
        </SlideOver>

        <ConfirmDialog
          open={removeTarget !== null}
          title="Remove member?"
          description={`${removeTarget?.name ?? ""} will lose access immediately. Their usage history is preserved.`}
          dangerous
          confirmLabel="Remove"
          loading={removeMutation.isPending}
          onClose={() => setRemoveTarget(null)}
          onConfirm={() => {
            if (removeTarget) {
              removeMutation.mutate(removeTarget.id);
            }
          }}
        />
      </Box>
    </RoleGuard>
  );
}

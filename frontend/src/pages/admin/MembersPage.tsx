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
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  ListItemText,
  MenuItem,
  Select,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { useSearchParams } from "react-router-dom";
import { z } from "zod";

import { fetchMembers,
  fetchMembersByTeam,
  inviteMember,
  removeMember,
  updateMember,
  type InviteMemberResult,
  type Member,
} from "@/api/members";
import { fetchOrganizations } from "@/api/organizations";
import { fetchRoles } from "@/api/roles";
import { fetchTeams } from "@/api/teams";
import { formatRoleLabel, isOrgAdminRoleId, isOrgWideRoleName, roleRequiresTeamAssignment } from "@/api/adapters/formatRoleLabel";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SlideOver } from "@/components/layout/SlideOver";
import { Role } from "@/types";
import { useAuthStore } from "@/stores/authStore";
import { useOrgScopeStore } from "@/stores/orgScopeStore";
import { tenantScopeKey } from "@/lib/tenantScope";
import { tokens } from "@/theme/palette";
import { formatRelativeTime } from "@/utils/formatters";

const baseSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  email: z.string().email("Enter a valid email"),
  roleId: z.string().min(1, "Role is required"),
  password: z.string().optional(),
  teamIds: z.array(z.string()),
  organizationId: z.string().optional(),
  organizationName: z.string().optional(),
});

type FormValues = z.infer<typeof baseSchema>;

interface SlideOverState {
  open: boolean;
  member: Member | null;
}

const ROLE_CHIP_COLORS: Record<
  Role,
  { background: string; color: string }
> = {
  [Role.SuperAdmin]: { background: "#EDE9FE", color: "#7C3AED" },
  [Role.OrgAdmin]: { background: "#F5F3FF", color: "#5B21B6" },
  [Role.TeamAdmin]: { background: "#EFF6FF", color: "#2563EB" },
  [Role.FinanceViewer]: { background: "#ECFDF5", color: "#059669" },
  [Role.TeamMember]: { background: tokens.bgDefault, color: tokens.textMuted },
  [Role.Auditor]: { background: "#FFF7ED", color: "#C2410C" },
};

function formatRoleLabelFromEnum(role: Role | string): string {
  return formatRoleLabel(String(role));
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
      label={formatRoleLabelFromEnum(role)}
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
  const currentUser = useAuthStore((s) => s.user);
  const isSuperAdmin = currentUser?.platformRole === Role.SuperAdmin;
  const isOrgAdmin = currentUser?.platformRole === Role.OrgAdmin;
  const isPlatformOrg =
    currentUser?.organizationSlug === "platform" ||
    currentUser?.organizationSlug === "default";
  const selectedOrganizationId = useOrgScopeStore((s) => s.selectedOrganizationId);
  const setSelectedOrganizationId = useOrgScopeStore((s) => s.setSelectedOrganizationId);
  const canManageRoles = isSuperAdmin || isOrgAdmin;
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const [slideOver, setSlideOver] = useState<SlideOverState>({
    open: false,
    member: null,
  });
  const [removeTarget, setRemoveTarget] = useState<Member | null>(null);
  const [inviteResult, setInviteResult] = useState<InviteMemberResult | null>(null);
  const [copied, setCopied] = useState(false);

  const teamFilter = searchParams.get("team") ?? "";
  const invitedFilter = searchParams.get("filter") === "invited";
  const filterValue = teamFilter || (invitedFilter ? "__invited__" : "");

  const orgScopeKey = tenantScopeKey(currentUser, selectedOrganizationId);
  const tenantAdminRequiresOrg = isSuperAdmin && !selectedOrganizationId;

  const organizationsQuery = useQuery({
    queryKey: ["organizations"],
    queryFn: fetchOrganizations,
    enabled: isSuperAdmin,
  });

  const teamsQuery = useQuery({
    queryKey: ["teams", orgScopeKey],
    queryFn: fetchTeams,
    enabled: !tenantAdminRequiresOrg,
  });

  const membersQuery = useQuery({
    queryKey: teamFilter
      ? ["members", "team", teamFilter, orgScopeKey]
      : invitedFilter
        ? ["members", "invited", orgScopeKey]
        : ["members", "all", orgScopeKey],
    queryFn: () => {
      if (teamFilter) {
        return fetchMembersByTeam(teamFilter);
      }
      if (invitedFilter) {
        return fetchMembers("invited");
      }
      return fetchMembers("all");
    },
    enabled: !tenantAdminRequiresOrg,
  });

  const createMutation = useMutation({
    mutationFn: inviteMember,
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ["members"] });
      await queryClient.invalidateQueries({ queryKey: ["organizations"] });
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      await queryClient.invalidateQueries({ queryKey: ["roles"] });
      if (result.organizationId) {
        setSelectedOrganizationId(result.organizationId);
      }
      setSlideOver({ open: false, member: null });
      if (result.temporaryPassword) {
        setInviteResult(result);
        setCopied(false);
      }
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
    setValue,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(
      baseSchema.superRefine((data, ctx) => {
        if (data.password && data.password.length > 0 && data.password.length < 8) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: "Password must be at least 8 characters",
            path: ["password"],
          });
        }
      }),
    ),
    defaultValues: {
      name: "",
      email: "",
      roleId: "",
      password: "",
      teamIds: [],
      organizationId: "",
      organizationName: "",
    },
  });

  const watchedRoleId = useWatch({ control, name: "roleId" }) ?? "";
  const watchedOrganizationId = useWatch({ control, name: "organizationId" }) ?? "";
  const inviteTargetOrgId = isSuperAdmin
    ? watchedOrganizationId || selectedOrganizationId || ""
    : "";

  const rolesQuery = useQuery({
    queryKey: ["roles", inviteTargetOrgId || orgScopeKey, slideOver.open ? "invite" : "idle"],
    queryFn: () =>
      fetchRoles(isSuperAdmin ? inviteTargetOrgId || selectedOrganizationId : undefined),
    enabled: canManageRoles && slideOver.open,
  });

  const availableRoles = useMemo(() => {
    let roles = rolesQuery.data ?? [];
    roles = roles.filter((role) => {
      if (!isSuperAdmin && role.name === Role.SuperAdmin) {
        return false;
      }
      if (!isSuperAdmin && isPlatformOrg && role.name === Role.OrgAdmin) {
        return false;
      }
      return true;
    });
    if (isSuperAdmin && !isEditMode && !roles.some((role) => role.name === Role.OrgAdmin)) {
      roles = [
        {
          id: Role.OrgAdmin,
          name: Role.OrgAdmin,
          description: "Organization administrator",
          is_system: true,
          created_at: "",
        },
        ...roles,
      ];
    }
    return roles;
  }, [isSuperAdmin, isPlatformOrg, isEditMode, rolesQuery.data]);

  const isOrgAdminRoleSelected = useMemo(
    () => isOrgAdminRoleId(watchedRoleId, availableRoles),
    [availableRoles, watchedRoleId],
  );
  const needsInviteOrgSelection =
    isSuperAdmin &&
    !isEditMode &&
    !selectedOrganizationId &&
    !watchedOrganizationId &&
    !isOrgAdminRoleSelected;
  const needsOrgNameForOrgAdmin =
    isSuperAdmin && !isEditMode && isOrgAdminRoleSelected && !inviteTargetOrgId;

  const showTeamSelection = roleRequiresTeamAssignment(watchedRoleId, availableRoles);
  const isEditingSuperAdmin =
    isEditMode && slideOver.member?.platformRole === Role.SuperAdmin;
  const teamAdminRoleOptions = useMemo(
    () => [Role.TeamMember, Role.TeamAdmin],
    [],
  );

  useEffect(() => {
    if (!slideOver.open) {
      reset({
        name: "",
        email: "",
        roleId: "",
        password: "",
        teamIds: [],
        organizationId: selectedOrganizationId ?? "",
        organizationName: "",
      });
    }
  }, [reset, selectedOrganizationId, slideOver.open]);

  useEffect(() => {
    if (!slideOver.open) {
      return;
    }

    if (slideOver.member) {
      const matchedRoleId = availableRoles.find(
        (r) => r.name === slideOver.member!.platformRole,
      )?.id;
      reset({
        name: slideOver.member.name,
        email: slideOver.member.email,
        roleId: matchedRoleId ?? slideOver.member.platformRole,
        password: "",
        teamIds: slideOver.member.teams.map((team) => team.id),
      });
      return;
    }

    const defaultRoleId =
      availableRoles.find((r) => r.name === "team_member")?.id ?? Role.TeamMember;
    reset({
      name: "",
      email: "",
      roleId: defaultRoleId,
      password: "",
      teamIds: teamFilter ? [teamFilter] : [],
      organizationId: selectedOrganizationId ?? "",
      organizationName: "",
    });
  }, [reset, slideOver.open, slideOver.member, teamFilter, availableRoles, selectedOrganizationId]);

  const inviteTargetOrgName = useMemo(() => {
    if (!inviteTargetOrgId) {
      return null;
    }
    return (organizationsQuery.data ?? []).find((org) => org.id === inviteTargetOrgId)?.name ?? null;
  }, [inviteTargetOrgId, organizationsQuery.data]);

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
  const inviteTeams = useMemo(() => {
    if (!isSuperAdmin || !inviteTargetOrgId) {
      return teams;
    }
    return teams.filter((team) => team.organizationId === inviteTargetOrgId);
  }, [inviteTargetOrgId, isSuperAdmin, teams]);
  const activeTeam = teams.find((team) => team.id === teamFilter);

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
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {row.name}
                </Typography>
                {row.source === "tool" && (
                  <Chip
                    size="small"
                    label={row.toolName ? `Tool · ${row.toolName}` : "Tool member"}
                    sx={{ height: 18, fontSize: "0.625rem" }}
                  />
                )}
                {row.source === "upload" && (
                  <Chip
                    size="small"
                    label="File import"
                    sx={{ height: 18, fontSize: "0.625rem" }}
                  />
                )}
              </Box>
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
        render: (row) =>
          row.source === "tool" || row.source === "upload" ? (
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              —
            </Typography>
          ) : (
            <RoleChip role={row.platformRole} />
          ),
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
            {row.source === "platform" && row.platformRole !== Role.SuperAdmin && (
              <>
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
              </>
            )}
          </Box>
        ),
      },
    ],
    [],
  );

  const handleFilterChange = (value: string) => {
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      next.delete("team");
      next.delete("filter");
      if (value === "__invited__") {
        next.set("filter", "invited");
      } else if (value) {
        next.set("team", value);
      }
      return next;
    });
  };

  const onSubmit = (data: FormValues) => {
    const isOrgAdminInvite = isSuperAdmin && !isEditMode && isOrgAdminRoleSelected;

    if (needsOrgNameForOrgAdmin && !data.organizationName?.trim()) {
      setError("organizationName", {
        type: "manual",
        message: "Organization name is required for Organization Admin",
      });
      return;
    }

    if (
      isSuperAdmin &&
      !isEditMode &&
      !isOrgAdminInvite &&
      !selectedOrganizationId &&
      !data.organizationId?.trim()
    ) {
      setValue("organizationId", "", { shouldValidate: true });
      return;
    }

    const teamIds = showTeamSelection ? data.teamIds : [];
    if (showTeamSelection && teamIds.length === 0) {
      setValue("teamIds", [], { shouldValidate: true });
      return;
    }

    const isRoleUuid = /^[0-9a-f-]{36}$/i.test(data.roleId);
    const updateBody = isRoleUuid
      ? { name: data.name, roleId: data.roleId, teamIds }
      : {
          name: data.name,
          platformRole: data.roleId as Role,
          teamIds,
        };

    if (isEditMode && slideOver.member) {
      updateMutation.mutate({
        id: slideOver.member.id,
        body: updateBody,
      });
      return;
    }

    const organizationId = data.organizationId?.trim() || selectedOrganizationId || undefined;
    const organizationName =
      isOrgAdminInvite && !organizationId ? data.organizationName?.trim() : undefined;

    if (isOrgAdminInvite && !isRoleUuid) {
      createMutation.mutate({
        name: data.name,
        email: data.email,
        platformRole: Role.OrgAdmin,
        password: data.password?.trim() || undefined,
        teamIds: [],
        organizationId,
        organizationName,
      });
      return;
    }

    const createBody = isRoleUuid
      ? {
          name: data.name,
          email: data.email,
          roleId: data.roleId,
          password: data.password?.trim() || undefined,
          teamIds,
          organizationId,
        }
      : {
          name: data.name,
          email: data.email,
          platformRole: data.roleId as Role,
          password: data.password?.trim() || undefined,
          teamIds,
          organizationId,
        };

    createMutation.mutate(createBody);
  };

  return (
    <RoleGuard
      resource="members"
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to manage members."
        />
      }
    >
      <Box>
        {tenantAdminRequiresOrg && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Select a customer organization in the header to manage members for that
            tenant only. Without a selection, member lists combine all organizations.
          </Alert>
        )}
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
              {activeTeam
                ? `Showing members for ${activeTeam.name}`
                : invitedFilter
                  ? "Manually invited platform members"
                  : "All platform and tool members across teams"}
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

          <FormControl size="small" sx={{ width: 220 }}>
            <Select
              value={filterValue}
              onChange={(event) =>
                handleFilterChange(event.target.value as string)
              }
              displayEmpty
            >
              <MenuItem value="">All teams</MenuItem>
              <MenuItem value="__invited__">Invited members</MenuItem>
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
              ? isEditingSuperAdmin
                ? "Super Admin accounts cannot be modified"
                : "Update role and team assignments"
              : "Set login credentials and role"
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
                disabled={savePending || isEditingSuperAdmin}
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

            {needsOrgNameForOrgAdmin && (
              <TextField
                {...register("organizationName")}
                fullWidth
                label="Organization name"
                size="small"
                error={Boolean(errors.organizationName)}
                helperText={
                  errors.organizationName?.message ??
                  "Creates a new customer organization if this name does not exist"
                }
              />
            )}

            {needsInviteOrgSelection && (
              <Controller
                name="organizationId"
                control={control}
                rules={{ required: "Select an organization" }}
                render={({ field }) => (
                  <FormControl fullWidth size="small" error={Boolean(errors.organizationId)}>
                    <InputLabel id="member-org-label">Organization</InputLabel>
                    <Select
                      {...field}
                      labelId="member-org-label"
                      label="Organization"
                      value={field.value ?? ""}
                      onChange={(event) => {
                        field.onChange(event.target.value);
                        setValue("roleId", "", { shouldValidate: true });
                        setValue("teamIds", [], { shouldValidate: true });
                      }}
                    >
                      {(organizationsQuery.data ?? []).map((org) => (
                        <MenuItem key={org.id} value={org.id}>
                          {org.name}
                        </MenuItem>
                      ))}
                    </Select>
                    <Typography variant="caption" sx={{ color: tokens.textMuted, mt: 0.5 }}>
                      Choose the customer organization, or select one from the header first.
                    </Typography>
                  </FormControl>
                )}
              />
            )}

            {isSuperAdmin && !isEditMode && isOrgAdminRoleSelected && inviteTargetOrgName && (
              <Alert severity="info">
                Inviting Organization Admin into {inviteTargetOrgName}. Select a different
                organization from the header to change the target.
              </Alert>
            )}

            {isSuperAdmin && !isEditMode && needsOrgNameForOrgAdmin && (
              <Alert severity="info">
                Enter the customer organization name. A new tenant is created automatically if
                the name does not already exist.
              </Alert>
            )}

            {isSuperAdmin && !isEditMode && inviteTargetOrgName && !isOrgAdminRoleSelected && !needsInviteOrgSelection && (
              <Alert severity="info">
                Inviting into {inviteTargetOrgName}. Change organization from the header dropdown
                if needed.
              </Alert>
            )}

            {isPlatformOrg && !isSuperAdmin && !isEditMode && (
              <Alert severity="info">
                Organization Admin accounts belong to a customer organization. On this platform
                account, invite Team Admin or Team Member roles.
              </Alert>
            )}

            <Controller
              name="roleId"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="member-role-label">Platform role</InputLabel>
                  {canManageRoles ? (
                    <Select
                      {...field}
                      labelId="member-role-label"
                      label="Platform role"
                      disabled={
                        isEditingSuperAdmin ||
                        rolesQuery.isLoading ||
                        (!rolesQuery.isLoading && availableRoles.length === 0)
                      }
                      onChange={(event) => {
                        const nextRoleId = event.target.value as string;
                        field.onChange(nextRoleId);
                        if (!roleRequiresTeamAssignment(nextRoleId, availableRoles)) {
                          setValue("teamIds", [], { shouldValidate: true });
                        }
                        if (isOrgAdminRoleId(nextRoleId, availableRoles)) {
                          setValue("organizationId", "", { shouldValidate: true });
                        }
                      }}
                    >
                      {rolesQuery.isLoading ? (
                        <MenuItem value="" disabled>
                          Loading roles…
                        </MenuItem>
                      ) : (
                        availableRoles.map((role) => (
                          <MenuItem key={role.id} value={role.id}>
                            {formatRoleLabel(role.name)}
                          </MenuItem>
                        ))
                      )}
                    </Select>
                  ) : (
                    <Select
                      value={field.value}
                      labelId="member-role-label"
                      label="Platform role"
                      onChange={(event) => {
                        const roleName = event.target.value;
                        const matched = availableRoles.find((r) => r.name === roleName);
                        const nextRoleId = matched?.id ?? roleName;
                        field.onChange(nextRoleId);
                        if (isOrgWideRoleName(roleName)) {
                          setValue("teamIds", [], { shouldValidate: true });
                        }
                      }}
                    >
                      {teamAdminRoleOptions.map((role) => (
                        <MenuItem key={role} value={role}>
                          {formatRoleLabelFromEnum(role)}
                        </MenuItem>
                      ))}
                    </Select>
                  )}
                </FormControl>
              )}
            />

            {!isEditMode && (
              <TextField
                {...register("password")}
                fullWidth
                label="Password"
                size="small"
                type="password"
                autoComplete="new-password"
                error={Boolean(errors.password)}
                helperText={
                  errors.password?.message ??
                  "Optional — leave blank to generate a temporary password"
                }
              />
            )}

            {showTeamSelection && (
              <Controller
                name="teamIds"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth size="small" error={Boolean(errors.teamIds)}>
                    <InputLabel id="member-teams-label">Teams</InputLabel>
                    <Select
                      {...field}
                      labelId="member-teams-label"
                      label="Teams"
                      multiple
                      disabled={isEditingSuperAdmin}
                      renderValue={(selected) =>
                        (selected as string[])
                          .map((id) => inviteTeams.find((t) => t.id === id)?.name ?? id)
                          .join(", ")
                      }
                    >
                      {inviteTeams.map((team) => (
                        <MenuItem key={team.id} value={team.id}>
                          <Checkbox checked={(field.value as string[]).includes(team.id)} />
                          <ListItemText primary={team.name} />
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.teamIds && (
                      <Typography variant="caption" sx={{ color: "error.main", mt: 0.5 }}>
                        {errors.teamIds.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            )}
          </Box>
        </SlideOver>

        <ConfirmDialog
          open={removeTarget !== null}
          title="Remove member?"
          description={`${removeTarget?.name ?? "This member"} will lose access to the platform.`}
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

        {/* One-time credentials dialog shown after a successful invite */}
        <Dialog
          open={inviteResult !== null}
          onClose={() => setInviteResult(null)}
          maxWidth="xs"
          fullWidth
        >
          <DialogTitle>Member invited</DialogTitle>
          <DialogContent>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>{inviteResult?.member.name}</strong> ({inviteResult?.member.email}) has been
              added. Share these credentials with them — the password won't be shown again.
            </Typography>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                p: 1.5,
                borderRadius: 1,
                backgroundColor: tokens.bgDefault,
                border: `1px solid ${tokens.border}`,
              }}
            >
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="caption" sx={{ color: tokens.textMuted, display: "block" }}>
                  Email
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: "monospace", wordBreak: "break-all" }}>
                  {inviteResult?.member.email}
                </Typography>
                <Typography variant="caption" sx={{ color: tokens.textMuted, display: "block", mt: 1 }}>
                  Temporary password
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: "monospace", wordBreak: "break-all" }}>
                  {inviteResult?.temporaryPassword}
                </Typography>
              </Box>
              <Tooltip title={copied ? "Copied!" : "Copy credentials"}>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    void navigator.clipboard.writeText(
                      `Email: ${inviteResult?.member.email}\nPassword: ${inviteResult?.temporaryPassword}`,
                    );
                    setCopied(true);
                  }}
                >
                  {copied ? "Copied" : "Copy"}
                </Button>
              </Tooltip>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button variant="contained" onClick={() => setInviteResult(null)}>
              Done
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </RoleGuard>
  );
}

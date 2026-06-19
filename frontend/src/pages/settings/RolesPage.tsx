import { IconLock, IconPlus } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  createRole,
  fetchRolePermissions,
  fetchRoles,
  updateRolePermissions,
  type PermissionRow,
  type RoleRecord,
} from "@/api/roles";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { tokens } from "@/theme/palette";

const RESOURCE_LABELS: Record<string, string> = {
  insights: "Insights",
  alerts: "Alerts",
  uploads: "Uploads",
  members: "Members",
  reports: "Reports",
  audit_logs: "Audit log",
  tools: "Tools",
  teams: "Teams",
  credentials: "Credentials",
  collectors: "Collectors",
  settings: "Settings",
  my_usage: "My usage",
};

const RESOURCE_ORDER = Object.keys(RESOURCE_LABELS);

function formatRoleLabel(name: string): string {
  return name
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function RolesPage() {
  const queryClient = useQueryClient();
  const [matrix, setMatrix] = useState<Record<string, PermissionRow[]>>({});
  const [savingRoleId, setSavingRoleId] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [newRoleOpen, setNewRoleOpen] = useState(false);
  const [newRoleName, setNewRoleName] = useState("");
  const [newRoleDescription, setNewRoleDescription] = useState("");
  const [newRoleNameError, setNewRoleNameError] = useState<string | null>(null);
  const debounceTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const rolesQuery = useQuery({
    queryKey: ["roles"],
    queryFn: fetchRoles,
  });

  const roles = rolesQuery.data ?? [];

  useEffect(() => {
    if (roles.length === 0) return;

    void (async () => {
      const entries = await Promise.all(
        roles.map(async (role) => {
          const perms = await fetchRolePermissions(role.id);
          return [role.id, perms] as const;
        }),
      );
      setMatrix(Object.fromEntries(entries));
    })();
  }, [roles]);

  const saveMutation = useMutation({
    mutationFn: ({
      roleId,
      permissions,
    }: {
      roleId: string;
      permissions: PermissionRow[];
    }) => updateRolePermissions(roleId, permissions),
    onSuccess: async (_data, variables) => {
      setMatrix((prev) => ({ ...prev, [variables.roleId]: variables.permissions }));
      setSavingRoleId(null);
      setSaveError(null);
      await queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: () => {
      setSavingRoleId(null);
      setSaveError("Failed to save permissions. Changes were reverted.");
    },
  });

  const createMutation = useMutation({
    mutationFn: () => createRole(newRoleName.trim(), newRoleDescription.trim() || undefined),
    onSuccess: async (role) => {
      const perms = await fetchRolePermissions(role.id);
      setMatrix((prev) => ({ ...prev, [role.id]: perms }));
      setNewRoleOpen(false);
      setNewRoleName("");
      setNewRoleDescription("");
      setNewRoleNameError(null);
      await queryClient.invalidateQueries({ queryKey: ["roles"] });
    },
  });

  const scheduleSave = useCallback(
    (roleId: string, permissions: PermissionRow[], previous: PermissionRow[]) => {
      if (debounceTimers.current[roleId]) {
        clearTimeout(debounceTimers.current[roleId]);
      }
      debounceTimers.current[roleId] = setTimeout(() => {
        setSavingRoleId(roleId);
        saveMutation.mutate(
          { roleId, permissions },
          {
            onError: () => {
              setMatrix((prev) => ({ ...prev, [roleId]: previous }));
            },
          },
        );
      }, 300);
    },
    [saveMutation],
  );

  const handleToggle = useCallback(
    (
      role: RoleRecord,
      resource: string,
      field: "can_read" | "can_write",
      checked: boolean,
    ) => {
      const current = matrix[role.id];
      if (!current) return;

      const previous = current.map((row) => ({ ...row }));
      const next = current.map((row) => {
        if (row.resource !== resource) return row;
        if (field === "can_write") {
          return {
            ...row,
            can_write: checked,
            can_read: checked ? true : row.can_read,
          };
        }
        return { ...row, can_read: checked, can_write: checked ? row.can_write : false };
      });

      setMatrix((prev) => ({ ...prev, [role.id]: next }));
      scheduleSave(role.id, next, previous);
    },
    [matrix, scheduleSave],
  );

  const sortedRoles = useMemo(
    () => [...roles].sort((a, b) => Number(b.is_system) - Number(a.is_system) || a.name.localeCompare(b.name)),
    [roles],
  );

  const handleCreateRole = () => {
    if (!newRoleName.trim()) {
      setNewRoleNameError("Role name is required");
      return;
    }
    setNewRoleNameError(null);
    createMutation.mutate();
  };

  return (
    <RoleGuard resource="settings">
      <Box>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            mb: 3,
          }}
        >
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Roles & permissions
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted, mt: 0.5 }}>
              Configure read and write access per resource for each role.
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<IconPlus size={16} />}
            onClick={() => setNewRoleOpen(true)}
          >
            New Role
          </Button>
        </Box>

        {rolesQuery.isLoading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
            <CircularProgress size={28} />
          </Box>
        )}

        {rolesQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load roles.
          </Alert>
        )}

        {saveError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setSaveError(null)}>
            {saveError}
          </Alert>
        )}

        {!rolesQuery.isLoading && sortedRoles.length > 0 && (
          <Box sx={{ overflowX: "auto", border: `1px solid ${tokens.border}`, borderRadius: 1 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600, minWidth: 160 }}>Resource</TableCell>
                  {sortedRoles.map((role) => (
                    <TableCell key={role.id} align="center" sx={{ minWidth: 140 }}>
                      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 0.5 }}>
                        {role.is_system && <IconLock size={14} />}
                        <Typography variant="caption" sx={{ fontWeight: 600 }}>
                          {formatRoleLabel(role.name)}
                        </Typography>
                        {savingRoleId === role.id && <CircularProgress size={12} />}
                      </Box>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {RESOURCE_ORDER.map((resource) => (
                  <TableRow key={resource}>
                    <TableCell>{RESOURCE_LABELS[resource]}</TableCell>
                    {sortedRoles.map((role) => {
                      const row = matrix[role.id]?.find((p) => p.resource === resource);
                      return (
                        <TableCell key={`${role.id}-${resource}`} align="center">
                          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, alignItems: "center" }}>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                              <Typography variant="caption">R</Typography>
                              <Switch
                                size="small"
                                checked={Boolean(row?.can_read)}
                                onChange={(e) =>
                                  handleToggle(role, resource, "can_read", e.target.checked)
                                }
                              />
                            </Box>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                              <Typography variant="caption">W</Typography>
                              <Switch
                                size="small"
                                checked={Boolean(row?.can_write)}
                                onChange={(e) =>
                                  handleToggle(role, resource, "can_write", e.target.checked)
                                }
                              />
                            </Box>
                          </Box>
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}

        <Dialog open={newRoleOpen} onClose={() => setNewRoleOpen(false)} maxWidth="xs" fullWidth>
          <DialogTitle>New role</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              fullWidth
              label="Name"
              margin="dense"
              value={newRoleName}
              onChange={(e) => {
                setNewRoleName(e.target.value);
                if (newRoleNameError) setNewRoleNameError(null);
              }}
              error={Boolean(newRoleNameError)}
              helperText={newRoleNameError}
            />
            <TextField
              fullWidth
              label="Description"
              margin="dense"
              multiline
              minRows={2}
              value={newRoleDescription}
              onChange={(e) => setNewRoleDescription(e.target.value)}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setNewRoleOpen(false)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleCreateRole}
              disabled={createMutation.isPending}
            >
              Save
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </RoleGuard>
  );
}

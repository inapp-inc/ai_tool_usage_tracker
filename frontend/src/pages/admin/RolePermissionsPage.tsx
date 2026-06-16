/**
 * SuperAdmin-only page at /admin/permissions.
 * Renders a matrix of roles × pages with Read/Write toggles.
 */
import { Fragment, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Paper,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "@/api/client";

// ─── Types ───────────────────────────────────────────────────────────────────

interface PageAccess {
  read: boolean;
  write: boolean;
}

interface PermissionsMatrix {
  team_admin:     Record<string, PageAccess>;
  finance_viewer: Record<string, PageAccess>;
  auditor:        Record<string, PageAccess>;
}

interface PermissionsResponse {
  permissions: PermissionsMatrix;
  pages: string[];
  roles: string[];
}

// ─── Labels ──────────────────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  team_admin:     "Team Admin",
  finance_viewer: "Finance Viewer",
  auditor:        "Auditor",
};

const PAGE_LABELS: Record<string, string> = {
  "insights":          "Insights",
  "admin:teams":       "Admin › Teams",
  "admin:groups":      "Admin › Groups",
  "admin:members":     "Admin › Members",
  "admin:credentials": "Admin › Credentials",
  "alerts":            "Alerts",
  "uploads":           "Uploads",
  "audit":             "Audit Log",
};

// ─── API helpers ─────────────────────────────────────────────────────────────

const fetchPermissions = () =>
  apiRequest<PermissionsResponse>("/permissions");

const savePermissions = (matrix: PermissionsMatrix) =>
  apiRequest<PermissionsResponse>("/permissions", {
    method: "PUT",
    body: JSON.stringify({ permissions: matrix }),
  });

// ─── Component ───────────────────────────────────────────────────────────────

export function RolePermissionsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery<PermissionsResponse>({
    queryKey: ["admin-permissions"],
    queryFn: fetchPermissions,
  });

  const [draft, setDraft] = useState<PermissionsMatrix | null>(null);
  const [toast, setToast] = useState<{
    open: boolean;
    message: string;
    severity: "success" | "error";
  }>({ open: false, message: "", severity: "success" });

  useEffect(() => {
    if (data && !draft) setDraft(structuredClone(data.permissions));
  }, [data, draft]);

  const saveMutation = useMutation({
    mutationFn: savePermissions,
    onSuccess: (updated) => {
      queryClient.setQueryData(["admin-permissions"], (old: PermissionsResponse) => ({
        ...old,
        permissions: updated.permissions,
      }));
      // Bust the current user's access cache so nav updates immediately
      queryClient.invalidateQueries({ queryKey: ["my-access"] });
      setToast({ open: true, message: "Permissions saved.", severity: "success" });
    },
    onError: () =>
      setToast({ open: true, message: "Failed to save.", severity: "error" }),
  });

  if (isLoading || !draft) {
    return (
      <Box display="flex" justifyContent="center" mt={8}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return <Alert severity="error">Failed to load permissions.</Alert>;
  }

  const roles: string[] = data!.roles;
  const pages: string[] = data!.pages;

  const toggle = (role: string, page: string, field: "read" | "write") => {
    setDraft((prev) => {
      if (!prev) return prev;
      const next = structuredClone(prev);
      const key = role as keyof PermissionsMatrix;
      const current = next[key][page] ?? { read: false, write: false };
      if (field === "write") {
        const newWrite = !current.write;
        next[key][page] = { read: newWrite ? true : current.read, write: newWrite };
      } else {
        const newRead = !current.read;
        next[key][page] = { read: newRead, write: newRead ? current.write : false };
      }
      return next;
    });
  };

  const isDirty = JSON.stringify(draft) !== JSON.stringify(data!.permissions);

  return (
    <Box p={3}>
      <Typography variant="h5" fontWeight={600} mb={0.5}>
        Role Permissions
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Control which pages each role can access. SuperAdmin always has full
        access and is not shown here.
      </Typography>

      <Paper elevation={1} sx={{ overflowX: "auto" }}>
        <Table size="small" sx={{ minWidth: 700 }}>
          <TableHead>
            <TableRow sx={{ bgcolor: "grey.50" }}>
              <TableCell sx={{ fontWeight: 600, minWidth: 160 }}>Page</TableCell>
              {roles.map((role) => (
                <TableCell
                  key={role}
                  align="center"
                  colSpan={2}
                  sx={{
                    fontWeight: 600,
                    borderLeft: "1px solid",
                    borderColor: "divider",
                  }}
                >
                  {ROLE_LABELS[role] ?? role}
                </TableCell>
              ))}
            </TableRow>
            <TableRow sx={{ bgcolor: "grey.50" }}>
              <TableCell />
              {roles.map((role) => (
                <Fragment key={role}>
                  <TableCell
                    align="center"
                    sx={{
                      borderLeft: "1px solid",
                      borderColor: "divider",
                      py: 0.5,
                      color: "text.secondary",
                      fontSize: 12,
                    }}
                  >
                    Read
                  </TableCell>
                  <TableCell
                    align="center"
                    sx={{ py: 0.5, color: "text.secondary", fontSize: 12 }}
                  >
                    Write
                  </TableCell>
                </Fragment>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {pages.map((page) => (
              <TableRow key={page} hover>
                <TableCell sx={{ fontWeight: 500 }}>
                  {PAGE_LABELS[page] ?? page}
                </TableCell>
                {roles.map((role) => {
                  const key = role as keyof PermissionsMatrix;
                  const access = draft[key][page] ?? { read: false, write: false };
                  return (
                    <Fragment key={role}>
                      <TableCell
                        align="center"
                        sx={{ borderLeft: "1px solid", borderColor: "divider" }}
                      >
                        <Tooltip title={access.read ? "Revoke read" : "Grant read"}>
                          <Checkbox
                            size="small"
                            checked={access.read}
                            onChange={() => toggle(role, page, "read")}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip
                          title={
                            access.write
                              ? "Revoke write"
                              : "Grant write (implies read)"
                          }
                        >
                          <Checkbox
                            size="small"
                            checked={access.write}
                            onChange={() => toggle(role, page, "write")}
                          />
                        </Tooltip>
                      </TableCell>
                    </Fragment>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Box mt={2} display="flex" gap={2} justifyContent="flex-end">
        <Button
          variant="outlined"
          disabled={!isDirty || saveMutation.isPending}
          onClick={() => setDraft(structuredClone(data!.permissions))}
        >
          Discard changes
        </Button>
        <Button
          variant="contained"
          disabled={!isDirty || saveMutation.isPending}
          onClick={() => saveMutation.mutate(draft!)}
        >
          {saveMutation.isPending ? "Saving…" : "Save permissions"}
        </Button>
      </Box>

      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast((t) => ({ ...t, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity={toast.severity}
          onClose={() => setToast((t) => ({ ...t, open: false }))}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

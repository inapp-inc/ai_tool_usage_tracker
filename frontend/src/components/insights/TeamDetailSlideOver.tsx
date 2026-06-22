import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Divider,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { fetchDashboardStats } from "@/api/dashboard";
import type { Credential } from "@/api/credentials";
import { fetchTeamToolAssignment } from "@/api/teamTools";
import type { Team } from "@/api/teams";
import { fetchTools } from "@/api/tools";
import {
  fetchTeamDrilldown,
  type TeamUsageRow,
  type UserUsageRow,
} from "@/api/usage";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { TeamToolPricingSummary } from "@/components/teams/TeamToolPricingSummary";
import { UsageBreakdownStats } from "@/components/usage/UsageBreakdownStats";
import { SlideOver } from "@/components/layout/SlideOver";
import { tokens } from "@/theme/palette";

interface TeamDetailSlideOverProps {
  open: boolean;
  onClose: () => void;
  teamRow: TeamUsageRow | null;
  teamMeta: Team | null;
  from: string;
  to: string;
  filterToolId: string;
  toolOptions: Array<{ id: string; name: string }>;
  assignedToolIds: string[];
  credentials: Credential[];
  userColumns: Column<UserUsageRow>[];
}

export function TeamDetailSlideOver({
  open,
  onClose,
  teamRow,
  teamMeta,
  from,
  to,
  filterToolId,
  toolOptions,
  assignedToolIds,
  credentials,
  userColumns,
}: TeamDetailSlideOverProps) {
  const initialToolId =
    filterToolId || assignedToolIds[0] || "";

  const [panelToolId, setPanelToolId] = useState(initialToolId);

  useEffect(() => {
    if (open) {
      setPanelToolId(initialToolId);
    }
  }, [open, initialToolId]);

  const toolNameById = useMemo(
    () => new Map(toolOptions.map((tool) => [tool.id, tool.name])),
    [toolOptions],
  );

  const assignedTools = useMemo(
    () =>
      assignedToolIds.map((id) => ({
        id,
        name: toolNameById.get(id) ?? "Tool",
      })),
    [assignedToolIds, toolNameById],
  );

  const panelFilters = useMemo(
    () => ({
      teamId: teamRow?.teamId,
      toolId: panelToolId || undefined,
    }),
    [panelToolId, teamRow?.teamId],
  );

  const statsQuery = useQuery({
    queryKey: ["insights", "team-panel-stats", from, to, panelFilters],
    queryFn: () => fetchDashboardStats(from, to, panelFilters),
    enabled: open && Boolean(teamRow?.teamId),
  });

  const usersQuery = useQuery({
    queryKey: ["insights", "team-panel-users", teamRow?.teamId, from, to, panelToolId],
    queryFn: () =>
      fetchTeamDrilldown(
        teamRow!.teamId,
        from,
        to,
        panelToolId || null,
        panelFilters,
      ),
    enabled: open && Boolean(teamRow?.teamId),
  });

  const assignmentQuery = useQuery({
    queryKey: ["team-tool-assignment", teamRow?.teamId, panelToolId],
    queryFn: () => fetchTeamToolAssignment(teamRow!.teamId, panelToolId),
    enabled: open && Boolean(teamRow?.teamId) && Boolean(panelToolId),
  });

  const catalogToolsQuery = useQuery({
    queryKey: ["tools", "catalog"],
    queryFn: () => fetchTools(),
    enabled: open,
  });

  const panelCredential = useMemo(
    () =>
      credentials.find(
        (credential) =>
          credential.teamId === teamRow?.teamId &&
          (credential.catalogueToolId === panelToolId ||
            credential.toolId === panelToolId),
      ),
    [credentials, panelToolId, teamRow?.teamId],
  );

  const catalogTool = catalogToolsQuery.data?.find((tool) => tool.id === panelToolId);
  const assignment = assignmentQuery.data;
  const pricing = assignment?.pricing ?? catalogTool?.pricing;
  const pricingSource = assignment ? "team" : "tool_default";

  const sortedUsers = useMemo(
    () => [...(usersQuery.data ?? [])].sort((a, b) => b.tokens - a.tokens),
    [usersQuery.data],
  );

  return (
    <SlideOver
      open={open}
      onClose={onClose}
      title={teamRow?.teamName ?? ""}
      subtitle={
        teamMeta
          ? `${teamMeta.status === "active" ? "Active" : "Inactive"} · team details`
          : "Team details"
      }
      width={560}
    >
      {!teamRow ? null : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          <Box>
            <Typography
              variant="caption"
              sx={{
                color: tokens.textMuted,
                textTransform: "uppercase",
                display: "block",
                mb: 1,
              }}
            >
              Usage summary
            </Typography>
            {statsQuery.isPending ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
                <CircularProgress size={22} />
              </Box>
            ) : statsQuery.isError ? (
              <Alert severity="error">Failed to load usage summary.</Alert>
            ) : statsQuery.data ? (
              <UsageBreakdownStats stats={statsQuery.data} showIncludedCost />
            ) : null}
          </Box>

          {assignedTools.length > 0 && (
            <Box>
              <Typography
                variant="caption"
                sx={{
                  color: tokens.textMuted,
                  textTransform: "uppercase",
                  display: "block",
                  mb: 1,
                }}
              >
                Tools assigned
              </Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                {assignedTools.map((tool) => (
                  <Chip
                    key={tool.id}
                    label={tool.name}
                    size="small"
                    color={panelToolId === tool.id ? "primary" : "default"}
                    variant={panelToolId === tool.id ? "filled" : "outlined"}
                    onClick={() => setPanelToolId(tool.id)}
                    sx={{ cursor: "pointer" }}
                  />
                ))}
              </Box>
            </Box>
          )}

          {panelToolId && (
            <>
              {panelCredential && (
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <StatusBadge status={panelCredential.status} />
                  <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                    Credential: {panelCredential.label}
                    {panelCredential.lastUsedAt
                      ? ` · last sync ${new Date(panelCredential.lastUsedAt).toLocaleString()}`
                      : ""}
                  </Typography>
                </Box>
              )}

              <Box>
                <Typography
                  variant="caption"
                  sx={{
                    color: tokens.textMuted,
                    textTransform: "uppercase",
                    display: "block",
                    mb: 1,
                  }}
                >
                  Package details
                </Typography>
                {assignmentQuery.isPending || catalogToolsQuery.isPending ? (
                  <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
                    <CircularProgress size={22} />
                  </Box>
                ) : pricing ? (
                  <TeamToolPricingSummary pricing={pricing} pricingSource={pricingSource} />
                ) : (
                  <Alert severity="info">
                    No pricing configured for this tool. Edit the team to set tool pricing.
                  </Alert>
                )}
              </Box>
            </>
          )}

          <Divider />

          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1.5 }}>
              Users
            </Typography>
            {usersQuery.isError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Failed to load user breakdown.
              </Alert>
            )}
            <DataTable
              columns={userColumns}
              rows={sortedUsers}
              rowKey={(row) => row.userId}
              loading={usersQuery.isPending}
              stickyHeader
              emptyTitle="No usage data"
              emptyDescription="No token usage recorded for this team in the selected period."
            />
          </Box>
        </Box>
      )}
    </SlideOver>
  );
}

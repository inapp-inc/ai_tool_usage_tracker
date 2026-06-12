import { IconDownload, IconPlus, IconTrash } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  deleteReport,
  downloadReport,
  fetchReports,
  type Report,
  type ReportFormat,
  type ReportSchedule,
  type ReportType,
} from "@/api/reports";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { tokens } from "@/theme/palette";
import { formatRelativeTime } from "@/utils/formatters";

const FORMAT_CHIP_COLORS: Record<
  ReportFormat,
  { background: string; color: string }
> = {
  pdf: { background: "#FEE2E2", color: "#DC2626" },
  csv: { background: "#DCFCE7", color: "#16A34A" },
  xlsx: { background: "#EFF6FF", color: "#2563EB" },
};

const SCHEDULE_LABELS: Record<ReportSchedule, string> = {
  once: "Once",
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

function formatReportType(type: ReportType): string {
  return type
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function FormatChip({ format }: { format: ReportFormat }) {
  const colors = FORMAT_CHIP_COLORS[format];
  return (
    <Chip
      size="small"
      label={format.toUpperCase()}
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

export function ReportsListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [deleteTarget, setDeleteTarget] = useState<Report | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const reportsQuery = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteReport,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      setDeleteTarget(null);
    },
  });

  const downloadMutation = useMutation({
    mutationFn: downloadReport,
    onMutate: (id) => {
      setDownloadingId(id);
    },
    onSettled: () => {
      setDownloadingId(null);
    },
  });

  const columns: Column<Report>[] = useMemo(
    () => [
      {
        key: "name",
        header: "Report",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {row.name}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {formatReportType(row.type)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "format",
        header: "Format",
        render: (row) => <FormatChip format={row.format} />,
      },
      {
        key: "schedule",
        header: "Schedule",
        render: (row) => SCHEDULE_LABELS[row.schedule],
      },
      {
        key: "status",
        header: "Status",
        render: (row) => <StatusBadge status={row.status} />,
      },
      {
        key: "generatedAt",
        header: "Generated",
        sortable: true,
        render: (row) =>
          row.generatedAt ? (
            formatRelativeTime(row.generatedAt)
          ) : (
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              Pending
            </Typography>
          ),
      },
      {
        key: "fileSizeKb",
        header: "Size",
        align: "right",
        render: (row) => (
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {row.fileSizeKb != null ? `${row.fileSizeKb} KB` : "—"}
          </Typography>
        ),
      },
      {
        key: "actions",
        header: "",
        align: "right",
        render: (row) => {
          const canDownload = row.status === "completed";
          return (
            <Box sx={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
              <IconButton
                size="small"
                aria-label={`Download ${row.name}`}
                disabled={!canDownload || downloadingId === row.id}
                onClick={(event) => {
                  event.stopPropagation();
                  downloadMutation.mutate(row.id);
                }}
                sx={{ color: canDownload ? "inherit" : tokens.textMuted }}
              >
                {downloadingId === row.id ? (
                  <CircularProgress size={12} />
                ) : (
                  <IconDownload size={15} />
                )}
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
          );
        },
      },
    ],
    [downloadMutation, downloadingId],
  );

  const reports = reportsQuery.data ?? [];
  const showEmpty = !reportsQuery.isPending && reports.length === 0;

  return (
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
            Reports
          </Typography>
          <Typography variant="body2" sx={{ color: tokens.textMuted }}>
            Scheduled and on-demand usage exports
          </Typography>
        </Box>
        <Button
          variant="contained"
          size="small"
          startIcon={<IconPlus size={15} />}
          onClick={() => navigate("/reports/new")}
        >
          New Report
        </Button>
      </Box>

      {reportsQuery.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load reports. Please refresh.
        </Alert>
      )}

      {showEmpty ? (
        <EmptyState
          title="No reports yet"
          description="Generate your first report to export usage data."
          action={{
            label: "New Report",
            onClick: () => navigate("/reports/new"),
          }}
        />
      ) : (
        <DataTable
          columns={columns}
          rows={reports}
          rowKey={(row) => row.id}
          loading={reportsQuery.isPending}
          emptyTitle="No reports yet"
          emptyDescription="Generate your first report to export usage data."
        />
      )}

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete report?"
        description={`"${deleteTarget?.name ?? ""}" will be permanently removed.`}
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
  );
}

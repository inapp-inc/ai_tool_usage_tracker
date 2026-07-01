import { IconDownload, IconSearch } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Chip,
  FormControl,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  Skeleton,
  TextField,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { useEffect, useMemo, useState } from "react";

import {
  exportAuditLog,
  fetchAuditLog,
  type AuditCategory,
  type AuditLogEntry,
  type AuditLogFilters,
} from "@/api/auditLog";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { EmptyState } from "@/components/feedback/EmptyState";
import { tokens } from "@/theme/palette";
import { formatDateTime, formatRelativeTime } from "@/utils/formatters";

const DEFAULT_FILTERS: AuditLogFilters = {
  search: "",
  category: "",
  from: "",
  to: "",
};

const CATEGORY_OPTIONS: Array<{ value: AuditCategory; label: string }> = [
  { value: "auth", label: "Auth" },
  { value: "user", label: "User" },
  { value: "team", label: "Team" },
  { value: "tool", label: "Tool" },
  { value: "credential", label: "Credential" },
  { value: "alert", label: "Alert" },
  { value: "upload", label: "Upload" },
  { value: "report", label: "Report" },
];

const CATEGORY_CHIP_COLORS: Record<
  AuditCategory,
  { background: string; color: string }
> = {
  auth: { background: "#EDE9FE", color: "#7C3AED" },
  user: { background: "#EFF6FF", color: "#2563EB" },
  team: { background: "#ECFDF5", color: "#059669" },
  tool: { background: "#FFF7ED", color: "#C2410C" },
  credential: { background: "#FEE2E2", color: "#DC2626" },
  alert: { background: "#FEF9C3", color: "#A16207" },
  upload: { background: "#F0FDF4", color: "#16A34A" },
  report: { background: tokens.bgDefault, color: tokens.textMuted },
};

function CategoryChip({ category }: { category: AuditCategory }) {
  const colors = CATEGORY_CHIP_COLORS[category];
  const label =
    CATEGORY_OPTIONS.find((option) => option.value === category)?.label ??
    category;

  return (
    <Chip
      size="small"
      label={label}
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

function escapeCsvValue(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function exportAuditLogCsv(entries: AuditLogEntry[]): void {
  const headers = ["Time", "Category", "Action", "Performed By", "Email", "IP"];
  const rows = entries.map((entry) => [
    formatDateTime(entry.createdAt),
    entry.category,
    entry.description,
    entry.actorName,
    entry.actorEmail,
    entry.ipAddress,
  ]);

  const csv = [headers, ...rows]
    .map((row) => row.map(escapeCsvValue).join(","))
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `audit-log-${format(new Date(), "yyyy-MM-dd")}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

export function AuditLogPage() {
  const [searchInput, setSearchInput] = useState("");
  const [filters, setFilters] = useState<AuditLogFilters>(DEFAULT_FILTERS);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setFilters((prev) => ({ ...prev, search: searchInput }));
    }, 300);

    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const auditLogQuery = useQuery({
    queryKey: ["audit-log", filters],
    queryFn: () => fetchAuditLog(filters),
  });

  const entries = auditLogQuery.data ?? [];

  const hasActiveFilters =
    searchInput.trim() !== "" ||
    filters.category !== "" ||
    filters.from !== "" ||
    filters.to !== "";

  const handleClearFilters = () => {
    setSearchInput("");
    setFilters(DEFAULT_FILTERS);
  };

  const columns: Column<AuditLogEntry>[] = useMemo(
    () => [
      {
        key: "createdAt",
        header: "Time",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2" sx={{ fontSize: "0.8125rem" }}>
              {formatDateTime(row.createdAt)}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {formatRelativeTime(row.createdAt)}
            </Typography>
          </Box>
        ),
      },
      {
        key: "category",
        header: "Category",
        render: (row) => <CategoryChip category={row.category} />,
      },
      {
        key: "description",
        header: "Action",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2">{row.description}</Typography>
            {row.targetName && (
              <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                {row.targetType}:{" "}
                <Box
                  component="span"
                  sx={{ fontWeight: 500, color: "inherit" }}
                >
                  {row.targetName}
                </Box>
              </Typography>
            )}
          </Box>
        ),
      },
      {
        key: "actorName",
        header: "Performed by",
        sortable: true,
        render: (row) => (
          <Box>
            <Typography variant="body2">{row.actorName}</Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {row.actorEmail}
            </Typography>
          </Box>
        ),
      },
      {
        key: "ipAddress",
        header: "IP",
        render: (row) => (
          <Typography
            variant="caption"
            sx={{
              color: tokens.textMuted,
              fontFamily: "monospace",
              fontSize: "0.75rem",
            }}
          >
            {row.ipAddress}
          </Typography>
        ),
      },
    ],
    [],
  );

  return (
    <RoleGuard
      resource="audit_logs"
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to view the audit log."
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
              Audit Log
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Complete record of all administrative actions
            </Typography>
          </Box>
          <Button
            variant="outlined"
            size="small"
            startIcon={<IconDownload size={15} />}
            disabled={entries.length === 0}
            onClick={() => {
              if (filters.from && filters.to) {
                void exportAuditLog(filters).catch(() => exportAuditLogCsv(entries));
              } else {
                exportAuditLogCsv(entries);
              }
            }}
          >
            Export CSV
          </Button>
        </Box>

        <Box
          sx={{
            display: "flex",
            gap: 2,
            mb: 2,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          <TextField
            size="small"
            placeholder="Search actions, users, targets…"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            sx={{ width: 280 }}
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

          <FormControl size="small" sx={{ width: 180 }}>
            <InputLabel id="audit-category-label">Category</InputLabel>
            <Select
              labelId="audit-category-label"
              label="Category"
              value={filters.category}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  category: event.target.value as AuditCategory | "",
                }))
              }
            >
              <MenuItem value="">All categories</MenuItem>
              {CATEGORY_OPTIONS.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            type="date"
            size="small"
            label="From"
            value={filters.from}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, from: event.target.value }))
            }
            sx={{ width: 150 }}
            slotProps={{ inputLabel: { shrink: true } }}
          />

          <TextField
            type="date"
            size="small"
            label="To"
            value={filters.to}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, to: event.target.value }))
            }
            sx={{ width: 150 }}
            slotProps={{ inputLabel: { shrink: true } }}
          />

          {hasActiveFilters && (
            <Button variant="text" size="small" onClick={handleClearFilters}>
              Clear filters
            </Button>
          )}
        </Box>

        {auditLogQuery.isPending ? (
          <Skeleton width={80} height={20} sx={{ mb: 1 }} />
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {entries.length} entries
          </Typography>
        )}

        {auditLogQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load audit log. Please refresh.
          </Alert>
        )}

        <DataTable
          columns={columns}
          rows={entries}
          rowKey={(row) => row.id}
          loading={auditLogQuery.isPending}
          stickyHeader
          emptyTitle="No audit entries"
          emptyDescription="No actions match your current filters."
        />
      </Box>
    </RoleGuard>
  );
}

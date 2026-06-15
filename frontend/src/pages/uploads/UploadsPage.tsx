import {
  IconEye,
  IconFile,
  IconFileText,
  IconTrash,
  IconUpload,
  IconX,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useRef, useState, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";

import {
  deleteUpload,
  fetchUploads,
  uploadFile,
  type UploadFormat,
  type UploadRecord,
} from "@/api/uploads";
import { fetchTeams, type Team } from "@/api/teams";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";
import { formatRelativeTime } from "@/utils/formatters";

const EMPTY_TEAMS: Team[] = [];

const FORMAT_CHIP_COLORS: Record<
  UploadFormat,
  { background: string; color: string }
> = {
  csv: { background: "#DCFCE7", color: "#16A34A" },
  json: { background: "#EFF6FF", color: "#2563EB" },
};

function FormatChip({ format }: { format: UploadFormat }) {
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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export function UploadsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedTeamId, setSelectedTeamId] = useState<string>("");
  const [isDragOver, setIsDragOver] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<UploadRecord | null>(null);

  const uploadsQuery = useQuery({
    queryKey: ["uploads"],
    queryFn: fetchUploads,
  });

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const uploadMutation = useMutation({
    mutationFn: ({
      file,
      teamId,
    }: {
      file: File;
      teamId: string | null;
    }) => uploadFile(file, teamId),
    onSuccess: async (record) => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      handleCloseDialog();
      navigate(`/uploads/${record.id}/preview`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUpload,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      setDeleteTarget(null);
    },
  });

  const teams = teamsQuery.data ?? EMPTY_TEAMS;

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedFile(null);
    setSelectedTeamId("");
    setIsDragOver(false);
  };

  const handleFileSelect = (file: File | null) => {
    if (!file) {
      return;
    }
    const extension = file.name.toLowerCase();
    if (!extension.endsWith(".csv") && !extension.endsWith(".json")) {
      return;
    }
    setSelectedFile(file);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files.item(0);
    handleFileSelect(file);
  };

  const columns: Column<UploadRecord>[] = useMemo(
    () => [
      {
        key: "fileName",
        header: "File",
        sortable: true,
        render: (row) => (
          <Box sx={{ display: "flex", alignItems: "flex-start", gap: 1 }}>
            <Box sx={{ mt: 0.25, flexShrink: 0 }}>
              <IconFileText size={15} />
            </Box>
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {row.fileName}
              </Typography>
              <FormatChip format={row.format} />
            </Box>
          </Box>
        ),
      },
      {
        key: "status",
        header: "Status",
        render: (row) =>
          row.status === "error" && row.errorMessage ? (
            <Tooltip title={row.errorMessage}>
              <Box component="span">
                <StatusBadge status={row.status} />
              </Box>
            </Tooltip>
          ) : (
            <StatusBadge status={row.status} />
          ),
      },
      {
        key: "rowCount",
        header: "Rows",
        sortable: true,
        render: (row) => (
          <Typography variant="body2">
            {row.rowCount?.toLocaleString() ?? "—"}
            {row.errorCount != null && row.errorCount > 0 && (
              <Typography
                component="span"
                variant="body2"
                sx={{ color: tokens.critical }}
              >
                {` (${row.errorCount} errors)`}
              </Typography>
            )}
          </Typography>
        ),
      },
      {
        key: "teamName",
        header: "Team",
        render: (row) => (
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {row.teamName ?? "Org-wide"}
          </Typography>
        ),
      },
      {
        key: "uploadedByName",
        header: "Uploaded by",
        render: (row) => (
          <Typography variant="caption">{row.uploadedByName}</Typography>
        ),
      },
      {
        key: "createdAt",
        header: "Uploaded",
        sortable: true,
        render: (row) => formatRelativeTime(row.createdAt),
      },
      {
        key: "actions",
        header: "",
        align: "right",
        render: (row) => (
          <Box sx={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
            <IconButton
              size="small"
              aria-label={`Preview ${row.fileName}`}
              onClick={(event) => {
                event.stopPropagation();
                navigate(`/uploads/${row.id}/preview`);
              }}
            >
              <IconEye size={15} />
            </IconButton>
            <IconButton
              size="small"
              aria-label={`Delete ${row.fileName}`}
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
    [navigate],
  );

  const uploads = uploadsQuery.data ?? [];
  const showEmpty = !uploadsQuery.isPending && uploads.length === 0;

  return (
    <RoleGuard
      roles={[Role.SuperAdmin, Role.TeamAdmin]}
      fallback={
        <EmptyState
          title="Access denied"
          description="You don't have permission to manage uploads."
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
              Uploads
            </Typography>
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              Import usage data from CSV or JSON exports
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="small"
            startIcon={<IconUpload size={15} />}
            onClick={() => setDialogOpen(true)}
          >
            Upload File
          </Button>
        </Box>

        {uploadsQuery.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load uploads. Please refresh.
          </Alert>
        )}

        {showEmpty ? (
          <EmptyState
            title="No uploads yet"
            description="Upload a CSV or JSON file to import usage data."
          />
        ) : (
          <DataTable
            columns={columns}
            rows={uploads}
            rowKey={(row) => row.id}
            loading={uploadsQuery.isPending}
            emptyTitle="No uploads yet"
            emptyDescription="Upload a CSV or JSON file to import usage data."
          />
        )}

        <Dialog
          open={dialogOpen}
          onClose={handleCloseDialog}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Upload Usage File</DialogTitle>
          <DialogContent>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.json"
              hidden
              onChange={(event) => {
                const file = event.target.files?.item(0) ?? null;
                handleFileSelect(file);
                event.target.value = "";
              }}
            />

            <Box
              onClick={() => {
                if (!selectedFile) {
                  fileInputRef.current?.click();
                }
              }}
              onDragOver={(event) => {
                event.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
              sx={{
                border: `2px dashed ${isDragOver ? tokens.primary : tokens.border}`,
                borderRadius: "10px",
                p: 4,
                textAlign: "center",
                cursor: selectedFile ? "default" : "pointer",
                backgroundColor: isDragOver ? "#EFF6FF" : tokens.bgDefault,
                transition: "border-color 0.15s, background-color 0.15s",
                "&:hover": selectedFile
                  ? undefined
                  : {
                      borderColor: tokens.primary,
                      backgroundColor: "#EFF6FF",
                    },
              }}
            >
              {selectedFile ? (
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 1,
                  }}
                >
                  <IconFile size={20} color={tokens.textMuted} />
                  <Box sx={{ textAlign: "left" }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {selectedFile.name}
                    </Typography>
                    <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                      {formatFileSize(selectedFile.size)}
                    </Typography>
                  </Box>
                  <IconButton
                    size="small"
                    aria-label="Clear selected file"
                    onClick={(event) => {
                      event.stopPropagation();
                      setSelectedFile(null);
                    }}
                  >
                    <IconX size={16} />
                  </IconButton>
                </Box>
              ) : (
                <>
                  <IconUpload size={32} color={tokens.textMuted} />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Drop your CSV or JSON file here
                  </Typography>
                  <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                    or click to browse
                  </Typography>
                </>
              )}
            </Box>

            <FormControl fullWidth size="small" sx={{ mt: 2 }}>
              <InputLabel id="upload-team-label">Assign to team</InputLabel>
              <Select
                labelId="upload-team-label"
                label="Assign to team"
                value={selectedTeamId}
                onChange={(event) => setSelectedTeamId(event.target.value)}
              >
                <MenuItem value="">Org-wide</MenuItem>
                {teams.map((team) => (
                  <MenuItem key={team.id} value={team.id}>
                    {team.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {selectedFile && (
              <Alert severity="info" sx={{ mt: 1 }}>
                After upload you can map CSV columns and preview extracted usage
                before confirming import.
              </Alert>
            )}
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button variant="text" onClick={handleCloseDialog}>
              Cancel
            </Button>
            <Button
              variant="contained"
              disabled={!selectedFile || uploadMutation.isPending}
              onClick={() => {
                if (selectedFile) {
                  uploadMutation.mutate({
                    file: selectedFile,
                    teamId: selectedTeamId === "" ? null : selectedTeamId,
                  });
                }
              }}
              startIcon={
                uploadMutation.isPending ? (
                  <CircularProgress size={14} color="inherit" />
                ) : undefined
              }
            >
              Upload & Validate
            </Button>
          </DialogActions>
        </Dialog>

        <ConfirmDialog
          open={deleteTarget !== null}
          title="Delete upload?"
          description={`"${deleteTarget?.fileName ?? ""}" and all its imported records will be removed.`}
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

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
  TextField,
  Step,
  StepLabel,
  Stepper,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";

import {
  applyUploadMapping,
  deleteUpload,
  fetchUploadMapping,
  fetchUploads,
  uploadFile,
  type UploadColumnMapping,
  type UploadFormat,
  type UploadRecord,
} from "@/api/uploads";
import { fetchTeams, type Team } from "@/api/teams";
import { fetchTools } from "@/api/tools";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { StatusBadge } from "@/components/data-display/StatusBadge";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { tokens } from "@/theme/palette";
import { formatRelativeTime } from "@/utils/formatters";
import {
  buildInitialColumnMapping,
  isColumnMappingReady,
  UploadColumnMappingForm,
} from "./UploadColumnMappingForm";

const EMPTY_TEAMS: Team[] = [];
const UPLOAD_STEPS = ["Upload file", "Map columns", "Preview & import"];
type UploadDialogStep = "file" | "mapping";

const FORMAT_CHIP_COLORS: Record<
  UploadFormat,
  { background: string; color: string }
> = {
  csv: { background: "#DCFCE7", color: "#16A34A" },
  json: { background: "#EFF6FF", color: "#2563EB" },
  xlsx: { background: "#EFF6FF", color: "#2563EB" },
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
  const [selectedToolId, setSelectedToolId] = useState<string>("");
  const [isDragOver, setIsDragOver] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<UploadRecord | null>(null);
  const [dialogStep, setDialogStep] = useState<UploadDialogStep>("file");
  const [activeUploadId, setActiveUploadId] = useState<string | null>(null);
  const [columnMapping, setColumnMapping] = useState<UploadColumnMapping>({});
  const [filterTeamId, setFilterTeamId] = useState<string>("");
  const [filterToolId, setFilterToolId] = useState<string>("");
  const [filterPeriodFrom, setFilterPeriodFrom] = useState<string>("");
  const [filterPeriodTo, setFilterPeriodTo] = useState<string>("");

  const uploadsQuery = useQuery({
    queryKey: [
      "uploads",
      filterTeamId,
      filterToolId,
      filterPeriodFrom,
      filterPeriodTo,
    ],
    queryFn: () =>
      fetchUploads({
        teamId: filterTeamId || null,
        toolId: filterToolId || null,
        periodFrom: filterPeriodFrom || null,
        periodTo: filterPeriodTo || null,
      }),
  });

  const teamsQuery = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const catalogToolsQuery = useQuery({
    queryKey: ["tools", "catalog"],
    queryFn: () => fetchTools(),
  });

  const mappingQuery = useQuery({
    queryKey: ["uploads", activeUploadId, "mapping"],
    queryFn: () => fetchUploadMapping(activeUploadId ?? ""),
    enabled: dialogOpen && dialogStep === "mapping" && Boolean(activeUploadId),
  });

  useEffect(() => {
    if (!mappingQuery.data) {
      return;
    }
    setColumnMapping(
      buildInitialColumnMapping(
        mappingQuery.data.suggestedMapping,
        mappingQuery.data.columnMapping,
      ),
    );
  }, [mappingQuery.data]);

  const uploadMutation = useMutation({
    mutationFn: ({
      file,
      teamId,
      toolId,
    }: {
      file: File;
      teamId: string | null;
      toolId: string | null;
    }) => uploadFile(file, teamId, toolId),
    onSuccess: async (record) => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      if (record.status === "error") {
        return;
      }
      if (record.status === "mapping") {
        setActiveUploadId(record.id);
        setDialogStep("mapping");
        return;
      }
      handleCloseDialog();
      navigate(`/uploads/${record.id}/preview`);
    },
  });

  const applyMappingMutation = useMutation({
    mutationFn: () => applyUploadMapping(activeUploadId ?? "", columnMapping),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      const uploadId = activeUploadId;
      handleCloseDialog();
      if (uploadId) {
        navigate(`/uploads/${uploadId}/preview`);
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUpload,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      await queryClient.invalidateQueries({ queryKey: ["copilot"] });
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      await queryClient.invalidateQueries({ queryKey: ["insights"] });
      setDeleteTarget(null);
    },
  });

  const teams = teamsQuery.data ?? EMPTY_TEAMS;
  const catalogTools = catalogToolsQuery.data ?? [];
  const selectedTool = catalogTools.find((tool) => tool.id === selectedToolId) ?? null;
  const isCopilotToolSelected = selectedTool?.provider === "copilot";
  const isFigmaToolSelected = selectedTool?.provider === "figma";
  const isBillingToolSelected = isCopilotToolSelected || isFigmaToolSelected;
  const uploadBlocked =
    Boolean(selectedFile) &&
    isBillingToolSelected &&
    selectedTeamId === "";

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedFile(null);
    setSelectedTeamId("");
    setSelectedToolId("");
    setIsDragOver(false);
    setDialogStep("file");
    setActiveUploadId(null);
    setColumnMapping({});
  };

  const isSpreadsheetUpload =
    selectedFile?.name.toLowerCase().endsWith(".csv") ||
    selectedFile?.name.toLowerCase().endsWith(".xlsx") ||
    selectedFile?.name.toLowerCase().endsWith(".xlsm") ||
    false;
  const skipMappingForCopilot = isCopilotToolSelected && isSpreadsheetUpload;
  const mappingReady = isColumnMappingReady(
    columnMapping,
    mappingQuery.data?.fields,
  );

  const handleFileSelect = (file: File | null) => {
    if (!file) {
      return;
    }
    const extension = file.name.toLowerCase();
    const isCopilotSpreadsheet =
      isCopilotToolSelected &&
      (extension.endsWith(".csv") ||
        extension.endsWith(".xlsx") ||
        extension.endsWith(".xlsm"));
    if (isCopilotSpreadsheet) {
      setSelectedFile(file);
      return;
    }
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
              {row.billingPeriodStart && row.billingPeriodEnd && (
                <Typography variant="caption" sx={{ color: tokens.textMuted, display: "block" }}>
                  {row.billingPeriodStart} → {row.billingPeriodEnd}
                </Typography>
              )}
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
        key: "toolName",
        header: "Tool",
        render: (row) => (
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {row.toolName ?? "—"}
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
              aria-label={
                row.status === "mapping"
                  ? `Map columns for ${row.fileName}`
                  : `Preview ${row.fileName}`
              }
              onClick={(event) => {
                event.stopPropagation();
                navigate(
                  row.status === "mapping"
                    ? `/uploads/${row.id}/map`
                    : `/uploads/${row.id}/preview`,
                );
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
      resource="uploads"
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

        <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 2 }}>
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel id="upload-filter-team">Team</InputLabel>
            <Select
              labelId="upload-filter-team"
              label="Team"
              value={filterTeamId}
              onChange={(event) => setFilterTeamId(event.target.value)}
            >
              <MenuItem value="">All teams</MenuItem>
              {teams.map((team) => (
                <MenuItem key={team.id} value={team.id}>
                  {team.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel id="upload-filter-tool">Tool</InputLabel>
            <Select
              labelId="upload-filter-tool"
              label="Tool"
              value={filterToolId}
              onChange={(event) => setFilterToolId(event.target.value)}
            >
              <MenuItem value="">All tools</MenuItem>
              {catalogTools.map((tool) => (
                <MenuItem key={tool.id} value={tool.id}>
                  {tool.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            size="small"
            label="Period from"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={filterPeriodFrom}
            onChange={(event) => setFilterPeriodFrom(event.target.value)}
          />
          <TextField
            size="small"
            label="Period to"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={filterPeriodTo}
            onChange={(event) => setFilterPeriodTo(event.target.value)}
          />
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
          maxWidth={dialogStep === "mapping" ? "md" : "sm"}
          fullWidth
        >
          <DialogTitle>
            {dialogStep === "mapping" ? "Map CSV columns" : "Upload Usage File"}
          </DialogTitle>
          <DialogContent>
            <Stepper
              activeStep={dialogStep === "mapping" ? 1 : 0}
              alternativeLabel
              sx={{ mb: 3, mt: 0.5 }}
            >
              {UPLOAD_STEPS.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            {dialogStep === "mapping" ? (
              <>
                {mappingQuery.isPending && (
                  <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                    <CircularProgress size={28} />
                  </Box>
                )}
                {mappingQuery.isError && (
                  <Alert severity="error">
                    Could not load CSV headers. Close and try uploading again.
                  </Alert>
                )}
                {mappingQuery.data && (
                  <UploadColumnMappingForm
                    headers={mappingQuery.data.headers}
                    fields={mappingQuery.data.fields}
                    mapping={columnMapping}
                    suggestedMapping={mappingQuery.data.suggestedMapping}
                    sampleRow={mappingQuery.data.sampleRow}
                    onMappingChange={setColumnMapping}
                  />
                )}
                {applyMappingMutation.isError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {applyMappingMutation.error instanceof Error
                      ? applyMappingMutation.error.message
                      : "Validation failed. Check your column mapping."}
                  </Alert>
                )}
                {!mappingReady && mappingQuery.data && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    Map at least one CSV column to continue.
                  </Alert>
                )}
              </>
            ) : (
              <>
            <input
              ref={fileInputRef}
              type="file"
              accept={
                isCopilotToolSelected
                  ? ".csv,.xlsx,.xlsm"
                  : ".csv,.json"
              }
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

            <FormControl fullWidth size="small" sx={{ mt: 2 }}>
              <InputLabel id="upload-tool-label">Tool (optional)</InputLabel>
              <Select
                labelId="upload-tool-label"
                label="Tool (optional)"
                value={selectedToolId}
                onChange={(event) => setSelectedToolId(event.target.value)}
              >
                <MenuItem value="">Auto-detect from data</MenuItem>
                {catalogTools.map((tool) => (
                  <MenuItem key={tool.id} value={tool.id}>
                    {tool.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {isCopilotToolSelected && (
              <Alert severity="info" sx={{ mt: 1 }}>
                Copilot billing CSV requires a team assignment. Map SKU and unit type
                columns after upload — usage events are not imported.
              </Alert>
            )}

            {isFigmaToolSelected && (
              <Alert severity="info" sx={{ mt: 1 }}>
                Figma billing CSV requires a team with Figma pricing configured (full/view
                seat costs and credits per USD). One row per user is imported per usage period.
              </Alert>
            )}

            {uploadBlocked && (
              <Alert severity="warning" sx={{ mt: 1 }}>
                Select a team before uploading{" "}
                {isFigmaToolSelected ? "Figma" : "Copilot"} billing data.
              </Alert>
            )}

            {selectedFile && isCopilotToolSelected && (
              <Alert severity="info" sx={{ mt: 1 }}>
                Copilot billing CSV or Excel files are parsed automatically using
                GitHub column names — no manual column mapping required.
              </Alert>
            )}

            {selectedFile && !isBillingToolSelected && (
              <Alert severity="info" sx={{ mt: 1 }}>
                {isSpreadsheetUpload
                  ? "After upload, map CSV columns to fields. If you assign a team, usage and members import to that team."
                  : "JSON files are parsed after upload. Assign a team to bind imported usage to that team."}
              </Alert>
            )}
              </>
            )}
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button variant="text" onClick={handleCloseDialog}>
              Cancel
            </Button>
            {dialogStep === "mapping" ? (
              <Button
                variant="contained"
                disabled={
                  !mappingReady ||
                  applyMappingMutation.isPending ||
                  mappingQuery.isPending
                }
                onClick={() => applyMappingMutation.mutate()}
                startIcon={
                  applyMappingMutation.isPending ? (
                    <CircularProgress size={14} color="inherit" />
                  ) : undefined
                }
              >
                Preview rows
              </Button>
            ) : (
            <Button
              variant="contained"
              disabled={
                !selectedFile || uploadMutation.isPending || uploadBlocked
              }
              onClick={() => {
                if (selectedFile) {
                  uploadMutation.mutate({
                    file: selectedFile,
                    teamId: selectedTeamId === "" ? null : selectedTeamId,
                    toolId: selectedToolId === "" ? null : selectedToolId,
                  });
                }
              }}
              startIcon={
                uploadMutation.isPending ? (
                  <CircularProgress size={14} color="inherit" />
                ) : undefined
              }
            >
              {skipMappingForCopilot
                ? "Upload & Preview"
                : isSpreadsheetUpload
                  ? "Upload & Map Columns"
                  : "Upload & Validate"}
            </Button>
            )}
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

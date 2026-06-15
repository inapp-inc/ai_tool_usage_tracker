import {
  IconAlertCircle,
  IconArrowLeft,
  IconCircleCheck,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ApiClientError } from "@/api/client";
import {
  EMPTY_CSV_COLUMN_MAPPING,
  type ToolCsvColumnMapping,
  type ToolCsvFormatHint,
} from "@/api/tools";
import {
  deleteUpload,
  inspectUpload,
  previewUploadWithMapping,
  submitUpload,
  type UploadPreviewRow,
} from "@/api/uploads";
import { CsvColumnMappingFields } from "@/components/csv/CsvColumnMappingFields";
import { csvMappingIsComplete } from "@/components/csv/csvImportUtils";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { ConfirmDialog } from "@/components/feedback/ConfirmDialog";
import { EmptyState } from "@/components/feedback/EmptyState";
import { tokens } from "@/theme/palette";
import {
  formatCost,
  formatDateTime,
  formatTokens,
} from "@/utils/formatters";

export function UploadPreviewPage() {
  const { uploadId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [discardOpen, setDiscardOpen] = useState(false);
  const [headers, setHeaders] = useState<string[]>([]);
  const [formatHint, setFormatHint] = useState<ToolCsvFormatHint>("daily");
  const [columnMapping, setColumnMapping] = useState<ToolCsvColumnMapping>(
    EMPTY_CSV_COLUMN_MAPPING,
  );
  const [inspectError, setInspectError] = useState<string | null>(null);
  const [preview, setPreview] = useState<Awaited<
    ReturnType<typeof previewUploadWithMapping>
  > | null>(null);

  const inspectQuery = useQuery({
    queryKey: ["uploads", uploadId, "inspect"],
    queryFn: () => inspectUpload(uploadId),
    enabled: Boolean(uploadId),
    retry: false,
  });

  useEffect(() => {
    if (inspectQuery.data) {
      setHeaders(inspectQuery.data.headers);
      setFormatHint(inspectQuery.data.formatHint);
      setColumnMapping(inspectQuery.data.suggestedMapping);
      setInspectError(null);
    }
  }, [inspectQuery.data]);

  useEffect(() => {
    if (inspectQuery.error) {
      setHeaders([]);
      setInspectError(
        inspectQuery.error instanceof ApiClientError
          ? inspectQuery.error.apiError.detail
          : inspectQuery.error.message || "Could not read CSV headers.",
      );
    }
  }, [inspectQuery.error]);

  const mappingReady = csvMappingIsComplete(formatHint, columnMapping);

  const previewMutation = useMutation({
    mutationFn: (mapping: ToolCsvColumnMapping) =>
      previewUploadWithMapping(uploadId, mapping),
    onSuccess: (result) => {
      setPreview(result);
    },
  });

  useEffect(() => {
    if (!uploadId || !mappingReady || !inspectQuery.isSuccess) {
      return;
    }
    if (previewMutation.isPending || inspectQuery.isPending) {
      return;
    }
    previewMutation.mutate(columnMapping);
  }, [uploadId, mappingReady, columnMapping, inspectQuery.isSuccess]);

  const deleteMutation = useMutation({
    mutationFn: deleteUpload,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      setDiscardOpen(false);
      navigate("/uploads");
    },
  });

  const submitMutation = useMutation({
    mutationFn: () => submitUpload(uploadId, { teamId: null }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      navigate("/uploads");
    },
  });

  const hasErrors = (preview?.errorRows ?? 0) > 0;
  const canImport =
    Boolean(preview) &&
    !preview?.parseError &&
    !preview?.needsMapping &&
    preview.validRows > 0;

  const previewError =
    preview?.parseError ??
    (previewMutation.error instanceof ApiClientError
      ? previewMutation.error.apiError.detail
      : previewMutation.error instanceof Error
        ? previewMutation.error.message
        : null);

  const columns: Column<UploadPreviewRow>[] = useMemo(
    () => [
      {
        key: "rowIndex",
        header: "#",
        render: (row) => (
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {row.rowIndex}
          </Typography>
        ),
      },
      {
        key: "userName",
        header: "User",
        render: (row) => (
          <Box>
            <Typography variant="body2">{row.userName}</Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {row.userId}
            </Typography>
          </Box>
        ),
      },
      {
        key: "model",
        header: "Model",
        render: (row) => (
          <Typography variant="caption">{row.model}</Typography>
        ),
      },
      {
        key: "tokens",
        header: "Tokens",
        render: (row) => formatTokens(row.tokens),
      },
      {
        key: "cost",
        header: "Cost",
        render: (row) => formatCost(row.cost),
      },
      {
        key: "timestamp",
        header: "Timestamp",
        render: (row) => formatDateTime(row.timestamp),
      },
      {
        key: "status",
        header: "Status",
        render: (row) =>
          row.status === "error" ? (
            <Box sx={{ display: "flex", alignItems: "flex-start", gap: 0.5 }}>
              <IconAlertCircle size={14} color={tokens.critical} />
              <Typography variant="caption" sx={{ color: tokens.critical }}>
                {row.errorReason}
              </Typography>
            </Box>
          ) : (
            <IconCircleCheck size={14} color={tokens.success} />
          ),
      },
    ],
    [],
  );

  const updateMapping = (patch: Partial<ToolCsvColumnMapping>) => {
    setColumnMapping((current) => ({ ...current, ...patch }));
    setPreview(null);
  };

  const handlePreview = () => {
    if (!mappingReady) {
      return;
    }
    previewMutation.mutate(columnMapping);
  };

  const pageLoading = inspectQuery.isPending && !headers.length;

  if (!uploadId) {
    return (
      <EmptyState
        title="Upload not found"
        description="Select an upload from the uploads list."
      />
    );
  }

  return (
    <Box>
      <Button
        variant="text"
        startIcon={<IconArrowLeft size={14} />}
        onClick={() => navigate("/uploads")}
        sx={{ mb: 1, ml: -0.5 }}
      >
        Back to Uploads
      </Button>

      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          mb: 3,
          gap: 2,
          flexWrap: "wrap",
        }}
      >
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {preview?.fileName ?? "Upload preview"}
          </Typography>
          {preview && (
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              {preview.totalRows} daily rows •{" "}
              <Box
                component="span"
                sx={{ color: hasErrors ? tokens.critical : tokens.textMuted }}
              >
                {preview.errorRows} errors
              </Box>
            </Typography>
          )}
        </Box>

        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            onClick={() => setDiscardOpen(true)}
          >
            Discard
          </Button>
          <Tooltip
            title={
              !canImport
                ? previewError || "Map columns and preview before importing"
                : ""
            }
            disableHoverListener={canImport}
          >
            <span>
              <Button
                variant="contained"
                size="small"
                disabled={!canImport || submitMutation.isPending}
                onClick={() => submitMutation.mutate()}
                startIcon={
                  submitMutation.isPending ? (
                    <CircularProgress size={14} color="inherit" />
                  ) : undefined
                }
              >
                Confirm Import
              </Button>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {(inspectError || previewError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {previewError ?? inspectError}
        </Alert>
      )}

      {pageLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress size={28} />
        </Box>
      )}

      {!pageLoading && headers.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2.5, mb: 3 }}>
          <Typography variant="body2" sx={{ color: tokens.textMuted, mb: 2 }}>
            Map your CSV headers to tokens, cost, and dates — same as tool CSV
            import. Adjust columns if auto-detection did not match your export.
          </Typography>
          <CsvColumnMappingFields
            headers={headers}
            formatHint={formatHint}
            columnMapping={columnMapping}
            onFormatHintChange={setFormatHint}
            onMappingChange={updateMapping}
            onPreview={handlePreview}
            previewPending={previewMutation.isPending}
            mappingReady={mappingReady}
          />
        </Paper>
      )}

      {preview && !preview.parseError && preview.validRows > 0 && (
        <>
          <Alert severity="info" sx={{ mb: 2 }}>
            Extracted {formatTokens(preview.tokenCount)} tokens and{" "}
            {formatCost(preview.costTotal)}
            {preview.dateFrom && preview.dateTo
              ? ` from ${preview.dateFrom} to ${preview.dateTo}`
              : ""}{" "}
            ({preview.sourceRowCount} source row
            {preview.sourceRowCount === 1 ? "" : "s"}).
          </Alert>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: hasErrors ? "1fr 1fr" : "1fr",
              gap: 2,
              mb: 3,
            }}
          >
            <Box
              sx={{
                backgroundColor: "#DCFCE7",
                border: "1px solid #BBF7D0",
                borderRadius: "10px",
                p: 2,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                <IconCircleCheck size={20} color="#16A34A" />
                <Typography variant="body2" sx={{ fontWeight: 600, color: "#16A34A" }}>
                  {preview.validRows} valid rows
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: "#16A34A" }}>
                Ready to import
              </Typography>
            </Box>

            {hasErrors && (
              <Box
                sx={{
                  backgroundColor: "#FEE2E2",
                  border: "1px solid #FECACA",
                  borderRadius: "10px",
                  p: 2,
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                  <IconAlertCircle size={20} color="#DC2626" />
                  <Typography variant="body2" sx={{ fontWeight: 600, color: "#DC2626" }}>
                    {preview.errorRows} rows with errors
                  </Typography>
                </Box>
                <Typography variant="caption" sx={{ color: "#DC2626" }}>
                  These rows will be skipped
                </Typography>
              </Box>
            )}
          </Box>
        </>
      )}

      <DataTable
        columns={columns}
        rows={preview?.rows ?? []}
        rowKey={(row) => String(row.rowIndex)}
        loading={previewMutation.isPending && !preview}
        stickyHeader
        emptyTitle={
          headers.length > 0
            ? "No preview yet"
            : inspectError
              ? "Could not inspect file"
              : "No preview data"
        }
        emptyDescription={
          headers.length > 0
            ? "Complete column mapping and preview extraction to see rows."
            : undefined
        }
      />

      <ConfirmDialog
        open={discardOpen}
        title="Discard upload?"
        description="This file will be deleted and no data will be imported."
        confirmLabel="Discard"
        loading={deleteMutation.isPending}
        onClose={() => setDiscardOpen(false)}
        onConfirm={() => deleteMutation.mutate(uploadId)}
      />
    </Box>
  );
}

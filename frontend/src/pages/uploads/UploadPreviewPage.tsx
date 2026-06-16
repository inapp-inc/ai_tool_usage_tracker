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
  Tooltip,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  deleteUpload,
  fetchUploadPreview,
  submitUpload,
  type UploadPreviewRow,
} from "@/api/uploads";
import { ApiClientError } from "@/api/client";
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

  const previewQuery = useQuery({
    queryKey: ["uploads", uploadId, "preview"],
    queryFn: () => fetchUploadPreview(uploadId),
    enabled: Boolean(uploadId),
    retry: (failureCount, error) => {
      if (error instanceof ApiClientError && error.apiError.status === 409) {
        return false;
      }
      return failureCount < 2;
    },
  });

  useEffect(() => {
    if (
      previewQuery.error instanceof ApiClientError &&
      previewQuery.error.apiError.status === 409
    ) {
      navigate(`/uploads/${uploadId}/map`, { replace: true });
    }
  }, [previewQuery.error, uploadId, navigate]);

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

  const preview = previewQuery.data;
  const hasErrors = (preview?.errorRows ?? 0) > 0;

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
            {preview?.fileName ?? "Loading preview…"}
          </Typography>
          {preview && (
            <Typography variant="body2" sx={{ color: tokens.textMuted }}>
              {preview.totalRows} rows •{" "}
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
            title={hasErrors ? "Fix errors before importing" : ""}
            disableHoverListener={!hasErrors}
          >
            <span>
              <Button
                variant="contained"
                size="small"
                disabled={hasErrors || submitMutation.isPending || !preview}
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

      {previewQuery.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load upload preview. Please refresh.
        </Alert>
      )}

      {preview && (
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
      )}

      <DataTable
        columns={columns}
        rows={preview?.rows ?? []}
        rowKey={(row) => String(row.rowIndex)}
        loading={previewQuery.isPending}
        stickyHeader
        emptyTitle="No preview data"
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

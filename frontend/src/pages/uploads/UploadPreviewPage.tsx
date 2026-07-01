import {
  IconArrowLeft,
  IconCircleCheck,
} from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Step,
  StepLabel,
  Stepper,
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

const UPLOAD_STEPS = ["Upload file", "Map columns", "Preview & import"];

export function UploadPreviewPage() {
  const { uploadId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [discardOpen, setDiscardOpen] = useState(false);
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());

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

  useEffect(() => {
    if (!previewQuery.data) {
      return;
    }
    setSelectedRows(
      new Set(previewQuery.data.rows.map((row) => row.rowIndex)),
    );
  }, [previewQuery.data]);

  const deleteMutation = useMutation({
    mutationFn: deleteUpload,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      setDiscardOpen(false);
      navigate("/uploads");
    },
  });

  const submitMutation = useMutation({
    mutationFn: () =>
      submitUpload(uploadId, {
        teamId: preview?.teamId ?? null,
        rowNumbers: Array.from(selectedRows).sort((a, b) => a - b),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      await queryClient.invalidateQueries({ queryKey: ["members"] });
      await queryClient.invalidateQueries({ queryKey: ["teams"] });
      await queryClient.invalidateQueries({ queryKey: ["copilot"] });
      await queryClient.invalidateQueries({ queryKey: ["figma"] });
      await queryClient.invalidateQueries({ queryKey: ["insights"] });
      navigate("/uploads");
    },
  });

  const preview = previewQuery.data;
  const allRows = preview?.rows ?? [];
  const isCopilotImport = Boolean(preview?.copilotSummary);
  const isFigmaImport = Boolean(preview?.figmaSummary);
  const isBillingImport = isCopilotImport || isFigmaImport;
  const copilotSummary = preview?.copilotSummary ?? null;
  const figmaSummary = preview?.figmaSummary ?? null;
  const hasPeriodConflict = Boolean(
    copilotSummary?.periodConflicts?.length || figmaSummary?.periodConflicts?.length,
  );
  const allSelected =
    allRows.length > 0 && selectedRows.size === allRows.length;
  const someSelected = selectedRows.size > 0 && !allSelected;

  const toggleRow = (rowIndex: number) => {
    setSelectedRows((current) => {
      const next = new Set(current);
      if (next.has(rowIndex)) {
        next.delete(rowIndex);
      } else {
        next.add(rowIndex);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (allSelected) {
      setSelectedRows(new Set());
      return;
    }
    setSelectedRows(new Set(allRows.map((row) => row.rowIndex)));
  };

  const columns: Column<UploadPreviewRow>[] = useMemo(
    () =>
      isCopilotImport
        ? [
            {
              key: "select",
              header: "",
              width: 48,
              render: (row) => (
                <Checkbox
                  size="small"
                  checked={selectedRows.has(row.rowIndex)}
                  onChange={() => toggleRow(row.rowIndex)}
                  onClick={(event) => event.stopPropagation()}
                />
              ),
            },
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
              key: "sku",
              header: "SKU",
              render: (row) => String(row.mappedData?.sku ?? row.rawData?.sku ?? "—"),
            },
            {
              key: "unitType",
              header: "Unit type",
              render: (row) =>
                String(row.mappedData?.unit_type ?? row.rawData?.unit_type ?? "—"),
            },
            {
              key: "monthlyAmount",
              header: "Monthly amount",
              render: (row) => {
                const value =
                  row.mappedData?.monthly_amount ??
                  row.rawData?.monthly_amount ??
                  row.rawData?.applied_cost_per_quantity;
                return value != null && value !== "" ? formatCost(Number(value)) : "—";
              },
            },
            {
              key: "netAmount",
              header: "Net amount",
              render: (row) => {
                const value = row.mappedData?.net_amount ?? row.rawData?.net_amount;
                return value != null && value !== "" ? formatCost(Number(value)) : "—";
              },
            },
            {
              key: "quantity",
              header: "Quantity",
              render: (row) =>
                String(row.mappedData?.quantity ?? row.rawData?.quantity ?? "—"),
            },
            {
              key: "notes",
              header: "Notes",
              render: (row) =>
                row.errorReason ? (
                  <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                    {row.errorReason}
                  </Typography>
                ) : (
                  <IconCircleCheck size={14} color={tokens.success} />
                ),
            },
          ]
        : isFigmaImport
          ? [
              {
                key: "select",
                header: "",
                width: 48,
                render: (row) => (
                  <Checkbox
                    size="small"
                    checked={selectedRows.has(row.rowIndex)}
                    onChange={() => toggleRow(row.rowIndex)}
                    onClick={(event) => event.stopPropagation()}
                  />
                ),
              },
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
                      {String(row.mappedData?.user_email ?? row.userId ?? "—")}
                    </Typography>
                  </Box>
                ),
              },
              {
                key: "seatType",
                header: "Seat type",
                render: (row) =>
                  String(row.model || row.mappedData?.seat_type || "—"),
              },
              {
                key: "seatCredits",
                header: "Seat credits",
                render: (row) =>
                  String(
                    row.mappedData?.seat_credits_used ??
                      row.rawData?.["Seat credits used"] ??
                      "—",
                  ),
              },
              {
                key: "paidCredits",
                header: "Paid credits",
                render: (row) =>
                  String(
                    row.mappedData?.paid_credits_used ??
                      row.rawData?.["Paid credits used"] ??
                      "—",
                  ),
              },
              {
                key: "cost",
                header: "Est. cost (USD)",
                render: (row) => formatCost(row.cost),
              },
              {
                key: "period",
                header: "Usage period",
                render: (row) => {
                  const start =
                    row.mappedData?.usage_period_start ?? row.rawData?.["Usage period start"];
                  const end =
                    row.mappedData?.usage_period_end ?? row.rawData?.["Usage period end"];
                  if (start && end) {
                    return `${String(start)} → ${String(end)}`;
                  }
                  return start ? String(start) : end ? String(end) : "—";
                },
              },
              {
                key: "notes",
                header: "Notes",
                render: (row) =>
                  row.errorReason ? (
                    <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                      {row.errorReason}
                    </Typography>
                  ) : (
                    <IconCircleCheck size={14} color={tokens.success} />
                  ),
              },
            ]
          : [
      {
        key: "select",
        header: "",
        width: 48,
        render: (row) => (
          <Checkbox
            size="small"
            checked={selectedRows.has(row.rowIndex)}
            onChange={() => toggleRow(row.rowIndex)}
            onClick={(event) => event.stopPropagation()}
          />
        ),
      },
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
              {row.userId || "From mapped CSV data"}
            </Typography>
          </Box>
        ),
      },
      {
        key: "model",
        header: "Model",
        render: (row) => (
          <Typography variant="caption">{row.model || "—"}</Typography>
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
        render: (row) =>
          row.timestamp ? formatDateTime(row.timestamp) : "—",
      },
      {
        key: "notes",
        header: "Notes",
        render: (row) =>
          row.errorReason ? (
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {row.errorReason}
            </Typography>
          ) : (
            <IconCircleCheck size={14} color={tokens.success} />
          ),
      },
    ],
    [selectedRows, isCopilotImport, isFigmaImport],
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

      <Stepper activeStep={2} alternativeLabel sx={{ mb: 3 }}>
        {UPLOAD_STEPS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

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
              {isBillingImport
                ? `${preview.totalRows} billing rows • ${selectedRows.size} selected for import`
                : `${preview.totalRows} mapped rows • ${selectedRows.size} selected for import`}
              {preview.teamName ? (
                <>
                  {" "}
                  • Team: <strong>{preview.teamName}</strong>
                </>
              ) : (
                <> • Org-wide (no team)</>
              )}
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
          <Button
            variant="contained"
            size="small"
            disabled={
              selectedRows.size === 0 ||
              submitMutation.isPending ||
              !preview ||
              hasPeriodConflict
            }
            onClick={() => submitMutation.mutate()}
            startIcon={
              submitMutation.isPending ? (
                <CircularProgress size={14} color="inherit" />
              ) : undefined
            }
          >
            {isBillingImport
              ? `Import ${selectedRows.size} billing row${selectedRows.size === 1 ? "" : "s"}`
              : `Import ${selectedRows.size} row${selectedRows.size === 1 ? "" : "s"}`}
          </Button>
        </Box>
      </Box>

      {previewQuery.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load upload preview. Please refresh.
        </Alert>
      )}

      {figmaSummary && (
        <Alert severity={hasPeriodConflict ? "warning" : "success"} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
            {hasPeriodConflict
              ? "Usage period already imported"
              : "Figma billing totals (all mapped rows)"}
          </Typography>
          {hasPeriodConflict ? (
            <Typography variant="body2">
              {figmaSummary.periodConflicts?.map((conflict) => (
                <span
                  key={`${conflict.usagePeriodStart}-${conflict.usagePeriodEnd}`}
                >
                  Period {conflict.usagePeriodStart} to {conflict.usagePeriodEnd} exists as{" "}
                  <strong>{conflict.existingFilename}</strong>. Delete that upload before
                  importing again.
                </span>
              ))}
            </Typography>
          ) : (
            <Typography variant="body2">
              Paid credit overage: {formatCost(figmaSummary.totalPaidCost)}
              {figmaSummary.creditsPerUsd != null && (
                <> · ${figmaSummary.creditsPerUsd}/paid credit</>
              )}{" "}
              · Import overage total: {formatCost(figmaSummary.totalCost)} · {figmaSummary.userCount}{" "}
              users ({figmaSummary.fullSeatCount} full, {figmaSummary.viewSeatCount} view). Subscription
              is configured on the team separately.
            </Typography>
          )}
        </Alert>
      )}

      {copilotSummary && (
        <Alert severity={hasPeriodConflict ? "warning" : "success"} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
            {hasPeriodConflict
              ? "Billing period already imported"
              : "Copilot billing totals (all mapped rows)"}
          </Typography>
          {hasPeriodConflict ? (
            <Typography variant="body2">
              {copilotSummary.periodConflicts?.map((conflict) => (
                <span key={`${conflict.billingPeriodStart}-${conflict.billingPeriodEnd}`}>
                  Period {conflict.billingPeriodStart} to {conflict.billingPeriodEnd} exists as{" "}
                  <strong>{conflict.existingFilename}</strong>. Delete that upload before importing
                  again.
                </span>
              ))}
            </Typography>
          ) : (
            <Typography variant="body2">
              Monthly cost limit: {formatCost(copilotSummary.monthlyCostLimit)} ·
              Additional spend (net): {formatCost(copilotSummary.additionalCost)}
              {copilotSummary.creditsCost > 0 && (
                <> · AI credits (gross): {formatCost(copilotSummary.creditsCost)}</>
              )}{" "}
              · Total (gross): {formatCost(copilotSummary.totalCost)}
            </Typography>
          )}
        </Alert>
      )}

      {preview && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {isCopilotImport ? (
            preview.teamName ? (
              <>
                Billing data from selected rows will update Copilot cost metrics for{" "}
                <strong>{preview.teamName}</strong>. No usage events are created.
              </>
            ) : (
              <>Assign a team when uploading Copilot billing CSV.</>
            )
          ) : isFigmaImport ? (
            preview.teamName ? (
              <>
                Figma billing from selected rows will be stored for{" "}
                <strong>{preview.teamName}</strong>. Costs use team pricing (credits per USD and
                seat costs). No usage events are created.
              </>
            ) : (
              <>Assign a team when uploading Figma billing CSV.</>
            )
          ) : preview.teamName ? (
            <>
              Usage and members from selected rows will be bound to{" "}
              <strong>{preview.teamName}</strong>. Platform users in the import
              are added to that team automatically.
            </>
          ) : (
            <>
              Rows are extracted from your column mapping. Select which rows to
              import. Choose a team when uploading to bind usage to a team.
            </>
          )}
        </Alert>
      )}

      {preview && allRows.length > 0 && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <Checkbox
            size="small"
            checked={allSelected}
            indeterminate={someSelected}
            onChange={toggleAll}
          />
          <Typography variant="body2">
            {allSelected ? "Deselect all" : "Select all mapped rows"}
          </Typography>
        </Box>
      )}

      <DataTable
        columns={columns}
        rows={allRows}
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

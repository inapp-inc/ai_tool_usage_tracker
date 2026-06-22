import { IconDownload, IconFileSpreadsheet } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Link,
  Stack,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import {
  absoluteDownloadUrl,
  downloadCursorPullFile,
  fetchCopilotPullRuns,
  fetchCursorPullRuns,
  fetchOpenaiPullRuns,
  type CursorPullRun,
  type CursorPullRunList,
} from "@/api/files";
import { DataTable, type Column } from "@/components/data-display/DataTable";
import { EmptyState } from "@/components/feedback/EmptyState";
import { appBasePath, appPath, resolveApiBase } from "@/lib/paths";

const VERIFICATION_FILENAME = "calculation-verification.xlsx";

function formatPeriod(run: CursorPullRun): string {
  if (run.since && run.until) {
    return `${run.since.slice(0, 10)} → ${run.until.slice(0, 10)}`;
  }
  return run.runId;
}

function fullStoragePath(storageRoot: string, storagePath: string): string {
  const root = storageRoot.replace(/\\/g, "/").replace(/\/$/, "");
  return `${root}/${storagePath}`;
}

function buildColumns(
  data: CursorPullRunList | undefined,
  downloadLabel: string,
): Column<CursorPullRun>[] {
  return [
    {
      key: "runId",
      header: "Sync run",
      sortable: true,
    },
    {
      key: "toolId",
      header: "Tool id",
      sortable: true,
    },
    {
      key: "storagePath",
      header: "Storage path",
      render: (row) =>
        data ? (
          <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: 12 }}>
            {fullStoragePath(data.storageRoot, row.storagePath)}
          </Typography>
        ) : (
          row.storagePath
        ),
    },
    {
      key: "period",
      header: "Period",
      render: (row) => formatPeriod(row),
    },
    {
      key: "pulledRecords",
      header: "Pulled",
      align: "right",
      render: (row) => row.pulledRecords ?? "—",
    },
    {
      key: "download",
      header: "Excel",
      render: (row) =>
        row.verificationExcelPath ? (
          <Stack spacing={0.5}>
            <Button
              size="small"
              startIcon={<IconDownload size={16} />}
              onClick={() =>
                void downloadCursorPullFile(
                  row.verificationExcelPath!,
                  VERIFICATION_FILENAME,
                )
              }
            >
              {downloadLabel}
            </Button>
            <Typography variant="caption" color="text.secondary" sx={{ fontFamily: "monospace" }}>
              {absoluteDownloadUrl(row.verificationExcelPath)}
            </Typography>
          </Stack>
        ) : (
          "—"
        ),
    },
  ];
}

function VerificationSection({
  title,
  description,
  emptyDescription,
  data,
  isLoading,
  error,
  refetch,
}: {
  title: string;
  description: string;
  emptyDescription: string;
  data: CursorPullRunList | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}) {
  const runs = data?.runs ?? [];
  const columns = buildColumns(data, "Download");

  return (
    <Box sx={{ mb: 4 }}>
      <Stack spacing={1} sx={{ mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
        {data && (
          <Typography variant="body2" color="text.secondary">
            Files on disk: <code>{data.cursorPullsDir}</code>
          </Typography>
        )}
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error.message}
        </Alert>
      )}

      {isLoading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress size={28} />
        </Box>
      ) : runs.length === 0 ? (
        <EmptyState
          icon={IconFileSpreadsheet}
          title="No verification dumps yet"
          description={emptyDescription}
          action={{
            label: "Refresh",
            onClick: () => void refetch(),
          }}
        />
      ) : (
        <DataTable
          columns={columns}
          rows={runs}
          rowKey={(row) => `${row.toolId}-${row.runId}`}
        />
      )}
    </Box>
  );
}

export function CursorVerificationPage() {
  const [searchParams] = useSearchParams();
  const toolId = searchParams.get("toolId");
  const runId = searchParams.get("runId");
  const provider = searchParams.get("provider") ?? "cursor";
  const autoDownload = searchParams.get("download") === "1";
  const pagePath = appPath("/files/cursor-verification");
  const basePath = appBasePath();

  const cursorQuery = useQuery({
    queryKey: ["cursor-pull-runs"],
    queryFn: fetchCursorPullRuns,
  });

  const copilotQuery = useQuery({
    queryKey: ["copilot-pull-runs"],
    queryFn: fetchCopilotPullRuns,
  });

  const openaiQuery = useQuery({
    queryKey: ["openai-pull-runs"],
    queryFn: fetchOpenaiPullRuns,
  });

  const activeData =
    provider === "copilot"
      ? copilotQuery.data
      : provider === "openai"
        ? openaiQuery.data
        : cursorQuery.data;

  const filteredRun = useMemo(() => {
    if (!toolId || !runId) {
      return null;
    }
    const runs = activeData?.runs ?? [];
    return runs.find((row) => row.toolId === toolId && row.runId === runId) ?? null;
  }, [activeData?.runs, runId, toolId]);

  useEffect(() => {
    if (!autoDownload || !filteredRun?.verificationExcelPath) {
      return;
    }
    void downloadCursorPullFile(
      filteredRun.verificationExcelPath,
      VERIFICATION_FILENAME,
    );
  }, [autoDownload, filteredRun]);

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={1} sx={{ mb: 3 }}>
        <Typography variant="h5">Calculation verification files</Typography>
        <Typography variant="body2" color="text.secondary">
          Each sync writes <strong>{VERIFICATION_FILENAME}</strong> plus raw JSON under the API
          storage volume so you can compare provider API fields to parsed ingest values.
        </Typography>
        <Alert severity="info" sx={{ mt: 1 }}>
          <Typography variant="body2" component="div">
            <strong>Page URL (local dev on port 5173):</strong>
            <br />
            <code>http://localhost:5173/files/cursor-verification</code>
            <br />
            <strong>Page URL (production with /aitool prefix):</strong>
            <br />
            <code>{window.location.origin}{basePath || ""}/files/cursor-verification</code>
            <br />
            <strong>Current app path:</strong> <code>{pagePath}</code>
          </Typography>
        </Alert>
      </Stack>

      {toolId && runId && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {filteredRun ? (
            <>
              Selected {provider} run <strong>{runId}</strong> for tool <strong>{toolId}</strong>.
              {activeData && (
                <>
                  {" "}
                  Path:{" "}
                  <code>{fullStoragePath(activeData.storageRoot, filteredRun.storagePath)}</code>
                </>
              )}
              {filteredRun.verificationExcelPath && (
                <>
                  {" "}
                  <Link
                    component="button"
                    type="button"
                    onClick={() =>
                      void downloadCursorPullFile(
                        filteredRun.verificationExcelPath!,
                        VERIFICATION_FILENAME,
                      )
                    }
                  >
                    Download Excel
                  </Link>
                </>
              )}
            </>
          ) : (
            <>
              Run not found. Trigger a {provider} sync with dumps enabled, then refresh.
            </>
          )}
        </Alert>
      )}

      <VerificationSection
        title="Cursor"
        description="Filtered usage events and daily usage rows with included vs billable cost rules."
        emptyDescription="Set CURSOR_PULL_DUMP_ENABLED=true and run a Cursor collector sync. Dumps appear under cursor-pulls/."
        data={cursorQuery.data}
        isLoading={cursorQuery.isLoading}
        error={cursorQuery.error instanceof Error ? cursorQuery.error : null}
        refetch={() => void cursorQuery.refetch()}
      />

      <VerificationSection
        title="GitHub Copilot"
        description="User metrics reports (tokens, chat/cli/agent flags) and billing seats with parsed token totals. Each row shows raw API fields, bind rules, final pull inclusion, and ingest status."
        emptyDescription="Set COPILOT_PULL_DUMP_ENABLED=true, connect Copilot credentials with a GitHub org id, and sync. Dumps appear under copilot-pulls/."
        data={copilotQuery.data}
        isLoading={copilotQuery.isLoading}
        error={copilotQuery.error instanceof Error ? copilotQuery.error : null}
        refetch={() => void copilotQuery.refetch()}
      />

      <VerificationSection
        title="OpenAI"
        description="Organization usage buckets (completions, embeddings, images, moderations) and daily costs with parsed token totals and allocated spend."
        emptyDescription="Set OPENAI_PULL_DUMP_ENABLED=true, connect an OpenAI Admin API key, and sync. Dumps appear under openai-pulls/."
        data={openaiQuery.data}
        isLoading={openaiQuery.isLoading}
        error={openaiQuery.error instanceof Error ? openaiQuery.error : null}
        refetch={() => void openaiQuery.refetch()}
      />

      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 2 }}>
        API base: {resolveApiBase()}
      </Typography>
    </Box>
  );
}

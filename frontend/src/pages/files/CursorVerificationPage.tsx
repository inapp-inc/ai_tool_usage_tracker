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
  fetchCursorPullRuns,
  type CursorPullRun,
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

export function CursorVerificationPage() {
  const [searchParams] = useSearchParams();
  const toolId = searchParams.get("toolId");
  const runId = searchParams.get("runId");
  const autoDownload = searchParams.get("download") === "1";
  const pagePath = appPath("/files/cursor-verification");
  const basePath = appBasePath();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["cursor-pull-runs"],
    queryFn: fetchCursorPullRuns,
  });

  const runs = data?.runs ?? [];

  const filteredRun = useMemo(() => {
    if (!toolId || !runId) {
      return null;
    }
    return runs.find((row) => row.toolId === toolId && row.runId === runId) ?? null;
  }, [runs, runId, toolId]);

  useEffect(() => {
    if (!autoDownload || !filteredRun?.verificationExcelPath) {
      return;
    }
    void downloadCursorPullFile(
      filteredRun.verificationExcelPath,
      VERIFICATION_FILENAME,
    );
  }, [autoDownload, filteredRun]);

  const columns: Column<CursorPullRun>[] = [
    {
      key: "runId",
      header: "Sync run",
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
              Download
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

  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={1} sx={{ mb: 3 }}>
        <Typography variant="h5">Cursor calculation verification</Typography>
        <Typography variant="body2" color="text.secondary">
          Each Cursor sync writes dumps under{" "}
          <strong>{VERIFICATION_FILENAME}</strong> in the API container storage volume.
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
        {data && (
          <Typography variant="body2" color="text.secondary">
            Files on disk: <code>{data.cursorPullsDir}</code>
          </Typography>
        )}
      </Stack>

      {toolId && runId && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {filteredRun ? (
            <>
              Selected run <strong>{runId}</strong> for tool <strong>{toolId}</strong>.
              {data && (
                <>
                  {" "}
                  Path:{" "}
                  <code>{fullStoragePath(data.storageRoot, filteredRun.storagePath)}</code>
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
            <>Run not found. Trigger a Cursor sync with dumps enabled, then refresh.</>
          )}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error instanceof Error ? error.message : "Failed to load verification files."}
        </Alert>
      )}

      {isLoading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      ) : runs.length === 0 ? (
        <EmptyState
          icon={IconFileSpreadsheet}
          title="No verification dumps yet"
          description="Set CURSOR_PULL_DUMP_ENABLED=true and run a Cursor collector sync. Dumps appear under cursor-pulls/ in the API storage volume."
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

      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 2 }}>
        API base: {resolveApiBase()}
      </Typography>
    </Box>
  );
}

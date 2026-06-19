import { apiFetch } from "./client";
import { resolveApiBase } from "@/lib/paths";

export interface CursorPullFile {
  name: string;
  downloadPath: string;
}

export interface CursorPullRun {
  toolId: string;
  runId: string;
  storagePath: string;
  since: string | null;
  until: string | null;
  pulledRecords: number | null;
  ingestedNew: number | null;
  skippedDuplicates: number | null;
  hasVerificationExcel: boolean;
  verificationExcelPath: string | null;
  files: CursorPullFile[];
}

export interface CursorPullRunList {
  storageRoot: string;
  cursorPullsDir: string;
  runs: CursorPullRun[];
}

interface ApiCursorPullFile {
  name: string;
  download_path: string;
}

interface ApiCursorPullRun {
  tool_id: string;
  run_id: string;
  storage_path: string;
  since: string | null;
  until: string | null;
  pulled_records: number | null;
  ingested_new: number | null;
  skipped_duplicates: number | null;
  has_verification_excel: boolean;
  verification_excel_path: string | null;
  files: ApiCursorPullFile[];
}

interface ApiCursorPullRunListResponse {
  storage_root: string;
  cursor_pulls_dir: string;
  data: ApiCursorPullRun[];
}

function mapRun(row: ApiCursorPullRun): CursorPullRun {
  return {
    toolId: row.tool_id,
    runId: row.run_id,
    storagePath: row.storage_path,
    since: row.since,
    until: row.until,
    pulledRecords: row.pulled_records,
    ingestedNew: row.ingested_new,
    skippedDuplicates: row.skipped_duplicates,
    hasVerificationExcel: row.has_verification_excel,
    verificationExcelPath: row.verification_excel_path,
    files: row.files.map((file) => ({
      name: file.name,
      downloadPath: file.download_path,
    })),
  };
}

export async function fetchCursorPullRuns(): Promise<CursorPullRunList> {
  const response = await apiFetch("/files/cursor-pulls");
  if (!response.ok) {
    const message =
      response.status === 401
        ? "Session expired. Please sign in again."
        : `Failed to load verification files (${response.status}).`;
    throw new Error(message);
  }
  const payload = (await response.json()) as ApiCursorPullRunListResponse;
  return {
    storageRoot: payload.storage_root,
    cursorPullsDir: payload.cursor_pulls_dir,
    runs: payload.data.map(mapRun),
  };
}

export async function downloadCursorPullFile(downloadPath: string, filename: string): Promise<void> {
  const response = await apiFetch(downloadPath);
  if (!response.ok) {
    throw new Error(`Download failed (${response.status})`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function absoluteDownloadUrl(downloadPath: string): string {
  return `${resolveApiBase()}${downloadPath}`;
}

export const filesApi = {
  fetchCursorPullRuns,
  downloadCursorPullFile,
  absoluteDownloadUrl,
};

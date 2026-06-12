const MOCK_LATENCY_MS = 400;
const UPLOAD_COMPLETE_DELAY_MS = 1000;

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), ms);
  });
}

export type UploadFormat = "csv" | "json";

export interface UploadRecord {
  id: string;
  fileName: string;
  format: UploadFormat;
  status: "pending" | "processing" | "completed" | "error";
  rowCount: number | null;
  errorCount: number | null;
  errorMessage: string | null;
  uploadedByName: string;
  teamId: string | null;
  teamName: string | null;
  fileSizeKb: number;
  createdAt: string;
  processedAt: string | null;
}

export interface UploadPreviewRow {
  rowIndex: number;
  userId: string;
  userName: string;
  model: string;
  tokens: number;
  cost: number;
  timestamp: string;
  status: "valid" | "error";
  errorReason: string | null;
}

export interface UploadPreview {
  uploadId: string;
  fileName: string;
  totalRows: number;
  validRows: number;
  errorRows: number;
  rows: UploadPreviewRow[];
}

export interface SubmitUploadRequest {
  teamId: string | null;
}

const TEAM_NAMES: Record<string, string> = {
  team_1: "Engineering",
  team_2: "Data Science",
  team_3: "Design",
  team_4: "Marketing",
  team_5: "Support",
  team_6: "Operations",
};

function resolveTeamName(teamId: string | null): string | null {
  if (!teamId) {
    return null;
  }
  return TEAM_NAMES[teamId] ?? null;
}

function inferFormat(fileName: string): UploadFormat {
  return fileName.toLowerCase().endsWith(".json") ? "json" : "csv";
}

function buildPreviewRows(): UploadPreviewRow[] {
  const models = ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro", "gpt-4o-mini"];
  const users = [
    { id: "user_1", name: "Alan Chen" },
    { id: "user_2", name: "Jordan Lee" },
    { id: "user_3", name: "Sam Rivera" },
    { id: "user_4", name: "Taylor Kim" },
    { id: "user_5", name: "Morgan Patel" },
  ];

  const rows: UploadPreviewRow[] = [];

  for (let index = 1; index <= 20; index += 1) {
    const user = users[(index - 1) % users.length];
    const isError = index === 7 || index === 15;

    rows.push({
      rowIndex: index,
      userId: user.id,
      userName: user.name,
      model: models[(index - 1) % models.length],
      tokens: 1200 + index * 340,
      cost: Number((0.012 + index * 0.004).toFixed(3)),
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * index).toISOString(),
      status: isError ? "error" : "valid",
      errorReason: isError
        ? index === 7
          ? "Invalid token count — must be a positive integer"
          : "Unknown model identifier"
        : null,
    });
  }

  return rows;
}

let mockUploads: UploadRecord[] = [
  {
    id: "upload_1",
    fileName: "june-usage-export.csv",
    format: "csv",
    status: "completed",
    rowCount: 1842,
    errorCount: 0,
    errorMessage: null,
    uploadedByName: "Alan Chen",
    teamId: null,
    teamName: null,
    fileSizeKb: 256,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    processedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3 + 60000).toISOString(),
  },
  {
    id: "upload_2",
    fileName: "engineering-usage.json",
    format: "json",
    status: "completed",
    rowCount: 420,
    errorCount: 12,
    errorMessage: null,
    uploadedByName: "Jordan Lee",
    teamId: "team_1",
    teamName: "Engineering",
    fileSizeKb: 98,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
    processedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2 + 45000).toISOString(),
  },
  {
    id: "upload_3",
    fileName: "daily-snapshot.csv",
    format: "csv",
    status: "processing",
    rowCount: null,
    errorCount: null,
    errorMessage: null,
    uploadedByName: "Sam Rivera",
    teamId: "team_2",
    teamName: "Data Science",
    fileSizeKb: 64,
    createdAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    processedAt: null,
  },
  {
    id: "upload_4",
    fileName: "pending-import.json",
    format: "json",
    status: "pending",
    rowCount: null,
    errorCount: null,
    errorMessage: null,
    uploadedByName: "Taylor Kim",
    teamId: null,
    teamName: null,
    fileSizeKb: 32,
    createdAt: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    processedAt: null,
  },
  {
    id: "upload_5",
    fileName: "corrupted-export.csv",
    format: "csv",
    status: "error",
    rowCount: null,
    errorCount: null,
    errorMessage: "File could not be parsed — missing required column 'tokens'",
    uploadedByName: "Morgan Patel",
    teamId: "team_3",
    teamName: "Design",
    fileSizeKb: 12,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    processedAt: null,
  },
  {
    id: "upload_6",
    fileName: "support-weekly.json",
    format: "json",
    status: "completed",
    rowCount: 156,
    errorCount: 0,
    errorMessage: null,
    uploadedByName: "Riley Brooks",
    teamId: "team_5",
    teamName: "Support",
    fileSizeKb: 44,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
    processedAt: new Date(Date.now() - 1000 * 60 * 60 * 12 + 30000).toISOString(),
  },
];

export async function fetchUploads(): Promise<UploadRecord[]> {
  return delay([...mockUploads]);
}

export async function uploadFile(
  file: File,
  teamId: string | null,
): Promise<UploadRecord> {
  const record: UploadRecord = {
    id: `upload_${Date.now()}`,
    fileName: file.name,
    format: inferFormat(file.name),
    status: "processing",
    rowCount: null,
    errorCount: null,
    errorMessage: null,
    uploadedByName: "Alan Chen",
    teamId,
    teamName: resolveTeamName(teamId),
    fileSizeKb: Math.max(1, Math.round(file.size / 1024)),
    createdAt: new Date().toISOString(),
    processedAt: null,
  };

  mockUploads = [record, ...mockUploads];

  setTimeout(() => {
    const index = mockUploads.findIndex((upload) => upload.id === record.id);
    if (index === -1) {
      return;
    }

    mockUploads = [
      ...mockUploads.slice(0, index),
      {
        ...mockUploads[index],
        status: "completed",
        rowCount: 20,
        errorCount: 2,
        processedAt: new Date().toISOString(),
      },
      ...mockUploads.slice(index + 1),
    ];
  }, UPLOAD_COMPLETE_DELAY_MS);

  return delay(record);
}

export async function fetchUploadPreview(id: string): Promise<UploadPreview> {
  const upload = mockUploads.find((item) => item.id === id);
  const rows = buildPreviewRows();
  const errorRows = rows.filter((row) => row.status === "error").length;

  const preview: UploadPreview = {
    uploadId: id,
    fileName: upload?.fileName ?? "upload-preview.csv",
    totalRows: rows.length,
    validRows: rows.length - errorRows,
    errorRows,
    rows,
  };

  return delay(preview);
}

export async function submitUpload(
  id: string,
  body: SubmitUploadRequest,
): Promise<UploadRecord> {
  const index = mockUploads.findIndex((upload) => upload.id === id);
  if (index === -1) {
    throw new Error("Upload not found");
  }

  const updated: UploadRecord = {
    ...mockUploads[index],
    teamId: body.teamId,
    teamName: resolveTeamName(body.teamId),
    status: "processing",
    processedAt: null,
  };

  mockUploads = [
    ...mockUploads.slice(0, index),
    updated,
    ...mockUploads.slice(index + 1),
  ];

  return delay(updated);
}

export async function deleteUpload(id: string): Promise<void> {
  mockUploads = mockUploads.filter((upload) => upload.id !== id);
  await delay(undefined);
}

export const uploadsApi = {
  fetchUploads,
  uploadFile,
  fetchUploadPreview,
  submitUpload,
  deleteUpload,
};

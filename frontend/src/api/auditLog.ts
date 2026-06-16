import { apiRequest } from "./client";
import {
  buildAuditExportBody,
  buildAuditLogQuery,
  mapApiAuditLogEntry,
  type ApiAuditLogEntry,
} from "./adapters/auditLog";

export type AuditAction =
  | "user.invite"
  | "user.remove"
  | "user.role_change"
  | "team.create"
  | "team.update"
  | "team.delete"
  | "tool.connect"
  | "tool.update"
  | "tool.delete"
  | "credential.generate"
  | "credential.revoke"
  | "alert.create"
  | "alert.update"
  | "alert.delete"
  | "upload.submit"
  | "upload.delete"
  | "report.generate"
  | "report.delete"
  | "auth.login"
  | "auth.logout";

export type AuditCategory =
  | "auth"
  | "user"
  | "team"
  | "tool"
  | "credential"
  | "alert"
  | "upload"
  | "report";

export interface AuditLogEntry {
  id: string;
  action: AuditAction;
  category: AuditCategory;
  actorName: string;
  actorEmail: string;
  actorRole: string;
  targetType: string | null;
  targetName: string | null;
  description: string;
  ipAddress: string;
  createdAt: string;
}

export interface AuditLogFilters {
  search: string;
  category: AuditCategory | "";
  from: string;
  to: string;
}

export async function fetchAuditLog(
  filters: AuditLogFilters,
): Promise<AuditLogEntry[]> {
  const query = buildAuditLogQuery(filters);
  const rows = await apiRequest<ApiAuditLogEntry[]>(`/audit-logs?${query}`);
  return rows.map(mapApiAuditLogEntry);
}

export async function exportAuditLog(filters: AuditLogFilters): Promise<void> {
  const body = buildAuditExportBody(filters);
  if (!body.from || !body.to) {
    throw new Error("Select a from and to date to export audit logs.");
  }

  const { apiFetch, ApiClientError, parseApiError } = await import("./client");
  const response = await apiFetch("/audit-logs/export", {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new ApiClientError(await parseApiError(response));
  }

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match?.[1] ?? `audit-log-${new Date().toISOString().slice(0, 10)}.csv`;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export const auditLogApi = {
  fetchAuditLog,
  exportAuditLog,
};

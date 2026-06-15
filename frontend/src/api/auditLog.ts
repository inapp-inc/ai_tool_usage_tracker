import { endOfDay, parseISO, startOfDay } from "date-fns";

import { apiRequest } from "./client";

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

interface BackendAuditEntry {
  id: string;
  action: AuditAction;
  category: AuditCategory;
  actor_name: string;
  actor_email: string;
  actor_role: string;
  target_type: string | null;
  target_name: string | null;
  description: string;
  ip_address: string;
  created_at: string;
}

function mapAuditEntry(row: BackendAuditEntry): AuditLogEntry {
  return {
    id: row.id,
    action: row.action,
    category: row.category,
    actorName: row.actor_name,
    actorEmail: row.actor_email,
    actorRole: row.actor_role,
    targetType: row.target_type,
    targetName: row.target_name,
    description: row.description,
    ipAddress: row.ip_address ?? "",
    createdAt: row.created_at,
  };
}

function filterClientSide(
  rows: AuditLogEntry[],
  filters: AuditLogFilters,
): AuditLogEntry[] {
  const fromDate = filters.from ? startOfDay(parseISO(filters.from)) : null;
  const toDate = filters.to ? endOfDay(parseISO(filters.to)) : null;

  return rows.filter((entry) => {
    if (filters.category && entry.category !== filters.category) {
      return false;
    }
    if (filters.search.trim()) {
      const haystack = [
        entry.description,
        entry.actorName,
        entry.actorEmail,
        entry.targetName ?? "",
        entry.action,
      ]
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(filters.search.trim().toLowerCase())) {
        return false;
      }
    }
    if (fromDate || toDate) {
      const createdAt = parseISO(entry.createdAt);
      if (fromDate && createdAt < fromDate) return false;
      if (toDate && createdAt > toDate) return false;
    }
    return true;
  });
}

export async function fetchAuditLog(
  filters: AuditLogFilters,
): Promise<AuditLogEntry[]> {
  const params = new URLSearchParams();
  if (filters.search.trim()) params.set("search", filters.search.trim());
  if (filters.category) params.set("category", filters.category);
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);

  const query = params.toString();
  const rows = await apiRequest<BackendAuditEntry[]>(
    `/audit-log${query ? `?${query}` : ""}`,
  );
  return filterClientSide(rows.map(mapAuditEntry), filters);
}

export const auditLogApi = {
  fetchAuditLog,
};

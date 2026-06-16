/** Maps OpenAPI audit log entries to frontend AuditLogEntry. */

import { formatRoleLabel } from "./formatRoleLabel";
import type {
  AuditAction,
  AuditCategory,
  AuditLogEntry,
} from "../auditLog";

export interface ApiAuditLogEntry {
  id: string;
  actor_id?: string | null;
  actor_email?: string | null;
  actor_display_name?: string | null;
  actor_role?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  resource_name?: string | null;
  description: string;
  outcome: string;
  source_ip?: string | null;
  correlation_id?: string | null;
  created_at: string;
}

const RESOURCE_TO_CATEGORY: Record<string, AuditCategory> = {
  auth: "auth",
  user: "user",
  team: "team",
  tool: "tool",
  credential: "credential",
  alert: "alert",
  upload: "upload",
  report: "report",
};

const ACTION_ALIASES: Record<string, AuditAction> = {
  "user.update": "user.role_change",
  "credential.update": "credential.generate",
  "credential.rotate": "credential.generate",
};

const TARGET_TYPE_LABELS: Record<string, string> = {
  auth: "Session",
  user: "User",
  team: "Team",
  tool: "Tool",
  credential: "Credential",
  alert: "Alert",
  upload: "Upload",
  report: "Report",
};

function mapAction(action: string): AuditAction {
  if (ACTION_ALIASES[action]) {
    return ACTION_ALIASES[action];
  }
  const known: AuditAction[] = [
    "user.invite",
    "user.remove",
    "user.role_change",
    "team.create",
    "team.update",
    "team.delete",
    "tool.connect",
    "tool.update",
    "tool.delete",
    "credential.generate",
    "credential.revoke",
    "alert.create",
    "alert.update",
    "alert.delete",
    "upload.submit",
    "upload.delete",
    "report.generate",
    "report.delete",
    "auth.login",
    "auth.logout",
  ];
  if (known.includes(action as AuditAction)) {
    return action as AuditAction;
  }
  return "auth.login";
}

export function mapApiAuditLogEntry(api: ApiAuditLogEntry): AuditLogEntry {
  const category = RESOURCE_TO_CATEGORY[api.resource_type] ?? "auth";
  return {
    id: api.id,
    action: mapAction(api.action),
    category,
    actorName: api.actor_display_name ?? api.actor_email ?? "System",
    actorEmail: api.actor_email ?? "",
    actorRole: formatRoleLabel(api.actor_role),
    targetType: TARGET_TYPE_LABELS[api.resource_type] ?? api.resource_type,
    targetName: api.resource_name ?? null,
    description: api.description,
    ipAddress: api.source_ip ?? "—",
    createdAt: api.created_at,
  };
}

export function categoryToResourceType(category: AuditCategory | ""): string | undefined {
  if (!category || category === "") {
    return undefined;
  }
  return category;
}

export function buildAuditLogQuery(filters: {
  search: string;
  category: AuditCategory | "";
  from: string;
  to: string;
}): string {
  const params = new URLSearchParams();
  if (filters.from) {
    params.set("from", `${filters.from}T00:00:00.000Z`);
  }
  if (filters.to) {
    params.set("to", `${filters.to}T23:59:59.999Z`);
  }
  const resourceType = categoryToResourceType(filters.category);
  if (resourceType) {
    params.set("resource_type", resourceType);
  }
  if (filters.search.trim()) {
    params.set("q", filters.search.trim());
  }
  params.set("limit", "500");
  return params.toString();
}

export function buildAuditExportBody(filters: {
  from: string;
  to: string;
  category: AuditCategory | "";
  search: string;
}): Record<string, string> {
  const body: Record<string, string> = {};
  if (filters.from) {
    body.from = `${filters.from}T00:00:00.000Z`;
  }
  if (filters.to) {
    body.to = `${filters.to}T23:59:59.999Z`;
  }
  const resourceType = categoryToResourceType(filters.category);
  if (resourceType) {
    body.resource_type = resourceType;
  }
  if (filters.search.trim()) {
    body.q = filters.search.trim();
  }
  return body;
}

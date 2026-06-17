/** Maps OpenAPI Credential responses to frontend Credential shape. */

import type {
  CreateCredentialRequest,
  Credential,
  SyncSchedule,
  UpdateCredentialRequest,
} from "../credentials";

export const SYNC_SCHEDULE_MINUTES: Record<SyncSchedule, number> = {
  hourly: 60,
  daily: 1440,
};

export function syncScheduleFromMinutes(minutes: number): SyncSchedule {
  return minutes >= 720 ? "daily" : "hourly";
}

export function syncScheduleLabel(schedule: SyncSchedule): string {
  return schedule === "daily" ? "Daily" : "Hourly";
}

export interface ApiCredential {
  id: string;
  label: string;
  description: string;
  vendor: string;
  catalogue_tool_id?: string | null;
  catalogue_tool_name?: string | null;
  tool_id: string;
  tool_name: string;
  team_id?: string | null;
  team_name?: string | null;
  api_endpoint?: string | null;
  masked_secret: string;
  status: "active" | "inactive";
  pull_interval_minutes?: number;
  rotation_reminder_days?: number | null;
  expires_at?: string | null;
  last_used_at?: string | null;
  created_at: string;
  created_by_name?: string | null;
}

export interface ApiCredentialCreateResponse {
  credential: ApiCredential;
  plain_secret: string;
}

export function mapApiCredential(api: ApiCredential): Credential {
  const pullIntervalMinutes = api.pull_interval_minutes ?? 60;
  return {
    id: api.id,
    label: api.label,
    description: api.description,
    provider: api.vendor,
    catalogueToolId: api.catalogue_tool_id ?? "",
    catalogueToolName: api.catalogue_tool_name ?? api.tool_name,
    apiEndpoint: api.api_endpoint ?? null,
    toolId: api.tool_id,
    toolName: api.catalogue_tool_name ?? api.tool_name,
    teamId: api.team_id ?? "",
    teamName: api.team_name ?? "Unassigned",
    keyMasked: api.masked_secret,
    status: api.status,
    syncSchedule: syncScheduleFromMinutes(pullIntervalMinutes),
    pullIntervalMinutes,
    rotationReminderDays: api.rotation_reminder_days ?? null,
    expiresAt: api.expires_at ?? null,
    lastUsedAt: api.last_used_at ?? null,
    createdAt: api.created_at,
    createdByName: api.created_by_name ?? "—",
  };
}

export function toCredentialCreateBody(body: CreateCredentialRequest): {
  label: string;
  description: string;
  tool_id: string;
  team_id: string;
  secret_value: string;
  pull_interval_minutes: number;
  rotation_reminder_days: number | null;
  expires_at: string | null;
} {
  return {
    label: body.label,
    description: body.description,
    tool_id: body.catalogueToolId,
    team_id: body.teamId,
    secret_value: body.apiKey,
    pull_interval_minutes: SYNC_SCHEDULE_MINUTES[body.syncSchedule],
    rotation_reminder_days: body.rotationReminderDays,
    expires_at: body.expiresAt,
  };
}

export function toCredentialUpdateBody(
  body: UpdateCredentialRequest,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  if (body.label !== undefined) {
    payload.label = body.label;
  }
  if (body.description !== undefined) {
    payload.description = body.description;
  }
  if (body.teamId !== undefined) {
    payload.team_id = body.teamId;
  }
  if (body.apiKey !== undefined && body.apiKey.trim()) {
    payload.secret_value = body.apiKey.trim();
  }
  if (body.syncSchedule !== undefined) {
    payload.pull_interval_minutes = SYNC_SCHEDULE_MINUTES[body.syncSchedule];
  }
  if (body.rotationReminderDays !== undefined) {
    payload.rotation_reminder_days = body.rotationReminderDays;
  }
  if (body.expiresAt !== undefined) {
    payload.expires_at = body.expiresAt;
  }
  if (body.status !== undefined) {
    payload.active = body.status === "active";
  }
  return payload;
}

/** Maps OpenAPI Credential responses to frontend Credential shape. */

import type {
  CreateCredentialRequest,
  Credential,
  CredentialEnvironment,
  UpdateCredentialRequest,
} from "../credentials";

export interface ApiCredential {
  id: string;
  label: string;
  description: string;
  tool_id: string;
  tool_name: string;
  team_id?: string | null;
  team_name?: string | null;
  environment: CredentialEnvironment;
  masked_secret: string;
  status: "active" | "inactive";
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
  return {
    id: api.id,
    label: api.label,
    description: api.description,
    toolId: api.tool_id,
    toolName: api.tool_name,
    teamId: api.team_id ?? "",
    teamName: api.team_name ?? "Unassigned",
    environment: api.environment,
    keyMasked: api.masked_secret,
    status: api.status,
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
  environment: CredentialEnvironment;
  secret_value: string;
  rotation_reminder_days: number | null;
  expires_at: string | null;
} {
  return {
    label: body.label,
    description: body.description,
    tool_id: body.toolId,
    team_id: body.teamId,
    environment: body.environment,
    secret_value: body.apiKey,
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
  if (body.toolId !== undefined) {
    payload.tool_id = body.toolId;
  }
  if (body.teamId !== undefined) {
    payload.team_id = body.teamId;
  }
  if (body.environment !== undefined) {
    payload.environment = body.environment;
  }
  if (body.apiKey !== undefined && body.apiKey.trim()) {
    payload.secret_value = body.apiKey.trim();
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

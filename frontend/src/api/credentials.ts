import { apiRequest } from "./client";
import {
  mapApiCredential,
  toCredentialCreateBody,
  toCredentialUpdateBody,
  type ApiCredential,
  type ApiCredentialCreateResponse,
} from "./adapters/credentials";

export type SyncSchedule = "hourly" | "daily";

export interface Credential {
  id: string;
  label: string;
  description: string;
  provider: string;
  catalogueToolId: string;
  catalogueToolName: string;
  apiEndpoint: string | null;
  toolId: string;
  toolName: string;
  teamId: string;
  teamName: string;
  keyMasked: string;
  status: "active" | "inactive";
  syncSchedule: SyncSchedule;
  pullIntervalMinutes: number;
  rotationReminderDays: number | null;
  expiresAt: string | null;
  lastUsedAt: string | null;
  createdAt: string;
  createdByName: string;
}

export interface CreateCredentialRequest {
  label: string;
  description: string;
  catalogueToolId: string;
  teamId: string;
  apiKey: string;
  syncSchedule: SyncSchedule;
  rotationReminderDays: number | null;
  expiresAt: string | null;
}

export interface CreateCredentialResponse {
  credential: Credential;
  plainKey: string;
}

export type UpdateCredentialRequest = Partial<
  Omit<CreateCredentialRequest, "apiKey" | "catalogueToolId">
> & {
  apiKey?: string;
  status?: "active" | "inactive";
};

export type { ApiCredential } from "./adapters/credentials";
export {
  syncScheduleFromMinutes,
  syncScheduleLabel,
  SYNC_SCHEDULE_MINUTES,
} from "./adapters/credentials";

export async function fetchCredentials(): Promise<Credential[]> {
  const rows = await apiRequest<ApiCredential[]>("/credentials");
  return rows.map(mapApiCredential);
}

export async function createCredential(
  body: CreateCredentialRequest,
): Promise<CreateCredentialResponse> {
  const response = await apiRequest<ApiCredentialCreateResponse>("/credentials", {
    method: "POST",
    body: JSON.stringify(toCredentialCreateBody(body)),
  });
  return {
    credential: mapApiCredential(response.credential),
    plainKey: response.plain_secret,
  };
}

export async function validateCredential(body: {
  catalogueToolId: string;
  apiKey: string;
}): Promise<{ valid: boolean; provider: string; message?: string | null }> {
  return apiRequest<{ valid: boolean; provider: string; message?: string | null }>(
    "/credentials/validate",
    {
      method: "POST",
      body: JSON.stringify({
        tool_id: body.catalogueToolId,
        secret_value: body.apiKey,
      }),
    },
  );
}

export async function updateCredential(
  id: string,
  body: UpdateCredentialRequest,
): Promise<Credential> {
  const updated = await apiRequest<ApiCredential>(`/credentials/${id}`, {
    method: "PATCH",
    body: JSON.stringify(toCredentialUpdateBody(body)),
  });
  return mapApiCredential(updated);
}

export async function revokeCredential(id: string): Promise<void> {
  await apiRequest<void>(`/credentials/${id}`, { method: "DELETE" });
}

/** Fetch full decrypted API key for clipboard copy (super_admin only). */
export async function revealCredentialSecret(id: string): Promise<string> {
  const response = await apiRequest<{ secret_value: string }>(
    `/credentials/${id}/secret`,
  );
  return response.secret_value;
}

export const credentialsApi = {
  fetchCredentials,
  createCredential,
  validateCredential,
  updateCredential,
  revokeCredential,
  revealCredentialSecret,
};

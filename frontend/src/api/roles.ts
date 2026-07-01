import { apiRequest } from "./client";

export interface RoleRecord {
  id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  created_at: string;
}

export interface PermissionRow {
  resource: string;
  can_read: boolean;
  can_write: boolean;
  team_scoped: boolean;
}

export async function fetchRoles(organizationId?: string | null): Promise<RoleRecord[]> {
  const query =
    organizationId != null && organizationId !== ""
      ? `?organization_id=${encodeURIComponent(organizationId)}`
      : "";
  const response = await apiRequest<{ data: RoleRecord[] } | RoleRecord[]>(
    `/roles${query}`,
  );
  return Array.isArray(response) ? response : response.data;
}

export interface PermissionMatrixResponse {
  data: PermissionRow[];
}

function unwrapPermissionRows(
  response: PermissionRow[] | PermissionMatrixResponse,
): PermissionRow[] {
  return Array.isArray(response) ? response : response.data;
}

export async function fetchRolePermissions(roleId: string): Promise<PermissionRow[]> {
  const response = await apiRequest<PermissionRow[] | PermissionMatrixResponse>(
    `/roles/${roleId}/permissions`,
  );
  return unwrapPermissionRows(response);
}

export async function updateRolePermissions(
  roleId: string,
  permissions: PermissionRow[],
): Promise<PermissionRow[]> {
  const response = await apiRequest<PermissionRow[] | PermissionMatrixResponse>(
    `/roles/${roleId}/permissions`,
    {
      method: "PUT",
      body: JSON.stringify({ permissions }),
    },
  );
  return unwrapPermissionRows(response);
}

export async function createRole(
  name: string,
  description?: string,
): Promise<RoleRecord> {
  return apiRequest<RoleRecord>("/roles", {
    method: "POST",
    body: JSON.stringify({ name, description: description ?? null }),
  });
}

export async function patchRole(
  roleId: string,
  updates: { name?: string; description?: string },
): Promise<RoleRecord> {
  return apiRequest<RoleRecord>(`/roles/${roleId}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

export async function deleteRole(roleId: string): Promise<void> {
  await apiRequest<void>(`/roles/${roleId}`, { method: "DELETE" });
}

export const rolesApi = {
  fetchRoles,
  fetchRolePermissions,
  updateRolePermissions,
  createRole,
  patchRole,
  deleteRole,
};

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

export async function fetchRoles(): Promise<RoleRecord[]> {
  return apiRequest<RoleRecord[]>("/roles");
}

export async function fetchRolePermissions(roleId: string): Promise<PermissionRow[]> {
  return apiRequest<PermissionRow[]>(`/roles/${roleId}/permissions`);
}

export async function updateRolePermissions(
  roleId: string,
  permissions: PermissionRow[],
): Promise<PermissionRow[]> {
  return apiRequest<PermissionRow[]>(`/roles/${roleId}/permissions`, {
    method: "PUT",
    body: JSON.stringify({ permissions }),
  });
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

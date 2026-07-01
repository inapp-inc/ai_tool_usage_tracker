import { create } from "zustand";

import { fetchRolePermissions } from "@/api/roles";
import { setRefreshToken } from "@/api/auth";
import { setAccessToken } from "@/api/client";
import { isOrgWideRole, isOrgWideRoleName } from "@/auth/orgWideRoles";
import { resetTenantQueryCache } from "@/lib/queryClient";
import { syncOrgScopeForUser } from "@/lib/tenantScope";
import type { User } from "@/types";

export interface PermissionEntry {
  can_read: boolean;
  can_write: boolean;
  team_scoped: boolean;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  permissionMap: Record<string, PermissionEntry>;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  loadPermissions: (roleId: string) => Promise<void>;
  canRead: (resource: string) => boolean;
  canWrite: (resource: string) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  permissionMap: {},
  setAuth: (user, token) => {
    setAccessToken(token);
    syncOrgScopeForUser(user);
    resetTenantQueryCache();
    set({ user, accessToken: token, isAuthenticated: true });
  },
  clearAuth: () => {
    setAccessToken(null);
    setRefreshToken(null);
    syncOrgScopeForUser(null);
    resetTenantQueryCache();
    set({ user: null, accessToken: null, isAuthenticated: false, permissionMap: {} });
  },
  loadPermissions: async (roleId: string) => {
    const rows = await fetchRolePermissions(roleId);
    const permissionMap: Record<string, PermissionEntry> = {};
    for (const row of rows) {
      permissionMap[row.resource] = {
        can_read: row.can_read,
        can_write: row.can_write,
        team_scoped: row.team_scoped,
      };
    }
    set({ permissionMap });
  },
  canRead: (resource: string) => {
    const state = get();
    if (
      isOrgWideRole(state.user?.platformRole) ||
      isOrgWideRoleName(state.user?.roleName)
    ) {
      return true;
    }
    const entry = state.permissionMap[resource];
    return Boolean(entry?.can_read || entry?.can_write);
  },
  canWrite: (resource: string) => {
    const state = get();
    if (
      isOrgWideRole(state.user?.platformRole) ||
      isOrgWideRoleName(state.user?.roleName)
    ) {
      return true;
    }
    const entry = state.permissionMap[resource];
    return Boolean(entry?.can_write);
  },
}));

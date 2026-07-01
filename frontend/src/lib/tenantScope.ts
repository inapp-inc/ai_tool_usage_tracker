import { Role, type User } from "@/types";
import { useOrgScopeStore } from "@/stores/orgScopeStore";

/** React Query cache partition key — prevents cross-tenant stale data after login switches. */
export function tenantScopeKey(
  user: User | null | undefined,
  selectedOrganizationId: string | null,
): string {
  if (!user) {
    return "anonymous";
  }
  if (user.platformRole === Role.SuperAdmin) {
    return selectedOrganizationId ?? "__all__";
  }
  return user.organizationId ?? "tenant";
}

/** Pin org scope after auth changes so tenant users never inherit super-admin selection. */
export function syncOrgScopeForUser(user: User | null): void {
  if (!user) {
    useOrgScopeStore.getState().setSelectedOrganizationId(null);
    return;
  }

  if (user.platformRole === Role.SuperAdmin) {
    return;
  }

  if (user.organizationId) {
    useOrgScopeStore.getState().setSelectedOrganizationId(user.organizationId);
  }
}

export function isSuperAdminWithoutOrg(
  user: User | null | undefined,
  selectedOrganizationId: string | null,
): boolean {
  return user?.platformRole === Role.SuperAdmin && !selectedOrganizationId;
}

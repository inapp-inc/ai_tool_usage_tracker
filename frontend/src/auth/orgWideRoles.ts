import { Role } from "@/types";

/** Roles with full organization-wide access (mirrors backend ORG_WIDE_ROLE_NAMES). */
export const ORG_WIDE_ROLES = new Set<Role>([Role.SuperAdmin, Role.OrgAdmin]);

export function isOrgWideRole(role: Role | undefined | null): boolean {
  return role != null && ORG_WIDE_ROLES.has(role);
}

export function isOrgWideRoleName(roleName: string | undefined | null): boolean {
  return roleName === "super_admin" || roleName === "org_admin";
}

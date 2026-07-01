const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  org_admin: "Organization Admin",
  team_admin: "Team Admin",
  finance_viewer: "Finance Viewer",
  team_member: "Team Member",
  auditor: "Auditor",
};

export const ROLES_WITHOUT_TEAMS = new Set(["super_admin", "org_admin", "organization_admin"]);

export function isOrgWideRoleName(name: string | null | undefined): boolean {
  if (!name) {
    return false;
  }
  const normalized = name.trim().toLowerCase().replace(/[\s-]+/g, "_");
  return ROLES_WITHOUT_TEAMS.has(normalized);
}

export function isOrgAdminRoleId(
  roleId: string,
  roles: ReadonlyArray<{ id: string; name: string }>,
): boolean {
  if (!roleId) {
    return false;
  }
  if (roleId === "org_admin") {
    return true;
  }
  const matched = roles.find((role) => role.id === roleId);
  return matched?.name === "org_admin";
}

export function roleRequiresTeamAssignment(
  roleId: string,
  roles: ReadonlyArray<{ id: string; name: string }>,
): boolean {
  if (!roleId) {
    return true;
  }
  const matched = roles.find(
    (role) => role.id === roleId || role.id.toLowerCase() === roleId.toLowerCase(),
  );
  const roleName = matched?.name ?? roleId;
  return !isOrgWideRoleName(roleName);
}

export function formatRoleLabel(role: string | null | undefined): string {
  if (!role) {
    return "User";
  }
  return ROLE_LABELS[role] ?? role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

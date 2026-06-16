const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  team_admin: "Team Admin",
  finance_viewer: "Finance Viewer",
  team_member: "Team Member",
  auditor: "Auditor",
};

export function formatRoleLabel(role: string | null | undefined): string {
  if (!role) {
    return "User";
  }
  return ROLE_LABELS[role] ?? role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

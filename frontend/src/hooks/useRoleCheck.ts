import { useMemo } from "react";

import { useAuthStore } from "@/stores/authStore";
import type { Role } from "@/types";

export function useRoleCheck(requiredRoles: Role[]) {
  const user = useAuthStore((state) => state.user);

  return useMemo(() => {
    if (!user) {
      return { hasRole: false, user: null };
    }

    const roles = new Set<Role>([
      user.platformRole,
      ...user.teamMemberships.map((membership) => membership.role),
    ]);

    const hasRole = requiredRoles.some((role) => roles.has(role));
    return { hasRole, user };
  }, [requiredRoles, user]);
}

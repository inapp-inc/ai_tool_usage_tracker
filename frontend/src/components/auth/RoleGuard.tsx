import type { ReactNode } from "react";

import { useAuthStore } from "@/stores/authStore";
import { Role } from "@/types";

interface RoleGuardProps {
  roles: Role[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function RoleGuard({ roles, children, fallback = null }: RoleGuardProps) {
  const user = useAuthStore((state) => state.user);

  if (!user || !roles.includes(user.platformRole)) {
    return fallback;
  }

  return children;
}

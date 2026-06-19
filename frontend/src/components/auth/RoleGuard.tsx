import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";
import { Role } from "@/types";

interface RoleGuardProps {
  /** @deprecated Use resource-based permission checks instead. */
  roles?: Role[];
  /** Resource key for permission-based guard (preferred). */
  resource?: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export function RoleGuard({
  roles,
  resource,
  children,
  fallback = null,
}: RoleGuardProps) {
  const user = useAuthStore((state) => state.user);
  const canRead = useAuthStore((state) => state.canRead);

  if (!user) {
    return fallback;
  }

  if (resource) {
    if (!canRead(resource)) {
      return fallback ?? <Navigate to="/insights" replace />;
    }
    return children;
  }

  if (roles && roles.includes(user.platformRole)) {
    return children;
  }

  return fallback ?? <Navigate to="/insights" replace />;
}

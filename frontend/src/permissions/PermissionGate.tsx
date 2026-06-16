/**
 * <RequirePage page="alerts" action="read"> — redirects to /insights if denied (route guard).
 * <PermissionGate page="alerts" action="write"> — hides children if denied (element guard).
 */
import type { ReactElement, ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { usePermissions, type PageId } from "./PermissionsContext";

type Action = "read" | "write";

// ─── Route guard ─────────────────────────────────────────────────────────────

interface RequirePageProps {
  page: PageId;
  action?: Action;
  children: ReactNode;
  redirectTo?: string;
}

export function RequirePage({
  page,
  action = "read",
  children,
  redirectTo = "/insights",
}: RequirePageProps) {
  const { loaded, canRead, canWrite } = usePermissions();
  if (!loaded) return null;
  const allowed = action === "read" ? canRead(page) : canWrite(page);
  if (!allowed) return <Navigate to={redirectTo} replace />;
  return <>{children}</>;
}

// ─── Element guard ───────────────────────────────────────────────────────────

interface PermissionGateProps {
  page: PageId;
  action: Action;
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGate({
  page,
  action,
  children,
  fallback = null,
}: PermissionGateProps) {
  const { loaded, canRead, canWrite } = usePermissions();
  if (!loaded) return null;
  const allowed = action === "read" ? canRead(page) : canWrite(page);
  return <>{allowed ? children : fallback}</>;
}

// ─── Disabled-button wrapper ──────────────────────────────────────────────────

export function WriteGate({
  page,
  children,
}: {
  page: PageId;
  children: ReactElement;
}) {
  const { loaded, canWrite } = usePermissions();
  if (!loaded || canWrite(page)) return children;
  return (
    <span title="You don't have permission to perform this action.">
      {/* Clone with disabled so the button stays visible but inert */}
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      {(children as any).type
        ? { ...children, props: { ...children.props, disabled: true } }
        : children}
    </span>
  );
}

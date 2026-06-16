/**
 * Fetches the current user's page-level access from GET /api/v1/permissions/my-access
 * immediately after login. Wrap the app inside <PermissionsProvider>.
 */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "@/api/client";
import { useAuthStore } from "@/stores/authStore";

// ─── Types ───────────────────────────────────────────────────────────────────

export type PageId =
  | "insights"
  | "admin:teams"
  | "admin:groups"
  | "admin:members"
  | "admin:credentials"
  | "alerts"
  | "uploads"
  | "audit";

export interface PageAccess {
  read: boolean;
  write: boolean;
}

interface MyAccessResponse {
  role: string;
  access: Record<string, PageAccess>;
}

interface PermissionsContextValue {
  loaded: boolean;
  canRead: (page: PageId) => boolean;
  canWrite: (page: PageId) => boolean;
  access: Record<string, PageAccess> | null;
}

// ─── Context ─────────────────────────────────────────────────────────────────

const PermissionsContext = createContext<PermissionsContextValue>({
  loaded: false,
  canRead: () => false,
  canWrite: () => false,
  access: null,
});

// ─── Provider ────────────────────────────────────────────────────────────────

export function PermissionsProvider({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const { data, isSuccess } = useQuery<MyAccessResponse>({
    queryKey: ["my-access"],
    queryFn: () => apiRequest<MyAccessResponse>("/permissions/my-access"),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // matches Redis TTL
    retry: 1,
  });

  const canRead = useCallback(
    (page: PageId) => data?.access[page]?.read ?? false,
    [data],
  );

  const canWrite = useCallback(
    (page: PageId) => data?.access[page]?.write ?? false,
    [data],
  );

  const value = useMemo<PermissionsContextValue>(
    () => ({ loaded: isSuccess, canRead, canWrite, access: data?.access ?? null }),
    [isSuccess, canRead, canWrite, data],
  );

  return (
    <PermissionsContext.Provider value={value}>
      {children}
    </PermissionsContext.Provider>
  );
}

// ─── Hooks ───────────────────────────────────────────────────────────────────

export function usePermissions(): PermissionsContextValue {
  return useContext(PermissionsContext);
}

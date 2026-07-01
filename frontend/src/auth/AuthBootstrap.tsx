import { useEffect, useState, type ReactNode } from "react";

import { restoreAuthSession } from "@/api/auth";
import { PageSkeleton } from "@/components/feedback/PageSkeleton";
import { useAuthStore } from "@/stores/authStore";

interface AuthBootstrapProps {
  children: ReactNode;
}

/** Restore session from persisted refresh token before rendering protected routes. */
export function AuthBootstrap({ children }: AuthBootstrapProps) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const session = await restoreAuthSession();
        if (!cancelled && session) {
          useAuthStore.getState().setAuth(session.user, session.accessToken);
          if (session.user.roleId) {
            await useAuthStore.getState().loadPermissions(session.user.roleId);
          }
        }
      } catch {
        if (!cancelled) {
          useAuthStore.getState().clearAuth();
        }
      } finally {
        if (!cancelled) {
          setReady(true);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  if (!ready) {
    return <PageSkeleton />;
  }

  return children;
}

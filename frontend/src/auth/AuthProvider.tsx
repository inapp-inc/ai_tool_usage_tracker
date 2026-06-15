import { useEffect, useState, type ReactNode } from "react";

import { fetchCurrentUser, getRefreshToken, restoreAuthSession } from "@/api/auth";
import { setAccessToken } from "@/api/client";
import { loadStoredAccessToken, persistAccessToken } from "@/auth/sessionStorage";
import { PageSkeleton } from "@/components/feedback/PageSkeleton";
import { useAuthStore } from "@/stores/authStore";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const setAuth = useAuthStore((state) => state.setAuth);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    if (isAuthenticated) {
      setReady(true);
      return;
    }

    let cancelled = false;

    async function bootstrapSession() {
      const storedAccess = loadStoredAccessToken();
      if (storedAccess) {
        setAccessToken(storedAccess);
        try {
          const user = await fetchCurrentUser();
          if (!cancelled) {
            setAuth(user, storedAccess);
            setReady(true);
            return;
          }
        } catch {
          setAccessToken(null);
          persistAccessToken(null);
        }
      }

      if (getRefreshToken()) {
        try {
          const session = await restoreAuthSession();
          if (!cancelled && session) {
            persistAccessToken(session.accessToken);
            setAuth(session.user, session.accessToken);
          }
        } catch {
          // Session cannot be restored; user stays logged out.
        }
      }

      if (!cancelled) {
        setReady(true);
      }
    }

    void bootstrapSession();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, setAuth]);

  if (!ready) {
    return <PageSkeleton />;
  }

  return children;
}

import { lazy, Suspense, type ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { AuthProvider } from "@/auth/AuthProvider";
import { normalizeBasePath } from "@/config/basePath";
import { AppShell } from "@/components/layout/AppShell";
import { PageSkeleton } from "@/components/feedback/PageSkeleton";

// ─── Auth ────────────────────────────────────────────────────────────────────
const LoginPage = lazy(() =>
  import("@/pages/auth/LoginPage").then((m) => ({ default: m.LoginPage })),
);

// ─── Insights ────────────────────────────────────────────────────────────────
const InsightsPage = lazy(() =>
  import("@/pages/insights/InsightsPage").then((m) => ({ default: m.InsightsPage })),
);

// ─── Alerts ───────────────────────────────────────────────────────────────────
const AlertsPage = lazy(() =>
  import("@/pages/alerts/AlertsPage").then((m) => ({ default: m.AlertsPage })),
);

// ─── Uploads ─────────────────────────────────────────────────────────────────
const UploadsPage = lazy(() =>
  import("@/pages/uploads/UploadsPage").then((m) => ({ default: m.UploadsPage })),
);
const UploadPreviewPage = lazy(() =>
  import("@/pages/uploads/UploadPreviewPage").then((m) => ({
    default: m.UploadPreviewPage,
  })),
);

// ─── Admin ───────────────────────────────────────────────────────────────────
const ToolsPage = lazy(() =>
  import("@/pages/admin/ToolsPage").then((m) => ({ default: m.ToolsPage })),
);
const TeamsPage = lazy(() =>
  import("@/pages/admin/TeamsPage").then((m) => ({ default: m.TeamsPage })),
);
const MembersPage = lazy(() =>
  import("@/pages/admin/MembersPage").then((m) => ({ default: m.MembersPage })),
);
const CredentialsPage = lazy(() =>
  import("@/pages/admin/CredentialsPage").then((m) => ({
    default: m.CredentialsPage,
  })),
);
const ProvidersPage = lazy(() =>
  import("@/pages/admin/ProvidersPage").then((m) => ({
    default: m.ProvidersPage,
  })),
);
const AuditLogPage = lazy(() =>
  import("@/pages/admin/AuditLogPage").then((m) => ({ default: m.AuditLogPage })),
);

// ─── Guard ───────────────────────────────────────────────────────────────────
function ProtectedRoute({ children }: { children: ReactElement }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

function RootRedirect() {
  const { isAuthenticated } = useAuth();
  return <Navigate to={isAuthenticated ? "/insights" : "/login"} replace />;
}

function GuestRoute({ children }: { children: ReactElement }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/insights" replace />;
  return children;
}

// ─── Routes ──────────────────────────────────────────────────────────────────
const routerBasename = normalizeBasePath(import.meta.env.VITE_BASE_PATH);

export function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route
        path="/login"
        element={
          <GuestRoute>
            <LoginPage />
          </GuestRoute>
        }
      />

      {/* Protected — wrapped in AppShell */}
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/insights" element={<InsightsPage />} />

        <Route path="/dashboard" element={<Navigate to="/insights" replace />} />
        <Route path="/usage/teams" element={<Navigate to="/insights" replace />} />
        <Route path="/usage/teams/:teamId" element={<Navigate to="/insights" replace />} />
        <Route path="/reports" element={<Navigate to="/insights" replace />} />
        <Route path="/reports/new" element={<Navigate to="/insights" replace />} />

        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/alerts/history" element={<AlertsPage />} />

        <Route path="/uploads" element={<UploadsPage />} />
        <Route path="/uploads/:uploadId/preview" element={<UploadPreviewPage />} />

        <Route path="/admin/teams" element={<ToolsPage />} />
        <Route path="/admin/tools" element={<Navigate to="/admin/teams" replace />} />
        <Route path="/admin/providers" element={<ProvidersPage />} />
        <Route path="/admin/groups" element={<TeamsPage />} />
        <Route path="/admin/members" element={<MembersPage />} />
        <Route path="/admin/credentials" element={<CredentialsPage />} />
        <Route path="/admin/audit-log" element={<AuditLogPage />} />
      </Route>

      {/* Fallback */}
      <Route path="/" element={<RootRedirect />} />
      <Route path="*" element={<Navigate to="/insights" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter basename={routerBasename}>
      <AuthProvider>
        <Suspense fallback={<PageSkeleton />}>
          <AppRoutes />
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
import { lazy, Suspense, type ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { AuthProvider } from "@/auth/AuthProvider";
import { PermissionsProvider } from "@/permissions/PermissionsContext";
import { RequirePage } from "@/permissions/PermissionGate";
import { AppShell } from "@/components/layout/AppShell";
import { PageSkeleton } from "@/components/feedback/PageSkeleton";
import { Role } from "@/types";

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
const RolePermissionsPage = lazy(() =>
  import("@/pages/admin/RolePermissionsPage").then((m) => ({
    default: m.RolePermissionsPage,
  })),
);

// ─── Guard ───────────────────────────────────────────────────────────────────
function ProtectedRoute({ children }: { children: ReactElement }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

function SuperAdminOnly({ children }: { children: ReactElement }) {
  const { user } = useAuth();
  if (user?.platformRole !== Role.SuperAdmin) return <Navigate to="/insights" replace />;
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
const routerBasename =
  import.meta.env.VITE_BASE_PATH?.replace(/\/$/, "") || undefined;

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

        <Route
          path="/alerts"
          element={
            <RequirePage page="alerts" action="read">
              <AlertsPage />
            </RequirePage>
          }
        />
        <Route path="/alerts/history" element={<AlertsPage />} />

        <Route
          path="/uploads"
          element={
            <RequirePage page="uploads" action="read">
              <UploadsPage />
            </RequirePage>
          }
        />
        <Route path="/uploads/:uploadId/preview" element={<UploadPreviewPage />} />

        <Route
          path="/admin/teams"
          element={
            <RequirePage page="admin:teams" action="read">
              <ToolsPage />
            </RequirePage>
          }
        />
        <Route path="/admin/tools" element={<Navigate to="/admin/teams" replace />} />
        <Route
          path="/admin/providers"
          element={
            <SuperAdminOnly>
              <ProvidersPage />
            </SuperAdminOnly>
          }
        />
        <Route
          path="/admin/groups"
          element={
            <RequirePage page="admin:groups" action="read">
              <TeamsPage />
            </RequirePage>
          }
        />
        <Route
          path="/admin/members"
          element={
            <RequirePage page="admin:members" action="read">
              <MembersPage />
            </RequirePage>
          }
        />
        <Route
          path="/admin/credentials"
          element={
            <RequirePage page="admin:credentials" action="read">
              <CredentialsPage />
            </RequirePage>
          }
        />
        <Route
          path="/admin/audit-log"
          element={
            <RequirePage page="audit" action="read">
              <AuditLogPage />
            </RequirePage>
          }
        />
        <Route
          path="/admin/permissions"
          element={
            <SuperAdminOnly>
              <RolePermissionsPage />
            </SuperAdminOnly>
          }
        />
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
        <PermissionsProvider>
          <Suspense fallback={<PageSkeleton />}>
            <AppRoutes />
          </Suspense>
        </PermissionsProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
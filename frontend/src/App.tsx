import { lazy, Suspense, type ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { RoleGuard } from "@/components/auth/RoleGuard";
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
const MyUsagePage = lazy(() =>
  import("@/pages/usage/MyUsagePage").then((m) => ({ default: m.MyUsagePage })),
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
const UploadMappingPage = lazy(() =>
  import("@/pages/uploads/UploadMappingPage").then((m) => ({
    default: m.UploadMappingPage,
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
const AuditLogPage = lazy(() =>
  import("@/pages/admin/AuditLogPage").then((m) => ({ default: m.AuditLogPage })),
);

// ─── Guard ───────────────────────────────────────────────────────────────────
function ProtectedRoute({ children }: { children: ReactElement }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

// ─── Routes ──────────────────────────────────────────────────────────────────
export function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />

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

        <Route path="/my-usage" element={<MyUsagePage />} />

        <Route
          path="/alerts"
          element={
            <RoleGuard roles={[Role.SuperAdmin, Role.TeamAdmin]} fallback={<Navigate to="/insights" replace />}>
              <AlertsPage />
            </RoleGuard>
          }
        />
        <Route
          path="/alerts/history"
          element={
            <RoleGuard roles={[Role.SuperAdmin, Role.TeamAdmin]} fallback={<Navigate to="/insights" replace />}>
              <AlertsPage />
            </RoleGuard>
          }
        />
        <Route
          path="/uploads"
          element={
            <RoleGuard roles={[Role.SuperAdmin, Role.TeamAdmin]} fallback={<Navigate to="/insights" replace />}>
              <UploadsPage />
            </RoleGuard>
          }
        />
        <Route
          path="/uploads/:uploadId/map"
          element={
            <RoleGuard roles={[Role.SuperAdmin, Role.TeamAdmin]} fallback={<Navigate to="/insights" replace />}>
              <UploadMappingPage />
            </RoleGuard>
          }
        />
        <Route
          path="/uploads/:uploadId/preview"
          element={
            <RoleGuard roles={[Role.SuperAdmin, Role.TeamAdmin]} fallback={<Navigate to="/insights" replace />}>
              <UploadPreviewPage />
            </RoleGuard>
          }
        />

        <Route
          path="/admin/tools"
          element={
            <RoleGuard roles={[Role.SuperAdmin]} fallback={<Navigate to="/insights" replace />}>
              <ToolsPage />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/teams"
          element={
            <RoleGuard roles={[Role.SuperAdmin]} fallback={<Navigate to="/insights" replace />}>
              <TeamsPage />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/credentials"
          element={
            <RoleGuard roles={[Role.SuperAdmin]} fallback={<Navigate to="/insights" replace />}>
              <CredentialsPage />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/members"
          element={
            <RoleGuard roles={[Role.SuperAdmin, Role.TeamAdmin]} fallback={<Navigate to="/insights" replace />}>
              <MembersPage />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/audit-log"
          element={
            <RoleGuard roles={[Role.SuperAdmin, Role.Auditor]} fallback={<Navigate to="/insights" replace />}>
              <AuditLogPage />
            </RoleGuard>
          }
        />
      </Route>

      {/* Fallback */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/insights" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "") || undefined}>
      <Suspense fallback={<PageSkeleton />}>
        <AppRoutes />
      </Suspense>
    </BrowserRouter>
  );
}
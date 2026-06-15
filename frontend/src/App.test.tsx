import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeAll, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Suspense } from "react";

import { AppRoutes } from "./App";
import { AuthProvider } from "./auth/AuthProvider";
import { PageSkeleton } from "./components/feedback/PageSkeleton";

function renderRoutes(initialEntry: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <AuthProvider>
          <Suspense fallback={<PageSkeleton />}>
            <AppRoutes />
          </Suspense>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AppRoutes", () => {
  beforeAll(async () => {
    sessionStorage.clear();
    await Promise.all([
      import("@/pages/auth/LoginPage"),
      import("@/pages/insights/InsightsPage"),
      import("@/pages/admin/ToolsPage"),
    ]);
  });

  it("renders login placeholder at /login", async () => {
    renderRoutes("/login");
    expect(
      await screen.findByRole("heading", { name: "Sign in to your account" }),
    ).toBeInTheDocument();
  });

  it("redirects unauthenticated users from /dashboard to /login", async () => {
    renderRoutes("/dashboard");
    expect(
      await screen.findByRole("heading", { name: "Sign in to your account" }),
    ).toBeInTheDocument();
  });
});

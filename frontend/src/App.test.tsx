import { beforeAll, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Suspense } from "react";

import { AppRoutes } from "./App";
import { PageSkeleton } from "./components/feedback/PageSkeleton";

function renderRoutes(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Suspense fallback={<PageSkeleton />}>
        <AppRoutes />
      </Suspense>
    </MemoryRouter>,
  );
}

describe("AppRoutes", () => {
  beforeAll(async () => {
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

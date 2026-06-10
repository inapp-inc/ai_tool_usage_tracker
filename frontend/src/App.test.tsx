import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AppRoutes } from "./App";
import { AuthProvider } from "./auth/AuthContext";

describe("AppRoutes", () => {
  it("renders login placeholder at /login", () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <AppRoutes />
        </MemoryRouter>
      </AuthProvider>,
    );
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });

  it("redirects unauthenticated users from /dashboard to /login", () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/dashboard"]}>
          <AppRoutes />
        </MemoryRouter>
      </AuthProvider>,
    );
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });
});

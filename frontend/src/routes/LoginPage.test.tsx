import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { LoginPage } from "./LoginPage";

describe("LoginPage", () => {
  it("uses i18n keys for visible strings", () => {
    render(<LoginPage />);
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });
});

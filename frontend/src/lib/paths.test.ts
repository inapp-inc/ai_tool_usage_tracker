import { beforeEach, describe, expect, it, vi } from "vitest";

import { appPath, resolveApiBase } from "./paths";

describe("paths (development — base /)", () => {
  beforeEach(() => {
    vi.stubEnv("BASE_URL", "/");
    vi.stubEnv("VITE_API_BASE_URL", "");
  });

  it("appPath leaves routes at root", () => {
    expect(appPath("/login")).toBe("/login");
  });

  it("resolveApiBase uses /api/v1", () => {
    expect(resolveApiBase()).toBe("/api/v1");
  });
});

describe("paths (production — base /aitool/)", () => {
  beforeEach(() => {
    vi.stubEnv("BASE_URL", "/aitool/");
    vi.stubEnv("VITE_API_BASE_URL", "");
  });

  it("appPath prefixes routes with /aitool", () => {
    expect(appPath("/login")).toBe("/aitool/login");
  });

  it("resolveApiBase derives /aitool/api/v1 from base", () => {
    expect(resolveApiBase()).toBe("/aitool/api/v1");
  });
});

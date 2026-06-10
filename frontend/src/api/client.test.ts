import { describe, expect, it, vi } from "vitest";

import { apiFetch, setAccessToken } from "./client";

describe("apiFetch", () => {
  it("attaches Authorization and X-Correlation-ID headers", async () => {
    setAccessToken("test-jwt-token");
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}"));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/health");

    expect(fetchMock).toHaveBeenCalledOnce();
    const [, options] = fetchMock.mock.calls[0];
    const headers = options.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer test-jwt-token");
    expect(headers.get("X-Correlation-ID")).toBeTruthy();

    vi.unstubAllGlobals();
    setAccessToken(null);
  });
});

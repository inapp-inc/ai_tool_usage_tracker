import { describe, expect, it } from "vitest";

import { normalizeBasePath } from "./basePath";

describe("normalizeBasePath", () => {
  it("strips trailing slash and whitespace", () => {
    expect(normalizeBasePath("/aitool/")).toBe("/aitool");
    expect(normalizeBasePath(" /aitool/ \r\n")).toBe("/aitool");
  });

  it("returns undefined for empty values", () => {
    expect(normalizeBasePath(undefined)).toBeUndefined();
    expect(normalizeBasePath("")).toBeUndefined();
    expect(normalizeBasePath("   ")).toBeUndefined();
  });
});

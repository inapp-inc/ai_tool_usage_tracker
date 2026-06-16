/** Normalize VITE_BASE_PATH for React Router (no trailing slash, no CR/LF). */
export function normalizeBasePath(value: string | undefined): string | undefined {
  if (value == null) {
    return undefined;
  }
  const normalized = value.trim().replace(/\/+$/, "");
  return normalized || undefined;
}

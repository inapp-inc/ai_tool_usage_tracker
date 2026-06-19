/** Application base path without trailing slash (e.g. `/aitool` or ``). */
export function appBasePath(): string {
  return import.meta.env.BASE_URL.replace(/\/$/, "");
}

/** Prefix an in-app route for hard navigation (`window.location`, `<a href>`, etc.). */
export function appPath(route: string): string {
  const normalized = route.startsWith("/") ? route : `/${route}`;
  const base = appBasePath();
  return base ? `${base}${normalized}` : normalized;
}

/** Resolve a file under Vite `public/` (respects BASE_URL in production). */
export function publicAssetPath(filename: string): string {
  const base = import.meta.env.BASE_URL;
  const normalized = filename.startsWith("/") ? filename.slice(1) : filename;
  return `${base}${normalized}`;
}

/** Resolve API base URL from env or derive from Vite `base` (e.g. `/aitool/api/v1`). */
export function resolveApiBase(): string {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configured) {
    return configured;
  }

  const base = import.meta.env.BASE_URL;
  if (base && base !== "/") {
    return `${base.replace(/\/$/, "")}/api/v1`;
  }

  return "/api/v1";
}

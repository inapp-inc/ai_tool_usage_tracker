import type { ApiError, ApiResponse } from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

function createCorrelationId(): string {
  return crypto.randomUUID();
}

export class ApiClientError extends Error {
  readonly apiError: ApiError;

  constructor(apiError: ApiError) {
    super(apiError.detail);
    this.name = "ApiClientError";
    this.apiError = apiError;
  }
}

export async function parseApiError(response: Response): Promise<ApiError> {
  const contentType = response.headers.get("Content-Type") ?? "";
  if (contentType.includes("application/json")) {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "status" in body && "detail" in body) {
      const record = body as Record<string, unknown>;
      const apiError: ApiError = {
        type: String(record.type ?? "about:blank"),
        title: String(record.title ?? "Request failed"),
        status: Number(record.status ?? response.status),
        detail: String(record.detail ?? response.statusText),
      };
      if (Array.isArray(record.errors)) {
        return {
          ...apiError,
          errors: record.errors as Array<{ field: string; message: string }>,
        };
      }
      return apiError;
    }
  }

  return {
    type: "about:blank",
    title: response.statusText || "Request failed",
    status: response.status,
    detail: response.statusText || "An unexpected error occurred",
  };
}

function logRequestOutcome(method: string, url: string, status: number): void {
  console.warn(`${method} ${url} ${status}`);
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("X-Correlation-ID", createCorrelationId());
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (
    !headers.has("Content-Type") &&
    init.body &&
    !(init.body instanceof FormData)
  ) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  const method = (init.method ?? "GET").toUpperCase();
  logRequestOutcome(method, `${API_BASE}${path}`, response.status);

  return response;
}

interface ApiRequestInit extends RequestInit {
  skipAuthRetry?: boolean;
}

export async function apiRequest<T>(
  path: string,
  init: ApiRequestInit = {},
): Promise<T> {
  const { skipAuthRetry = false, ...fetchInit } = init;
  let response = await apiFetch(path, fetchInit);

  if (response.status === 401 && !skipAuthRetry) {
    try {
      const { refreshToken } = await import("./auth");
      await refreshToken();
      return apiRequest<T>(path, { ...init, skipAuthRetry: true });
    } catch {
      const { useAuthStore } = await import("@/stores/authStore");
      useAuthStore.getState().clearAuth();
      window.location.assign("/login");
      throw new ApiClientError({
        type: "about:blank",
        title: "Unauthorized",
        status: 401,
        detail: "Session expired",
      });
    }
  }

  if (!response.ok) {
    throw new ApiClientError(await parseApiError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const payload: unknown = await response.json();
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as ApiResponse<T>).data;
  }

  return payload as T;
}

export async function apiFormRequest<T>(
  path: string,
  formData: FormData,
  init: ApiRequestInit = {},
): Promise<T> {
  const { skipAuthRetry = false, ...fetchInit } = init;
  let response = await apiFetch(path, {
    ...fetchInit,
    method: fetchInit.method ?? "POST",
    body: formData,
  });

  if (response.status === 401 && !skipAuthRetry) {
    try {
      const { refreshToken } = await import("./auth");
      await refreshToken();
      return apiFormRequest<T>(path, formData, { ...init, skipAuthRetry: true });
    } catch {
      const { useAuthStore } = await import("@/stores/authStore");
      useAuthStore.getState().clearAuth();
      window.location.assign("/login");
      throw new ApiClientError({
        type: "about:blank",
        title: "Unauthorized",
        status: 401,
        detail: "Session expired",
      });
    }
  }

  if (!response.ok) {
    throw new ApiClientError(await parseApiError(response));
  }

  const payload: unknown = await response.json();
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as ApiResponse<T>).data;
  }

  return payload as T;
}

export { API_BASE };

export interface ListPageMeta {
  limit?: number;
  next_cursor?: string | null;
  has_more?: boolean;
}

export interface ApiListResponse<T> {
  data: T[];
  meta?: ListPageMeta;
}

function buildQuery(
  params?: Record<string, string | number | boolean | undefined | null>,
): string {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function apiListRequest<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>,
  init: ApiRequestInit = {},
): Promise<ApiListResponse<T>> {
  const { skipAuthRetry = false, ...fetchInit } = init;
  const url = `${path}${buildQuery(params)}`;
  let response = await apiFetch(url, fetchInit);

  if (response.status === 401 && !skipAuthRetry) {
    try {
      const { refreshToken } = await import("./auth");
      await refreshToken();
      return apiListRequest<T>(path, params, { ...init, skipAuthRetry: true });
    } catch {
      const { useAuthStore } = await import("@/stores/authStore");
      useAuthStore.getState().clearAuth();
      window.location.assign("/login");
      throw new ApiClientError({
        type: "about:blank",
        title: "Unauthorized",
        status: 401,
        detail: "Session expired",
      });
    }
  }

  if (!response.ok) {
    throw new ApiClientError(await parseApiError(response));
  }

  const payload = (await response.json()) as ApiListResponse<T>;
  return payload;
}

export async function fetchAllPages<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>,
  limit = 100,
): Promise<T[]> {
  const items: T[] = [];
  let cursor: string | undefined;

  for (;;) {
    const page = await apiListRequest<T>(path, {
      ...params,
      limit,
      cursor,
    });
    items.push(...page.data);
    const next = page.meta?.next_cursor;
    if (!page.meta?.has_more || !next) {
      break;
    }
    cursor = next;
  }

  return items;
}

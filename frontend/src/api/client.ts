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

async function parseApiError(response: Response): Promise<ApiError> {
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
  if (!headers.has("Content-Type") && init.body) {
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

export { API_BASE };

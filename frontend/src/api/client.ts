import type { ApiError, ApiResponse } from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

let accessToken: string | null = null;

const GENERIC_ERROR_TITLES = new Set([
  "Error",
  "Bad Request",
  "Invalid request",
  "Unauthorized",
  "Authentication required",
  "Forbidden",
  "Not Found",
  "Not found",
  "Conflict",
  "Validation Error",
  "Validation error",
  "Request failed",
  "Internal Server Error",
]);

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

function extractDetailFromBody(
  record: Record<string, unknown>,
  status: number,
): string {
  const detail = record.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return null;
      })
      .filter((value): value is string => Boolean(value));
    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  const title = record.title;
  if (typeof title === "string" && title.trim() && !GENERIC_ERROR_TITLES.has(title.trim())) {
    return title.trim();
  }

  if (typeof record.message === "string" && record.message.trim()) {
    return record.message.trim();
  }

  if (status === 400) {
    return "The request could not be completed. Check your API key and try again.";
  }

  return `Request failed (${status})`;
}

async function parseApiError(response: Response): Promise<ApiError> {
  const status = response.status;
  const contentType = response.headers.get("Content-Type") ?? "";
  let body: unknown = null;

  if (contentType.includes("json") || contentType.includes("problem")) {
    try {
      body = await response.json();
    } catch {
      body = null;
    }
  }

  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    const detail = extractDetailFromBody(record, status);
    const apiError: ApiError = {
      type: String(record.type ?? "about:blank"),
      title: String(record.title ?? "Request failed"),
      status: Number(record.status ?? status),
      detail,
    };
    if (Array.isArray(record.errors)) {
      return {
        ...apiError,
        errors: record.errors as Array<{ field: string; message: string }>,
      };
    }
    return apiError;
  }

  return {
    type: "about:blank",
    title: response.statusText || "Request failed",
    status,
    detail:
      status === 400
        ? "The request could not be completed. Check your API key and try again."
        : response.statusText || "An unexpected error occurred",
  };
}

function logRequestOutcome(method: string, url: string, status: number): void {
  console.warn(`${method} ${url} ${status}`);
}

async function resolveAccessToken(): Promise<string | null> {
  if (accessToken) {
    return accessToken;
  }

  const { useAuthStore } = await import("@/stores/authStore");
  const storeToken = useAuthStore.getState().accessToken;
  if (storeToken) {
    setAccessToken(storeToken);
    return storeToken;
  }

  return null;
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("X-Correlation-ID", createCorrelationId());

  const token = await resolveAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
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

async function clearSessionAndRedirect(): Promise<void> {
  const { clearPersistedRefreshToken } = await import("./auth");
  const { useAuthStore } = await import("@/stores/authStore");
  clearPersistedRefreshToken();
  useAuthStore.getState().clearAuth();
  window.location.assign("/login");
}

export async function apiRequest<T>(
  path: string,
  init: ApiRequestInit = {},
): Promise<T> {
  const { skipAuthRetry = false, ...fetchInit } = init;
  let response = await apiFetch(path, fetchInit);

  if (response.status === 401 && !skipAuthRetry) {
    const { refreshToken, getRefreshToken } = await import("./auth");
    const { useAuthStore } = await import("@/stores/authStore");

    if (!getRefreshToken() && !useAuthStore.getState().accessToken) {
      await clearSessionAndRedirect();
      throw new ApiClientError({
        type: "about:blank",
        title: "Unauthorized",
        status: 401,
        detail: "Session expired. Please sign in again.",
      });
    }

    try {
      await refreshToken();
      return apiRequest<T>(path, { ...init, skipAuthRetry: true });
    } catch {
      if (useAuthStore.getState().isAuthenticated) {
        throw new ApiClientError({
          type: "about:blank",
          title: "Unauthorized",
          status: 401,
          detail: "Your session could not be renewed. Please sign in again.",
        });
      }

      await clearSessionAndRedirect();
      throw new ApiClientError({
        type: "about:blank",
        title: "Unauthorized",
        status: 401,
        detail: "Session expired. Please sign in again.",
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

export { API_BASE, parseApiError };

import { apiFetch, setAccessToken } from "./client";
import type { User } from "@/types";
import { Role } from "@/types";
import { useAuthStore } from "@/stores/authStore";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

interface UserProfileResponse {
  id: string;
  email: string;
  display_name?: string;
  role: string;
  role_id?: string | null;
  role_name?: string | null;
  organization_id: string;
  team_ids?: string[];
}

const REFRESH_TOKEN_STORAGE_KEY = "ai_tool_tracker_refresh_token";

let inMemoryRefreshToken: string | null = null;

function loadPersistedRefreshToken(): string | null {
  try {
    return sessionStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

function persistRefreshToken(token: string | null): void {
  try {
    if (token) {
      sessionStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, token);
    } else {
      sessionStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
    }
  } catch {
    // Ignore storage failures (private browsing, etc.)
  }
}

export function setRefreshToken(token: string | null): void {
  inMemoryRefreshToken = token;
  persistRefreshToken(token);
}

export function getRefreshToken(): string | null {
  if (inMemoryRefreshToken) {
    return inMemoryRefreshToken;
  }
  const stored = loadPersistedRefreshToken();
  if (stored) {
    inMemoryRefreshToken = stored;
  }
  return inMemoryRefreshToken;
}

export function clearPersistedRefreshToken(): void {
  inMemoryRefreshToken = null;
  persistRefreshToken(null);
}

function mapUserProfile(profile: UserProfileResponse): User {
  const platformRole = Object.values(Role).includes(profile.role as Role)
    ? (profile.role as Role)
    : Role.TeamMember;

  return {
    id: profile.id,
    email: profile.email,
    name: profile.display_name ?? profile.email,
    platformRole,
    roleId: profile.role_id ?? null,
    roleName: profile.role_name ?? profile.role,
    teamMemberships: (profile.team_ids ?? []).map((teamId) => ({
      teamId,
      teamName: teamId,
      role: platformRole,
    })),
  };
}

async function parseApiError(response: Response): Promise<string> {
  const contentType = response.headers.get("Content-Type") ?? "";
  if (contentType.includes("json") || contentType.includes("problem")) {
    try {
      const body: unknown = await response.json();
      if (body && typeof body === "object") {
        const record = body as Record<string, unknown>;
        if (typeof record.detail === "string" && record.detail.trim()) {
          return record.detail.trim();
        }
        if (typeof record.title === "string" && record.title.trim()) {
          return record.title.trim();
        }
      }
    } catch {
      // fall through
    }
  }
  return response.statusText || "Request failed";
}

export async function login(body: LoginRequest): Promise<LoginResponse> {
  const response = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }

  const tokens = (await response.json()) as TokenResponse;
  setAccessToken(tokens.access_token);
  if (tokens.refresh_token) {
    setRefreshToken(tokens.refresh_token);
  }

  const user = await fetchCurrentUser();
  if (user.roleId) {
    await useAuthStore.getState().loadPermissions(user.roleId);
  }
  return { user, accessToken: tokens.access_token };
}

export async function refreshToken(): Promise<TokenResponse> {
  const refresh = getRefreshToken();
  if (!refresh) {
    throw new Error("No refresh token available");
  }

  const response = await apiFetch("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refresh }),
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error("Refresh failed");
  }

  const tokens = (await response.json()) as TokenResponse;
  setAccessToken(tokens.access_token);
  if (tokens.refresh_token) {
    setRefreshToken(tokens.refresh_token);
  }

  return tokens;
}

export async function fetchCurrentUser(): Promise<User> {
  const response = await apiFetch("/auth/me");
  if (!response.ok) {
    throw new Error("Failed to fetch current user");
  }

  const profile = (await response.json()) as UserProfileResponse;
  return mapUserProfile(profile);
}

export async function restoreAuthSession(): Promise<{
  user: User;
  accessToken: string;
} | null> {
  if (!getRefreshToken()) {
    return null;
  }

  const tokens = await refreshToken();
  const user = await fetchCurrentUser();
  if (user.roleId) {
    await useAuthStore.getState().loadPermissions(user.roleId);
  }
  return { user, accessToken: tokens.access_token };
}

export const authApi = {
  login,
  fetchCurrentUser,
  refreshToken,
  restoreAuthSession,
};

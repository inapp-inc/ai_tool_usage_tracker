import { apiFetch, setAccessToken } from "./client";
import type { User } from "@/types";
import { Role } from "@/types";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
}

const MOCK_LOGIN_LATENCY_MS = 600;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function deriveNameFromEmail(email: string): string {
  const localPart = email.split("@")[0] ?? email;
  if (!localPart) {
    return email;
  }
  return localPart.charAt(0).toUpperCase() + localPart.slice(1);
}

export async function login(body: LoginRequest): Promise<LoginResponse> {
  await delay(MOCK_LOGIN_LATENCY_MS);

  if (body.password.length < 1 || body.email.trim().length < 1) {
    throw new Error("Invalid credentials");
  }

  return {
    user: {
      id: "u_1",
      name: deriveNameFromEmail(body.email),
      email: body.email,
      platformRole: Role.SuperAdmin,
      teamMemberships: [],
    },
    accessToken: `mock_token_${Date.now()}`,
  };
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
  organization_id: string;
  team_ids?: string[];
}

let inMemoryRefreshToken: string | null = null;

export function setRefreshToken(token: string | null): void {
  inMemoryRefreshToken = token;
}

export function getRefreshToken(): string | null {
  return inMemoryRefreshToken;
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
    teamMemberships: (profile.team_ids ?? []).map((teamId) => ({
      teamId,
      teamName: teamId,
      role: platformRole,
    })),
  };
}

export async function refreshToken(): Promise<TokenResponse> {
  if (!inMemoryRefreshToken) {
    throw new Error("No refresh token available");
  }

  const response = await apiFetch("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: inMemoryRefreshToken }),
  });

  if (!response.ok) {
    throw new Error("Refresh failed");
  }

  const tokens = (await response.json()) as TokenResponse;
  setAccessToken(tokens.access_token);
  if (tokens.refresh_token) {
    inMemoryRefreshToken = tokens.refresh_token;
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
  if (!inMemoryRefreshToken) {
    return null;
  }

  const tokens = await refreshToken();
  const user = await fetchCurrentUser();
  return { user, accessToken: tokens.access_token };
}

export const authApi = {
  login,
  fetchCurrentUser,
  refreshToken,
  restoreAuthSession,
};

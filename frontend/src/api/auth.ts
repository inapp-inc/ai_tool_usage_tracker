import { apiFetch, parseApiError, setAccessToken, ApiClientError } from "./client";
import { persistAccessToken } from "@/auth/sessionStorage";

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

const REFRESH_TOKEN_KEY = "refresh_token";

export function setRefreshToken(token: string | null): void {
  inMemoryRefreshToken = token;
  if (token) {
    sessionStorage.setItem(REFRESH_TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

export function getRefreshToken(): string | null {
  if (inMemoryRefreshToken) {
    return inMemoryRefreshToken;
  }
  inMemoryRefreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY);
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



export async function login(body: LoginRequest): Promise<LoginResponse> {

  const response = await apiFetch("/auth/login", {

    method: "POST",

    body: JSON.stringify({ email: body.email, password: body.password }),

  });



  if (!response.ok) {

    throw new ApiClientError(await parseApiError(response));

  }



  const tokens = (await response.json()) as TokenResponse;

  setAccessToken(tokens.access_token);
  persistAccessToken(tokens.access_token);
  if (tokens.refresh_token) {
    setRefreshToken(tokens.refresh_token);
  }



  const user = await fetchCurrentUser();

  return { user, accessToken: tokens.access_token };

}



export async function refreshToken(): Promise<TokenResponse> {
  const storedRefresh = getRefreshToken();
  if (!storedRefresh) {
    throw new Error("No refresh token available");
  }

  const response = await apiFetch("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: storedRefresh }),
  });

  if (!response.ok) {
    throw new Error("Refresh failed");
  }

  const tokens = (await response.json()) as TokenResponse;
  setAccessToken(tokens.access_token);
  persistAccessToken(tokens.access_token);
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
  return { user, accessToken: tokens.access_token };
}



export const authApi = {

  login,

  fetchCurrentUser,

  refreshToken,

  restoreAuthSession,

};



import { apiRequest } from "./client";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  createdAt: string;
}

export interface CreateOrganizationRequest {
  name: string;
  initialMember?: {
    email: string;
    password: string;
    displayName?: string;
    roleName?: string;
  };
}

export interface CreateOrganizationResult {
  organization: Organization;
  initialUserId: string | null;
  initialUserEmail: string | null;
}

interface ApiOrganization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

interface ApiCreateOrganizationResponse {
  organization: ApiOrganization;
  initial_user_id: string | null;
  initial_user_email: string | null;
}

function mapOrganization(row: ApiOrganization): Organization {
  return {
    id: row.id,
    name: row.name,
    slug: row.slug,
    createdAt: row.created_at,
  };
}

export async function fetchOrganizations(): Promise<Organization[]> {
  const rows = await apiRequest<ApiOrganization[]>("/organizations");
  return rows
    .map(mapOrganization)
    .filter((org) => org.slug !== "platform" && org.slug !== "default");
}

export async function createOrganization(
  body: CreateOrganizationRequest,
): Promise<CreateOrganizationResult> {
  const payload: Record<string, unknown> = {
    name: body.name,
  };
  if (body.initialMember) {
    payload.initial_member = {
      email: body.initialMember.email,
      password: body.initialMember.password,
      display_name: body.initialMember.displayName,
      role_name: body.initialMember.roleName ?? "team_member",
    };
  }
  const response = await apiRequest<ApiCreateOrganizationResponse>("/organizations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return {
    organization: mapOrganization(response.organization),
    initialUserId: response.initial_user_id,
    initialUserEmail: response.initial_user_email,
  };
}

export const organizationsApi = {
  fetchOrganizations,
  createOrganization,
};

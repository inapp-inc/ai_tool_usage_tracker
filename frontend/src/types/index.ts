// Roles
export enum Role {
  SuperAdmin = "super_admin",
  TeamAdmin = "team_admin",
  FinanceViewer = "finance_viewer",
  TeamMember = "team_member",
  Auditor = "auditor",
}

// Auth
export interface User {
  id: string;
  email: string;
  name: string;
  platformRole: Role;
  roleId?: string | null;
  roleName?: string | null;
  teamMemberships: TeamMembership[];
}

export interface PermissionEntry {
  can_read: boolean;
  can_write: boolean;
  team_scoped: boolean;
}

export interface TeamMembership {
  teamId: string;
  teamName: string;
  role: Role;
}

// Pagination
export interface CursorPage<T> {
  data: T[];
  nextCursor: string | null;
  total: number;
}

// API envelope
export interface ApiResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
}

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  errors?: Array<{ field: string; message: string }>;
}

// Date periods
export type Period =
  | "today"
  | "7d"
  | "30d"
  | "this_month"
  | "last_month"
  | "custom";

export interface DateRange {
  from: string;
  to: string;
}

// Tools
export type PricingModel = "per_token" | "per_seat" | "flat_fee" | "hybrid";

// Alerts
export type AlertSeverity = "warning" | "critical";
export type ThresholdType =
  | "absolute_tokens"
  | "percentage_allowance"
  | "cost_amount";
export type ThresholdScope = "tool" | "team" | "user";

// Upload
export type UploadStatus = "pending" | "processing" | "completed" | "failed";
export type UploadRecordStatus = "matched" | "flagged" | "unmatched";

import { apiRequest } from "./client";

export interface InAppNotification {
  id: string;
  notification_type: string;
  severity: string | null;
  title: string;
  body: string | null;
  payload: Record<string, unknown>;
  read: boolean;
  read_at: string | null;
  created_at: string;
}

export async function fetchUnreadCount(): Promise<number> {
  const result = await apiRequest<{ unread_count: number }>(
    "/notifications/unread-count",
  );
  return result.unread_count;
}

export async function fetchNotifications(options?: {
  unreadOnly?: boolean;
  limit?: number;
}): Promise<InAppNotification[]> {
  const params = new URLSearchParams();
  if (options?.unreadOnly) {
    params.set("unread_only", "true");
  }
  if (options?.limit !== undefined) {
    params.set("limit", String(options.limit));
  }
  const query = params.toString();
  return apiRequest<InAppNotification[]>(
    `/notifications${query ? `?${query}` : ""}`,
  );
}

export async function markNotificationRead(id: string): Promise<InAppNotification> {
  return apiRequest<InAppNotification>(`/notifications/${id}/read`, {
    method: "POST",
  });
}

export async function markAllNotificationsRead(): Promise<number> {
  const result = await apiRequest<{ marked_read: number }>(
    "/notifications/read-all",
    { method: "POST" },
  );
  return result.marked_read;
}

export const notificationsApi = {
  fetchUnreadCount,
  fetchNotifications,
  markNotificationRead,
  markAllNotificationsRead,
};

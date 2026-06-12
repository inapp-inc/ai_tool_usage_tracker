import { useEffect } from "react";

import { useNotificationStore } from "@/stores/notificationStore";
import { API_BASE } from "@/api/client";

export function useNotifications(enabled = true) {
  const addNotification = useNotificationStore((state) => state.addNotification);
  const setUnreadCount = useNotificationStore((state) => state.setUnreadCount);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const source = new EventSource(`${API_BASE}/notifications/stream`);

    source.onmessage = (event) => {
      try {
        const payload: unknown = JSON.parse(event.data);
        if (
          payload &&
          typeof payload === "object" &&
          "id" in payload &&
          "title" in payload &&
          "message" in payload
        ) {
          const record = payload as {
            id: string;
            title: string;
            message: string;
            createdAt?: string;
          };
          addNotification({
            id: record.id,
            title: record.title,
            message: record.message,
            read: false,
            createdAt: record.createdAt ?? new Date().toISOString(),
          });
        }
      } catch {
        // Ignore malformed SSE payloads
      }
    };

    source.addEventListener("unread_count", (event) => {
      const count = Number(event.data);
      if (!Number.isNaN(count)) {
        setUnreadCount(count);
      }
    });

    return () => {
      source.close();
    };
  }, [addNotification, enabled, setUnreadCount]);
}

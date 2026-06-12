import { create } from "zustand";

export interface Notification {
  id: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
}

interface NotificationState {
  unreadCount: number;
  notifications: Notification[];
  setUnreadCount: (n: number) => void;
  addNotification: (n: Notification) => void;
  markAllRead: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  unreadCount: 0,
  notifications: [],
  setUnreadCount: (n) => set({ unreadCount: n }),
  addNotification: (n) =>
    set((state) => ({
      notifications: [n, ...state.notifications],
      unreadCount: state.unreadCount + (n.read ? 0 : 1),
    })),
  markAllRead: () =>
    set((state) => ({
      unreadCount: 0,
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
    })),
}));

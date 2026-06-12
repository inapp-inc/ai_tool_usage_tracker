import { create } from "zustand";

import { setAccessToken } from "@/api/client";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  setAuth: (user, token) => {
    setAccessToken(token);
    set({ user, accessToken: token, isAuthenticated: true });
  },
  clearAuth: () => {
    setAccessToken(null);
    set({ user: null, accessToken: null, isAuthenticated: false });
  },
}));

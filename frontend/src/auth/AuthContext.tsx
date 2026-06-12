import { useAuthStore } from "@/stores/authStore";

export function useAuth(): { isAuthenticated: boolean } {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return { isAuthenticated };
}

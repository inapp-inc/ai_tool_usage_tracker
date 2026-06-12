import { useCallback } from "react";

export interface ToastMessage {
  id: string;
  message: string;
  severity: "success" | "error" | "info" | "warning";
}

type ToastListener = (toast: ToastMessage) => void;

const listeners = new Set<ToastListener>();

export function useToast() {
  const showToast = useCallback(
    (message: string, severity: ToastMessage["severity"] = "info") => {
      const toast: ToastMessage = {
        id: crypto.randomUUID(),
        message,
        severity,
      };
      listeners.forEach((listener) => listener(toast));
    },
    [],
  );

  return { showToast };
}

export function subscribeToToasts(listener: ToastListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

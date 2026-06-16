import { Alert, Snackbar } from "@mui/material";
import { useEffect, useState } from "react";

import {
  subscribeToToasts,
  type ToastMessage,
} from "@/hooks/useToast";

export function ToastHost() {
  const [toast, setToast] = useState<ToastMessage | null>(null);

  useEffect(() => {
    return subscribeToToasts((message) => {
      setToast(message);
    });
  }, []);

  return (
    <Snackbar
      open={toast !== null}
      autoHideDuration={5000}
      onClose={() => setToast(null)}
      anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
    >
      {toast ? (
        <Alert
          onClose={() => setToast(null)}
          severity={toast.severity}
          variant="filled"
          sx={{ width: "100%" }}
        >
          {toast.message}
        </Alert>
      ) : undefined}
    </Snackbar>
  );
}

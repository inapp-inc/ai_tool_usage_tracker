import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "@/App";
import { AuthBootstrap } from "@/auth/AuthBootstrap";
import { queryClient } from "@/lib/queryClient";
import { theme } from "@/theme";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthBootstrap>
          <App />
        </AuthBootstrap>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);

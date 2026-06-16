import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "@/App";
import { AuthBootstrap } from "@/auth/AuthBootstrap";
import { theme } from "@/theme";

const queryClient = new QueryClient();

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

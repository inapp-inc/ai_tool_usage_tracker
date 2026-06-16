import { Box } from "@mui/material";
import { Outlet } from "react-router-dom";

import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { ToastHost } from "@/components/feedback/ToastHost";

const SIDEBAR_WIDTH = 240;
const SIDEBAR_COLLAPSED_WIDTH = 64;
const TOPBAR_HEIGHT = 52;

export function AppShell() {
  return (
    <Box sx={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      <Sidebar
        width={SIDEBAR_WIDTH}
        collapsedWidth={SIDEBAR_COLLAPSED_WIDTH}
      />

      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          minWidth: 0,
        }}
      >
        <TopBar height={TOPBAR_HEIGHT} />

        <Box
          component="main"
          sx={{
            flex: 1,
            overflow: "auto",
            backgroundColor: "background.default",
            p: "16px 20px",
          }}
        >
          <Outlet />
        </Box>
      </Box>
      <ToastHost />
    </Box>
  );
}
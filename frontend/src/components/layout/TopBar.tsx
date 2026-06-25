import { IconChevronDown, IconLogout } from "@tabler/icons-react";
import {
  AppBar,
  Box,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useLocation } from "react-router-dom";

import { NotificationBell } from "./NotificationBell";
import { useAuthStore } from "@/stores/authStore";
import { tokens } from "@/theme/palette";

const ROUTE_TITLES: Record<string, string> = {
  "/insights": "Insights",
  "/alerts": "Alerts",
  "/uploads": "Uploads",
  "/admin/tools": "Tools",
  "/admin/teams": "Teams",
  "/admin/members": "Members",
  "/admin/credentials": "Credentials",
  "/admin/audit-log": "Audit log",
  "/admin/settings": "Settings",
  "/login": "",
};

function resolveTitle(pathname: string): string {
  // Exact match first
  if (ROUTE_TITLES[pathname]) return ROUTE_TITLES[pathname];
  // Prefix match for dynamic segments (e.g. /usage/teams/abc)
  const prefix = Object.keys(ROUTE_TITLES).find((key) =>
    pathname.startsWith(`${key}/`),
  );
  return prefix ? ROUTE_TITLES[prefix] : "";
}

interface TopBarProps {
  height: number;
}

export function TopBar({ height }: TopBarProps) {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const title = resolveTitle(location.pathname);

  const handleUserMenuOpen = (e: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(e.currentTarget);
  };
  const handleUserMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    handleUserMenuClose();
    clearAuth();
  };

  const initials = user?.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() ?? "";

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        backgroundColor: tokens.bgPaper,
        borderBottom: `0.5px solid ${tokens.border}`,
        height,
        justifyContent: "center",
        zIndex: 1,
      }}
    >
      <Toolbar
        sx={{
          minHeight: `${height}px !important`,
          px: "20px !important",
          gap: 1.5,
        }}
      >
        {/* Page title */}
        <Typography
          sx={{
            fontSize: "0.9375rem",
            fontWeight: 500,
            color: "text.primary",
            flex: 1,
          }}
        >
          {title}
        </Typography>

        {/* Period selector slot — injected by pages that need it */}
        <Box id="topbar-period-slot" />

        {/* Notification bell */}
        <NotificationBell />

        {/* User avatar + dropdown */}
        <Box
          onClick={handleUserMenuOpen}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 0.75,
            cursor: "pointer",
            borderRadius: "6px",
            px: 0.5,
            py: 0.25,
            "&:hover": { backgroundColor: "background.default" },
          }}
          aria-label="User menu"
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && handleUserMenuOpen(e as unknown as React.MouseEvent<HTMLElement>)}
        >
          <Box
            sx={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              backgroundColor: "#1E3A5F",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.6875rem",
              fontWeight: 500,
              color: "#60A5FA",
              flexShrink: 0,
            }}
          >
            {initials}
          </Box>
          <IconChevronDown size={13} style={{ color: tokens.textMuted }} />
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleUserMenuClose}
          transformOrigin={{ horizontal: "right", vertical: "top" }}
          anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
          slotProps={{
            paper: {
              sx: {
                mt: 0.5,
                minWidth: 180,
                border: `0.5px solid ${tokens.border}`,
                boxShadow: "0 4px 16px rgba(15,23,42,0.1)",
              },
            },
          }}
        >
          {user && (
            <Box sx={{ px: 2, py: 1, borderBottom: `0.5px solid ${tokens.border}` }}>
              <Typography sx={{ fontSize: "0.8125rem", fontWeight: 500 }}>
                {user.name}
              </Typography>
              <Typography sx={{ fontSize: "0.75rem", color: "text.secondary" }}>
                {user.email}
              </Typography>
            </Box>
          )}
          <MenuItem
            onClick={handleLogout}
            sx={{ fontSize: "0.8125rem", gap: 1, color: "error.main", mt: 0.5 }}
          >
            <IconLogout size={15} />
            Sign out
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
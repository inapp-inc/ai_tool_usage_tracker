import {
  IconBellRinging,
  IconChartBar,
  IconChevronLeft,
  IconChevronRight,
  IconCloudUpload,
  IconKey,
  IconRobot,
  IconSettings,
  IconShieldCheck,
  IconUser,
  IconUserPlus,
  IconUsersGroup,
} from "@tabler/icons-react";
import { Box, Tooltip, Typography } from "@mui/material";
import { useCallback, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { publicAssetPath } from "@/lib/paths";
import { useAuthStore } from "@/stores/authStore";
import { Role } from "@/types";
import { tokens } from "@/theme/palette";

interface NavItem {
  label: string;
  icon: React.ElementType;
  path: string;
  /** @deprecated use resource */
  roles?: Role[] | "all";
  resource?: string;
  accent: string;
}

interface NavSection {
  heading?: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    items: [
      {
        label: "Insights",
        icon: IconChartBar,
        path: "/insights",
        roles: "all",
        resource: "insights",
        accent: "#3B82F6",
      },
    ],
  },
  {
    heading: "My Data",
    items: [
      {
        label: "My Usage",
        icon: IconUser,
        path: "/my-usage",
        resource: "my_usage",
        accent: "#10B981",
      },
    ],
  },
  {
    heading: "Manage",
    items: [
      {
        label: "Alerts",
        icon: IconBellRinging,
        path: "/alerts",
        resource: "alerts",
        accent: "#F59E0B",
      },
      {
        label: "Uploads",
        icon: IconCloudUpload,
        path: "/uploads",
        resource: "uploads",
        accent: "#8B5CF6",
      },
    ],
  },
  {
    heading: "Admin",
    items: [
      {
        label: "Tools",
        icon: IconRobot,
        path: "/admin/tools",
        resource: "tools",
        accent: "#06B6D4",
      },
      {
        label: "Teams",
        icon: IconUsersGroup,
        path: "/admin/teams",
        resource: "teams",
        accent: "#EC4899",
      },
      {
        label: "Members",
        icon: IconUserPlus,
        path: "/admin/members",
        resource: "members",
        accent: "#6366F1",
      },
      {
        label: "Credentials",
        icon: IconKey,
        path: "/admin/credentials",
        resource: "credentials",
        accent: "#14B8A6",
      },
      {
        label: "Audit log",
        icon: IconShieldCheck,
        path: "/admin/audit-log",
        resource: "audit_logs",
        accent: "#EF4444",
      },
      {
        label: "Settings",
        icon: IconSettings,
        path: "/admin/settings",
        resource: "settings",
        accent: "#94A3B8",
      },
    ],
  },
];

const COLLAPSE_KEY = "sidebar_collapsed";
const INAPP_LOGO_SRC = publicAssetPath("inapp-logo.png");

interface SidebarProps {
  width: number;
  collapsedWidth: number;
}

export function Sidebar({ width, collapsedWidth }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem(COLLAPSE_KEY) === "true",
  );

  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const canRead = useAuthStore((s) => s.canRead);

  const toggleCollapse = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(COLLAPSE_KEY, String(next));
      return next;
    });
  }, []);

  const canSeeItem = useCallback(
    (item: NavItem): boolean => {
      if (item.resource) {
        if (item.resource === "insights" && item.roles === "all") {
          return true;
        }
        return canRead(item.resource);
      }
      if (item.roles === "all") return true;
      if (!user) return false;
      return (item.roles as Role[]).includes(user.platformRole);
    },
    [user, canRead],
  );

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(`${path}/`);

  const currentWidth = collapsed ? collapsedWidth : width;

  return (
    <Box
      component="nav"
      aria-label="Main navigation"
      sx={{
        width: currentWidth,
        minWidth: currentWidth,
        height: "100vh",
        background: `linear-gradient(180deg, ${tokens.sidebar} 0%, ${tokens.sidebarDark} 100%)`,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        transition: "width 0.2s ease, min-width 0.2s ease",
        position: "relative",
        flexShrink: 0,
        borderRight: "1px solid rgba(255,255,255,0.12)",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 1,
          py: 2,
          px: 1.5,
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          flexShrink: 0,
        }}
      >
        {collapsed ? (
          <Tooltip title="AI Usage Tracker · Built by The Foundry" placement="right">
            <Box
              component="img"
              src={INAPP_LOGO_SRC}
              alt="InApp"
              sx={{
                height: 28,
                width: "auto",
                maxWidth: "100%",
                flexShrink: 0,
                objectFit: "contain",
              }}
            />
          </Tooltip>
        ) : (
          <>
            <Box
              component="img"
              src={INAPP_LOGO_SRC}
              alt="InApp"
              sx={{
                height: 36,
                width: "auto",
                maxWidth: "100%",
                flexShrink: 0,
                objectFit: "contain",
              }}
            />
            <Box sx={{ width: "100%", textAlign: "center", px: 0.5 }}>
              <Typography
                sx={{
                  fontSize: "0.8125rem",
                  fontWeight: 700,
                  lineHeight: 1.25,
                  color: "#FFFFFF",
                  letterSpacing: "-0.2px",
                }}
              >
                AI Usage Tracker
              </Typography>
              <Typography
                sx={{
                  mt: 0.5,
                  fontSize: "0.5625rem",
                  fontWeight: 700,
                  lineHeight: 1.3,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "rgba(255,255,255,0.75)",
                }}
              >
                Built by The Foundry
              </Typography>
            </Box>
          </>
        )}
      </Box>

      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          py: 1.25,
          scrollbarWidth: "thin",
          scrollbarColor: "rgba(255,255,255,0.12) transparent",
          "&::-webkit-scrollbar": { width: "4px" },
          "&::-webkit-scrollbar-track": { background: "transparent" },
          "&::-webkit-scrollbar-thumb": {
            background: "rgba(255,255,255,0.12)",
            borderRadius: "4px",
          },
        }}
      >
        {NAV_SECTIONS.map((section, si) => {
          const visibleItems = section.items.filter(canSeeItem);
          if (visibleItems.length === 0) return null;

          return (
            <Box key={si}>
              {section.heading && !collapsed && (
                <Typography
                  sx={{
                    px: 2,
                    pt: 1.5,
                    pb: 0.75,
                    fontSize: "0.625rem",
                    fontWeight: 700,
                    color: "rgba(255,255,255,0.85)",
                    textTransform: "uppercase",
                    letterSpacing: "0.1em",
                  }}
                >
                  {section.heading}
                </Typography>
              )}
              {section.heading && collapsed && (
                <Box
                  sx={{
                    mx: 1.25,
                    my: 0.75,
                    borderTop: "1px solid rgba(255,255,255,0.08)",
                  }}
                />
              )}
              {visibleItems.map((item) => {
                const active = isActive(item.path);
                const Icon = item.icon;

                const navButton = (
                  <Box
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    sx={{
                      position: "relative",
                      display: "flex",
                      alignItems: "center",
                      gap: 1.25,
                      px: collapsed ? 0 : "10px",
                      py: "9px",
                      mx: 1,
                      my: "2px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      justifyContent: collapsed ? "center" : "flex-start",
                      backgroundColor: active
                        ? "rgba(255,255,255,0.1)"
                        : "transparent",
                      color: "#FFFFFF",
                      boxShadow: active
                        ? `inset 3px 0 0 ${tokens.sidebarAccent}`
                        : "none",
                      "&:hover": {
                        backgroundColor: active
                          ? "rgba(255,255,255,0.12)"
                          : "rgba(255,255,255,0.06)",
                        color: "#FFFFFF",
                      },
                      transition: "background-color 0.15s, color 0.15s, box-shadow 0.15s",
                    }}
                  >
                    <Box
                      sx={{
                        width: 28,
                        height: 28,
                        borderRadius: "7px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                        backgroundColor: active
                          ? "rgba(255,255,255,0.14)"
                          : "rgba(255,255,255,0.08)",
                        color: "#FFFFFF",
                        boxShadow: active ? "0 0 0 1px rgba(255,255,255,0.2)" : "none",
                      }}
                    >
                      <Icon size={16} stroke={active ? 2.25 : 1.75} />
                    </Box>
                    {!collapsed && (
                      <Typography
                        sx={{
                          fontSize: "0.8125rem",
                          fontWeight: 700,
                          whiteSpace: "nowrap",
                          color: "#FFFFFF",
                        }}
                      >
                        {item.label}
                      </Typography>
                    )}
                  </Box>
                );

                return collapsed ? (
                  <Tooltip key={item.path} title={item.label} placement="right">
                    {navButton}
                  </Tooltip>
                ) : (
                  navButton
                );
              })}
            </Box>
          );
        })}
      </Box>

      <Box
        sx={{
          borderTop: "1px solid rgba(255,255,255,0.08)",
          p: 1.5,
          flexShrink: 0,
        }}
      >
        {user && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              p: "8px",
              borderRadius: "8px",
              overflow: "hidden",
              backgroundColor: "rgba(255,255,255,0.06)",
            }}
          >
            <Box
              sx={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #1E40AF 0%, #172554 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.6875rem",
                fontWeight: 700,
                color: "#FFFFFF",
                flexShrink: 0,
              }}
            >
              {user.name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .slice(0, 2)
                .toUpperCase()}
            </Box>
            {!collapsed && (
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  sx={{
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    color: "#FFFFFF",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {user.name}
                </Typography>
                <Typography
                  sx={{
                    fontSize: "0.625rem",
                    fontWeight: 700,
                    color: "rgba(255,255,255,0.8)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {user.platformRole.replace("_", " ")}
                </Typography>
              </Box>
            )}
          </Box>
        )}

        <Box
          onClick={toggleCollapse}
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "flex-end",
            mt: 1,
            px: 1,
            py: 0.75,
            borderRadius: "6px",
            cursor: "pointer",
            color: "rgba(255,255,255,0.85)",
            "&:hover": { color: "#FFFFFF", backgroundColor: "rgba(255,255,255,0.12)" },
            transition: "color 0.15s, background-color 0.15s",
          }}
        >
          {collapsed ? <IconChevronRight size={16} /> : <IconChevronLeft size={16} />}
        </Box>
      </Box>
    </Box>
  );
}

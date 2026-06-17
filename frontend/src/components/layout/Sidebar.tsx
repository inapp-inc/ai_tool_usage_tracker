import {
    IconActivity,
    IconBell,
    IconChevronLeft,
    IconChevronRight,
    IconKey,
    IconLayoutDashboard,
    IconSettings,
    IconShield,
    IconTool,
    IconUpload,
    IconUser,
    IconUsers,
  } from "@tabler/icons-react";
  import { Box, Tooltip, Typography } from "@mui/material";
  import { useCallback, useState } from "react";
  import { useLocation, useNavigate } from "react-router-dom";
  
  import { useAuthStore } from "@/stores/authStore";
  import { Role } from "@/types";
  import { tokens } from "@/theme/palette";
  
  interface NavItem {
    label: string;
    icon: React.ElementType;
    path: string;
    roles: Role[] | "all";
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
          icon: IconLayoutDashboard,
          path: "/insights",
          roles: "all",
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
          roles: [Role.TeamMember],
        },
      ],
    },
    {
      heading: "Manage",
      items: [
        {
          label: "Alerts",
          icon: IconBell,
          path: "/alerts",
          roles: [Role.SuperAdmin, Role.TeamAdmin],
        },
        {
          label: "Uploads",
          icon: IconUpload,
          path: "/uploads",
          roles: [Role.SuperAdmin, Role.TeamAdmin],
        },
      ],
    },
    {
      heading: "Admin",
      items: [
        {
          label: "Tools",
          icon: IconTool,
          path: "/admin/tools",
          roles: [Role.SuperAdmin],
        },
        {
          label: "Teams",
          icon: IconUsers,
          path: "/admin/teams",
          roles: [Role.SuperAdmin],
        },
        {
          label: "Members",
          icon: IconUsers,
          path: "/admin/members",
          roles: [Role.SuperAdmin],
        },
        {
          label: "Credentials",
          icon: IconKey,
          path: "/admin/credentials",
          roles: [Role.SuperAdmin],
        },
        {
          label: "Audit log",
          icon: IconShield,
          path: "/admin/audit-log",
          roles: [Role.SuperAdmin, Role.Auditor],
        },
        {
          label: "Settings",
          icon: IconSettings,
          path: "/admin/settings",
          roles: [Role.SuperAdmin],
        },
      ],
    },
  ];
  
  const COLLAPSE_KEY = "sidebar_collapsed";
  
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
  
    const toggleCollapse = useCallback(() => {
      setCollapsed((prev) => {
        const next = !prev;
        localStorage.setItem(COLLAPSE_KEY, String(next));
        return next;
      });
    }, []);
  
    const canSeeItem = useCallback(
      (item: NavItem): boolean => {
        if (item.roles === "all") return true;
        if (!user) return false;
        return (item.roles as Role[]).includes(user.platformRole);
      },
      [user],
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
          backgroundColor: tokens.sidebar,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          transition: "width 0.2s ease, min-width 0.2s ease",
          position: "relative",
          flexShrink: 0,
        }}
      >
        {/* Logo */}
        <Box
          sx={{
            px: 2,
            py: "20px",
            borderBottom: "0.5px solid rgba(255,255,255,0.07)",
            display: "flex",
            alignItems: "center",
            gap: 1.25,
            minHeight: 72,
            flexShrink: 0,
          }}
        >
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: "8px",
              backgroundColor: tokens.primary,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              color: "#fff",
            }}
          >
            <IconActivity size={18} />
          </Box>
          {!collapsed && (
            <Box sx={{ overflow: "hidden" }}>
              <Typography
                sx={{
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "#fff",
                  letterSpacing: "-0.2px",
                  whiteSpace: "nowrap",
                }}
              >
                AI Tracker
              </Typography>
              <Typography
                sx={{ fontSize: "0.6875rem", color: "#475569", whiteSpace: "nowrap" }}
              >
                Usage & cost monitoring
              </Typography>
            </Box>
          )}
        </Box>
  
        {/* Nav items */}
        <Box
          sx={{
            flex: 1,
            overflowY: "auto",
            overflowX: "hidden",
            py: 1,
            // Firefox
            scrollbarWidth: "thin",
            scrollbarColor: "rgba(255,255,255,0.08) transparent",
            // Chrome / Safari / Edge
            "&::-webkit-scrollbar": {
              width: "4px",
            },
            "&::-webkit-scrollbar-track": {
              background: "transparent",
            },
            "&::-webkit-scrollbar-thumb": {
              background: "rgba(255,255,255,0.08)",
              borderRadius: "4px",
            },
            "&::-webkit-scrollbar-thumb:hover": {
              background: "rgba(255,255,255,0.15)",
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
                      pb: 0.5,
                      fontSize: "0.625rem",
                      fontWeight: 500,
                      color: "#334155",
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                    }}
                  >
                    {section.heading}
                  </Typography>
                )}
                {section.heading && collapsed && (
                  <Box
                    sx={{
                      mx: 1,
                      my: 0.5,
                      borderTop: "0.5px solid rgba(255,255,255,0.06)",
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
                        py: "8px",
                        mx: 1,
                        my: "1px",
                        borderRadius: "6px",
                        cursor: "pointer",
                        justifyContent: collapsed ? "center" : "flex-start",
                        backgroundColor: active
                          ? "rgba(59,130,246,0.15)"
                          : "transparent",
                        color: active ? "#fff" : tokens.sidebarText,
                        "&:hover": {
                          backgroundColor: active
                            ? "rgba(59,130,246,0.18)"
                            : "rgba(255,255,255,0.05)",
                          color: active ? "#fff" : "#CBD5E1",
                        },
                        transition: "background-color 0.1s, color 0.1s",
                      }}
                    >
                      {/* Active indicator bar */}
                      {active && (
                        <Box
                          sx={{
                            position: "absolute",
                            left: -8,
                            top: "50%",
                            transform: "translateY(-50%)",
                            width: 3,
                            height: 20,
                            borderRadius: "0 2px 2px 0",
                            backgroundColor: tokens.sidebarAccent,
                          }}
                        />
                      )}
                      <Icon
                        size={16}
                        style={{ flexShrink: 0, opacity: active ? 1 : 0.8 }}
                      />
                      {!collapsed && (
                        <Typography
                          sx={{
                            fontSize: "0.8125rem",
                            fontWeight: active ? 500 : 400,
                            whiteSpace: "nowrap",
                            color: "inherit",
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
  
        {/* User section */}
        <Box
          sx={{
            borderTop: "0.5px solid rgba(255,255,255,0.07)",
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
                p: "6px",
                borderRadius: "6px",
                overflow: "hidden",
              }}
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
                      fontWeight: 500,
                      color: "#E2E8F0",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {user.name}
                  </Typography>
                  <Typography
                    sx={{ fontSize: "0.625rem", color: "#475569", whiteSpace: "nowrap" }}
                  >
                    {user.platformRole.replace("_", " ")}
                  </Typography>
                </Box>
              )}
              {!collapsed && (
                <IconSettings
                  size={14}
                  style={{ color: "#475569", cursor: "pointer", flexShrink: 0 }}
                />
              )}
            </Box>
          )}
  
          {/* Collapse toggle */}
          <Box
            onClick={toggleCollapse}
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: collapsed ? "center" : "flex-end",
              mt: 0.5,
              px: 1,
              py: 0.5,
              borderRadius: "6px",
              cursor: "pointer",
              color: "#334155",
              "&:hover": { color: "#94A3B8" },
              transition: "color 0.1s",
            }}
          >
            {collapsed ? <IconChevronRight size={14} /> : <IconChevronLeft size={14} />}
          </Box>
        </Box>
      </Box>
    );
  }
import { IconBell } from "@tabler/icons-react";
import {
  Badge,
  Box,
  Button,
  CircularProgress,
  Divider,
  IconButton,
  Popover,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  markAllNotificationsRead,
  markNotificationRead,
  notificationsApi,
  type InAppNotification,
} from "@/api/notifications";
import { tokens } from "@/theme/palette";
import { formatRelativeTime } from "@/utils/formatters";

function NotificationItem({
  item,
  onNavigate,
}: {
  item: InAppNotification;
  onNavigate: (item: InAppNotification) => void;
}) {
  return (
    <Box
      onClick={() => onNavigate(item)}
      sx={{
        px: 2,
        py: 1.25,
        cursor: "pointer",
        backgroundColor: item.read ? "transparent" : "action.hover",
        "&:hover": { backgroundColor: "action.selected" },
      }}
    >
      <Typography sx={{ fontSize: "0.8125rem", fontWeight: 600, mb: 0.25 }}>
        {item.title}
      </Typography>
      {item.body && (
        <Typography
          sx={{
            fontSize: "0.75rem",
            color: "text.secondary",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {item.body}
        </Typography>
      )}
      <Typography sx={{ fontSize: "0.6875rem", color: tokens.textMuted, mt: 0.5 }}>
        {formatRelativeTime(item.created_at)}
      </Typography>
    </Box>
  );
}

export function NotificationBell() {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const open = Boolean(anchorEl);

  const unreadQuery = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: notificationsApi.fetchUnreadCount,
    refetchInterval: 60_000,
  });

  const listQuery = useQuery({
    queryKey: ["notifications", "recent", { unreadOnly: true }],
    queryFn: () => notificationsApi.fetchNotifications({ unreadOnly: true, limit: 5 }),
    enabled: open,
  });

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAllMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const unreadCount = unreadQuery.data ?? 0;

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => setAnchorEl(null);

  const handleNavigate = (item: InAppNotification) => {
    const deepLink =
      typeof item.payload?.deep_link === "string"
        ? item.payload.deep_link
        : "/alerts/history";
    if (!item.read) {
      markReadMutation.mutate(item.id);
    }
    handleClose();
    navigate(deepLink);
  };

  return (
    <>
      <IconButton
        size="small"
        aria-label="Notifications"
        onClick={handleOpen}
        sx={{
          border: `0.5px solid ${tokens.border}`,
          borderRadius: "6px",
          width: 32,
          height: 32,
          color: "text.secondary",
          "&:hover": { backgroundColor: "background.default" },
        }}
      >
        <Badge
          badgeContent={unreadCount > 0 ? unreadCount : undefined}
          color="error"
          max={99}
        >
          <IconBell size={16} />
        </Badge>
      </IconButton>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              mt: 0.75,
              width: 340,
              maxWidth: "90vw",
              border: `0.5px solid ${tokens.border}`,
              boxShadow: "0 4px 16px rgba(15,23,42,0.1)",
            },
          },
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            px: 2,
            py: 1.25,
          }}
        >
          <Typography sx={{ fontSize: "0.875rem", fontWeight: 600 }}>
            Notifications
          </Typography>
          {unreadCount > 0 && (
            <Button
              size="small"
              disabled={markAllMutation.isPending}
              onClick={() => markAllMutation.mutate()}
              sx={{ fontSize: "0.75rem", textTransform: "none" }}
            >
              Mark all read
            </Button>
          )}
        </Box>
        <Divider />

        {listQuery.isPending && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
            <CircularProgress size={20} />
          </Box>
        )}

        {!listQuery.isPending && (listQuery.data?.length ?? 0) === 0 && (
          <Typography
            sx={{ px: 2, py: 2.5, fontSize: "0.8125rem", color: "text.secondary" }}
          >
            No unread notifications
          </Typography>
        )}

        {listQuery.data?.map((item) => (
          <NotificationItem key={item.id} item={item} onNavigate={handleNavigate} />
        ))}
      </Popover>
    </>
  );
}

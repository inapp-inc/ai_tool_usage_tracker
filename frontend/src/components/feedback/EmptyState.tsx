import { IconInbox } from "@tabler/icons-react";
import { Box, Button, Typography } from "@mui/material";
import type { ElementType } from "react";

import { tokens } from "@/theme/palette";

interface EmptyStateProps {
  icon?: ElementType;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  size?: "sm" | "md";
}

export function EmptyState({
  icon: Icon = IconInbox,
  title,
  description,
  action,
  size = "md",
}: EmptyStateProps) {
  const isMd = size === "md";

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        py: isMd ? "48px" : "24px",
        gap: isMd ? "12px" : "8px",
      }}
    >
      {isMd ? (
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: "12px",
            backgroundColor: tokens.bgDefault,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: tokens.textMuted,
          }}
        >
          <Icon size={24} />
        </Box>
      ) : (
        <Box sx={{ color: tokens.textMuted, display: "flex" }}>
          <Icon size={20} />
        </Box>
      )}

      <Typography
        variant={isMd ? "body1" : "body2"}
        sx={{ fontWeight: 500, color: "text.primary" }}
      >
        {title}
      </Typography>

      {isMd && description && (
        <Typography variant="body2" sx={{ color: tokens.textMuted, maxWidth: 360 }}>
          {description}
        </Typography>
      )}

      {isMd && action && (
        <Button variant="outlined" size="small" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </Box>
  );
}

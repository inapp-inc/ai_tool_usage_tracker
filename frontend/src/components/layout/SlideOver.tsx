import { IconX } from "@tabler/icons-react";
import {
  Box,
  Drawer,
  IconButton,
  Typography,
} from "@mui/material";
import type { ReactNode } from "react";

import { tokens } from "@/theme/palette";

interface SlideOverProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  width?: number;
  children: ReactNode;
  footer?: ReactNode;
}

export function SlideOver({
  open,
  onClose,
  title,
  subtitle,
  width = 480,
  children,
  footer,
}: SlideOverProps) {
  return (
    <Drawer
      anchor="right"
      variant="temporary"
      open={open}
      onClose={onClose}
      slotProps={{
        paper: {
          sx: {
            width,
            display: "flex",
            flexDirection: "column",
          },
        },
      }}
    >
      <Box
        sx={{
          flexShrink: 0,
          px: "24px",
          py: "20px",
          borderBottom: `0.5px solid ${tokens.border}`,
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 2,
        }}
      >
        <Box>
          <Typography sx={{ fontSize: "0.9375rem", fontWeight: 600 }}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {subtitle}
            </Typography>
          )}
        </Box>
        <IconButton
          size="small"
          onClick={onClose}
          aria-label="Close panel"
          sx={{ mt: -0.5 }}
        >
          <IconX size={16} />
        </IconButton>
      </Box>

      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          px: "24px",
          py: "20px",
        }}
      >
        {children}
      </Box>

      {footer && (
        <Box
          sx={{
            flexShrink: 0,
            borderTop: `0.5px solid ${tokens.border}`,
            px: "24px",
            py: "12px",
            display: "flex",
            justifyContent: "flex-end",
            gap: 1,
          }}
        >
          {footer}
        </Box>
      )}
    </Drawer>
  );
}

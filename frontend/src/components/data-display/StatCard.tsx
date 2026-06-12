import {
  Box,
  Card,
  CardContent,
  Skeleton,
  Typography,
} from "@mui/material";
import { alpha } from "@mui/material/styles";
import type { ElementType } from "react";

import { tokens } from "@/theme/palette";

interface StatCardProps {
  label: string;
  value: string | number;
  delta?: number;
  deltaLabel?: string;
  icon?: ElementType;
  iconColor?: string;
  loading?: boolean;
  onClick?: () => void;
}

export function StatCard({
  label,
  value,
  delta,
  deltaLabel,
  icon: Icon,
  iconColor = tokens.primary,
  loading = false,
  onClick,
}: StatCardProps) {
  const isPositive = delta !== undefined && delta >= 0;
  const deltaColor = isPositive ? tokens.success : tokens.critical;
  const deltaPrefix = isPositive ? "▲ +" : "▼ -";
  const deltaText =
    delta !== undefined
      ? `${deltaPrefix}${Math.abs(delta).toFixed(1)}%`
      : null;

  return (
    <Card
      onClick={onClick}
      sx={{
        cursor: onClick ? "pointer" : "default",
        "&:hover": onClick
          ? { backgroundColor: tokens.bgDefault }
          : undefined,
      }}
    >
      <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: 1,
          }}
        >
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            {label}
          </Typography>
          {Icon && (
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: "8px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                backgroundColor: alpha(iconColor, 0.12),
                color: iconColor,
              }}
            >
              <Icon size={16} />
            </Box>
          )}
        </Box>

        {loading ? (
          <>
            <Skeleton
              animation="wave"
              width="40%"
              height={32}
              sx={{ mt: 1.5, mb: 1 }}
            />
            <Skeleton animation="wave" width="60%" height={14} />
          </>
        ) : (
          <>
            <Typography
              sx={{
                fontSize: "1.5rem",
                fontWeight: 700,
                color: "text.primary",
                mt: 1.5,
                lineHeight: 1.2,
              }}
            >
              {value}
            </Typography>

            {delta !== undefined && (
              <Typography
                component="div"
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.75,
                  mt: 1,
                }}
              >
                <Typography
                  component="span"
                  sx={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: deltaColor,
                  }}
                >
                  {deltaText}
                </Typography>
                {deltaLabel && (
                  <Typography
                    component="span"
                    variant="caption"
                    sx={{ color: tokens.textMuted }}
                  >
                    {deltaLabel}
                  </Typography>
                )}
              </Typography>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

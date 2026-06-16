import { Chip } from "@mui/material";

import { tokens } from "@/theme/palette";

type StatusVariant =
  | "active"
  | "inactive"
  | "paused"
  | "error"
  | "pending"
  | "mapping"
  | "processing"
  | "completed"
  | "cancelled";

interface StatusBadgeProps {
  status: StatusVariant;
  label?: string;
}

const STATUS_COLORS: Record<
  StatusVariant,
  { background: string; color: string }
> = {
  active: { background: "#DCFCE7", color: "#16A34A" },
  inactive: { background: tokens.bgDefault, color: tokens.textMuted },
  paused: { background: "#FEF9C3", color: "#A16207" },
  error: { background: "#FEE2E2", color: "#DC2626" },
  pending: { background: "#EFF6FF", color: "#2563EB" },
  mapping: { background: "#FEF9C3", color: "#A16207" },
  processing: { background: "#EFF6FF", color: "#2563EB" },
  completed: { background: "#DCFCE7", color: "#16A34A" },
  cancelled: { background: tokens.bgDefault, color: tokens.textMuted },
};

function defaultLabel(status: StatusVariant): string {
  if (status === "mapping") {
    return "Map columns";
  }
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const colors = STATUS_COLORS[status];

  return (
    <Chip
      size="small"
      label={label ?? defaultLabel(status)}
      sx={{
        backgroundColor: colors.background,
        color: colors.color,
        fontWeight: 500,
        "& .MuiChip-label": { px: 1 },
      }}
    />
  );
}

export type { StatusVariant };

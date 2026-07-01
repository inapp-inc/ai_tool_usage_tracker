import { IconCalendar } from "@tabler/icons-react";
import {
  Box,
  Button,
  Chip,
  Popover,
  TextField,
  Typography,
} from "@mui/material";
import {
  endOfDay,
  format,
  isSameYear,
  parseISO,
  startOfDay,
  subDays,
} from "date-fns";
import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

import type { DateRange } from "@/types";
import { tokens } from "@/theme/palette";
import { currentMonthUtcRange } from "@/utils/periods";

interface PeriodSelectorProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  /** portal: render in top bar slot (default). inline: render in place. */
  variant?: "portal" | "inline";
}

type PresetKey = "today" | "7d" | "30d" | "90d" | "month" | "custom";

const PRESETS: Array<{ key: PresetKey; label: string }> = [
  { key: "today", label: "Today" },
  { key: "7d", label: "7 days" },
  { key: "30d", label: "30 days" },
  { key: "90d", label: "90 days" },
  { key: "month", label: "This month" },
  { key: "custom", label: "Custom" },
];

function toDateRange(from: Date, to: Date): DateRange {
  return {
    from: startOfDay(from).toISOString(),
    to: endOfDay(to).toISOString(),
  };
}

function computePresetRange(preset: Exclude<PresetKey, "custom">): DateRange {
  const today = new Date();
  const end = endOfDay(today);

  switch (preset) {
    case "today":
      return toDateRange(today, today);
    case "7d":
      return toDateRange(subDays(today, 6), end);
    case "30d":
      return toDateRange(subDays(today, 29), end);
    case "90d":
      return toDateRange(subDays(today, 89), end);
    case "month":
      return currentMonthUtcRange();
  }
}

function formatDisplayRange(from: Date, to: Date): string {
  if (isSameYear(from, to)) {
    return `${format(from, "MMM d")} – ${format(to, "MMM d, yyyy")}`;
  }
  return `${format(from, "MMM d, yyyy")} – ${format(to, "MMM d, yyyy")}`;
}

function toInputDate(iso: string): string {
  return format(parseISO(iso), "yyyy-MM-dd");
}

export function PeriodSelector({
  value,
  onChange,
  variant = "portal",
}: PeriodSelectorProps) {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<PresetKey>("month");
  const [customFrom, setCustomFrom] = useState(() => toInputDate(value.from));
  const [customTo, setCustomTo] = useState(() => toInputDate(value.to));
  const [portalTarget, setPortalTarget] = useState<HTMLElement | null>(null);

  useEffect(() => {
    if (variant === "inline") {
      return;
    }
    const updateTarget = () => {
      setPortalTarget(document.getElementById("topbar-period-slot"));
    };
    updateTarget();
    window.addEventListener("resize", updateTarget);
    return () => window.removeEventListener("resize", updateTarget);
  }, [variant]);

  useEffect(() => {
    setCustomFrom(toInputDate(value.from));
    setCustomTo(toInputDate(value.to));
  }, [value.from, value.to]);

  const displayLabel = useMemo(
    () => formatDisplayRange(parseISO(value.from), parseISO(value.to)),
    [value.from, value.to],
  );

  const handlePresetSelect = (preset: PresetKey) => {
    setSelectedPreset(preset);
    if (preset === "custom") return;

    onChange(computePresetRange(preset));
    setAnchorEl(null);
  };

  const handleApplyCustom = () => {
    const from = startOfDay(new Date(`${customFrom}T00:00:00`));
    const to = endOfDay(new Date(`${customTo}T00:00:00`));
    onChange(toDateRange(from, to));
    setAnchorEl(null);
  };

  const button = (
    <>
      <Box
        component="button"
        type="button"
        onClick={(event) => setAnchorEl(event.currentTarget)}
        sx={{
          height: 32,
          borderRadius: "6px",
          border: `0.5px solid ${tokens.border}`,
          backgroundColor: tokens.bgPaper,
          fontSize: "0.8125rem",
          px: 1.5,
          display: "flex",
          alignItems: "center",
          gap: 1,
          cursor: "pointer",
          color: "text.primary",
          fontFamily: "inherit",
          "&:hover": { backgroundColor: tokens.bgDefault },
        }}
      >
        <IconCalendar size={14} />
        <Typography component="span" sx={{ fontSize: "0.8125rem" }}>
          {displayLabel}
        </Typography>
      </Box>

      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              mt: 0.5,
              p: 2,
              minWidth: 320,
              border: `0.5px solid ${tokens.border}`,
            },
          },
        }}
      >
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}>
          {PRESETS.map((preset) => (
            <Chip
              key={preset.key}
              label={preset.label}
              size="small"
              variant={selectedPreset === preset.key ? "filled" : "outlined"}
              color={selectedPreset === preset.key ? "primary" : "default"}
              onClick={() => handlePresetSelect(preset.key)}
              clickable
            />
          ))}
        </Box>

        {selectedPreset === "custom" && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
            <Box sx={{ display: "flex", gap: 1 }}>
              <TextField
                label="From"
                type="date"
                size="small"
                value={customFrom}
                onChange={(event) => setCustomFrom(event.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
                fullWidth
              />
              <TextField
                label="To"
                type="date"
                size="small"
                value={customTo}
                onChange={(event) => setCustomTo(event.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
                fullWidth
              />
            </Box>
            <Button variant="contained" size="small" onClick={handleApplyCustom}>
              Apply
            </Button>
          </Box>
        )}
      </Popover>
    </>
  );

  if (variant === "inline") {
    return button;
  }

  if (!portalTarget) {
    return button;
  }

  return createPortal(button, portalTarget);
}

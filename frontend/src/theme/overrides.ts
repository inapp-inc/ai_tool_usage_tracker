import type { Components, Theme } from "@mui/material/styles";

import { tokens } from "./palette";

export const overrides: Components<Theme> = {
  MuiButton: {
    defaultProps: {
      disableElevation: true,
    },
    styleOverrides: {
      root: {
        textTransform: "none",
        fontWeight: 500,
        borderRadius: 6,
        fontSize: "0.8125rem",
      },
      sizeSmall: { padding: "4px 10px" },
      sizeMedium: { padding: "7px 14px" },
    },
  },

  MuiCard: {
    styleOverrides: {
      root: {
        boxShadow: "none",
        border: `0.5px solid ${tokens.border}`,
        borderRadius: 10,
        backgroundImage: "none",
      },
    },
  },

  MuiPaper: {
    styleOverrides: {
      root: {
        boxShadow: "none",
        backgroundImage: "none",
      },
      elevation1: {
        boxShadow: "none",
        border: `0.5px solid ${tokens.border}`,
      },
    },
  },

  MuiTableContainer: {
    styleOverrides: {
      root: {
        border: `0.5px solid ${tokens.border}`,
        borderRadius: 10,
        boxShadow: "none",
      },
    },
  },

  MuiTableHead: {
    styleOverrides: {
      root: {
        "& .MuiTableCell-root": {
          backgroundColor: tokens.bgDefault,
          fontWeight: 500,
          fontSize: "0.6875rem",
          textTransform: "uppercase" as const,
          letterSpacing: "0.04em",
          color: tokens.textMuted,
          borderBottom: `0.5px solid ${tokens.border}`,
          padding: "8px 12px",
          userSelect: "none",
        },
      },
    },
  },

  MuiTableBody: {
    styleOverrides: {
      root: {
        "& .MuiTableRow-root:last-child .MuiTableCell-root": {
          borderBottom: "none",
        },
      },
    },
  },

  MuiTableCell: {
    styleOverrides: {
      root: {
        borderBottom: `0.5px solid ${tokens.border}`,
        padding: "9px 12px",
        fontSize: "0.8125rem",
      },
    },
  },

  MuiTableRow: {
    styleOverrides: {
      root: {
        "&:hover td": {
          backgroundColor: tokens.bgDefault,
        },
      },
    },
  },

  MuiChip: {
    styleOverrides: {
      root: {
        fontSize: "0.6875rem",
        fontWeight: 500,
        height: 22,
        borderRadius: 4,
      },
      label: {
        paddingLeft: 7,
        paddingRight: 7,
      },
    },
  },

  MuiOutlinedInput: {
    styleOverrides: {
      root: {
        fontSize: "0.8125rem",
        borderRadius: 6,
        backgroundColor: tokens.bgPaper,
        "& .MuiOutlinedInput-notchedOutline": {
          borderColor: tokens.border,
          borderWidth: "0.5px",
        },
        "&:hover .MuiOutlinedInput-notchedOutline": {
          borderColor: tokens.textMuted,
          borderWidth: "0.5px",
        },
        "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
          borderColor: tokens.primary,
          borderWidth: "1.5px",
        },
      },
      input: {
        padding: "8px 10px",
      },
    },
  },

  MuiInputLabel: {
    styleOverrides: {
      root: {
        fontSize: "0.8125rem",
        fontWeight: 500,
        color: tokens.textMuted,
        "&.Mui-focused": { color: tokens.primary },
      },
    },
  },

  MuiSelect: {
    styleOverrides: {
      select: {
        fontSize: "0.8125rem",
        padding: "8px 10px",
      },
    },
  },

  MuiTooltip: {
    defaultProps: {
      arrow: true,
    },
    styleOverrides: {
      tooltip: {
        fontSize: "0.75rem",
        backgroundColor: "#1E293B",
        borderRadius: 6,
        padding: "5px 10px",
      },
      arrow: {
        color: "#1E293B",
      },
    },
  },

  MuiDrawer: {
    styleOverrides: {
      paper: {
        border: "none",
        boxShadow: "none",
      },
    },
  },

  MuiDivider: {
    styleOverrides: {
      root: {
        borderColor: tokens.border,
        borderWidth: "0.5px",
      },
    },
  },

  MuiAlert: {
    styleOverrides: {
      root: {
        fontSize: "0.8125rem",
        borderRadius: 8,
      },
    },
  },

  MuiLinearProgress: {
    styleOverrides: {
      root: {
        borderRadius: 2,
        height: 5,
        backgroundColor: tokens.bgDefault,
      },
      bar: {
        borderRadius: 2,
      },
    },
  },

  MuiIconButton: {
    styleOverrides: {
      root: {
        borderRadius: 6,
      },
    },
  },

  MuiTab: {
    styleOverrides: {
      root: {
        textTransform: "none",
        fontSize: "0.8125rem",
        fontWeight: 400,
        minHeight: 40,
        padding: "10px 14px",
        "&.Mui-selected": {
          fontWeight: 500,
        },
      },
    },
  },

  MuiTabs: {
    styleOverrides: {
      root: {
        minHeight: 40,
      },
      indicator: {
        height: 2,
        borderRadius: "2px 2px 0 0",
      },
    },
  },

  MuiListItemButton: {
    styleOverrides: {
      root: {
        borderRadius: 6,
        fontSize: "0.8125rem",
      },
    },
  },

  MuiBadge: {
    styleOverrides: {
      badge: {
        fontSize: "0.625rem",
        fontWeight: 700,
        minWidth: 16,
        height: 16,
        padding: "0 4px",
      },
    },
  },

  MuiSnackbar: {
    defaultProps: {
      anchorOrigin: { vertical: "bottom", horizontal: "left" },
      autoHideDuration: 4000,
    },
  },

  MuiDialog: {
    styleOverrides: {
      paper: {
        boxShadow: "0 8px 32px rgba(15,23,42,0.12)",
        border: `0.5px solid ${tokens.border}`,
        borderRadius: 12,
      },
    },
  },
};
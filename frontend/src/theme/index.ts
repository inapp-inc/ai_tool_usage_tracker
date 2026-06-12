import { createTheme } from "@mui/material/styles";

import { overrides } from "./overrides";
import { tokens } from "./palette";
import { typography } from "./typography";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: tokens.primary },
    success: { main: tokens.success },
    warning: { main: tokens.warning },
    error: { main: tokens.critical },
    background: {
      default: tokens.bgDefault,
      paper: tokens.bgPaper,
    },
    text: {
      primary: tokens.textPrimary,
      secondary: tokens.textMuted,
    },
    divider: tokens.border,
  },
  typography,
  components: overrides,
});

export { tokens } from "./palette";

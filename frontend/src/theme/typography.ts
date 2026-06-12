import type { ThemeOptions } from "@mui/material/styles";

import { tokens } from "./palette";

export const typography: ThemeOptions["typography"] = {
  fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  h1: { fontSize: "2rem", fontWeight: 700, lineHeight: 1.2 },
  h2: { fontSize: "1.5rem", fontWeight: 600, lineHeight: 1.3 },
  h3: { fontSize: "1.25rem", fontWeight: 600, lineHeight: 1.4 },
  h4: { fontSize: "1.125rem", fontWeight: 600, lineHeight: 1.4 },
  body1: { fontSize: "0.9375rem", lineHeight: 1.5 },
  body2: { fontSize: "0.875rem", lineHeight: 1.5 },
  caption: { fontSize: "0.75rem", lineHeight: 1.4, color: tokens.textMuted },
};

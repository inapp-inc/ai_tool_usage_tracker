import { Container, Typography } from "@mui/material";

import { t } from "../i18n";

export function DashboardPage() {
  return (
    <Container>
      <Typography variant="h4">{t("routes.dashboard.title")}</Typography>
    </Container>
  );
}

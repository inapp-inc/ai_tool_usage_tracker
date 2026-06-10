import { Container, Typography } from "@mui/material";

import { t } from "../i18n";

export function AdminPage() {
  return (
    <Container>
      <Typography variant="h4">{t("routes.admin.title")}</Typography>
    </Container>
  );
}

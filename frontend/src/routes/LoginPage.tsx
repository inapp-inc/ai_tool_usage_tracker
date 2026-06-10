import { Container, Typography } from "@mui/material";

import { t } from "../i18n";

export function LoginPage() {
  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {t("auth.login.title")}
      </Typography>
      <Typography>{t("auth.login.email")}</Typography>
    </Container>
  );
}

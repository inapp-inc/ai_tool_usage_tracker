import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";

export function PageSkeleton() {
  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "background.default",
      }}
    >
      <CircularProgress size={32} color="primary" />
    </Box>
  );
}

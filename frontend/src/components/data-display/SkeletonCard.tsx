import { Box, Card, CardContent, Skeleton } from "@mui/material";

interface SkeletonCardProps {
  rows?: number;
}

export function SkeletonCard({ rows = 1 }: SkeletonCardProps) {
  return (
    <Card>
      <CardContent sx={{ p: "20px", "&:last-child": { pb: "20px" } }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 1,
          }}
        >
          <Skeleton animation="wave" width="60%" height={14} />
          <Skeleton
            animation="wave"
            variant="rounded"
            width={28}
            height={28}
            sx={{ borderRadius: "8px", flexShrink: 0 }}
          />
        </Box>

        <Skeleton
          animation="wave"
          width="40%"
          height={32}
          sx={{ mt: 1.5 }}
        />

        {rows > 1 && (
          <Skeleton
            animation="wave"
            width="80%"
            height={12}
            sx={{ mt: 1 }}
          />
        )}
      </CardContent>
    </Card>
  );
}

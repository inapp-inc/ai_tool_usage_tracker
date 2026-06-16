import { IconArrowLeft } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  applyUploadMapping,
  fetchUploadMapping,
  type UploadColumnMapping,
} from "@/api/uploads";
import { EmptyState } from "@/components/feedback/EmptyState";
import { tokens } from "@/theme/palette";

const EMPTY_OPTION = "";

function buildInitialMapping(
  suggested: UploadColumnMapping,
  saved: UploadColumnMapping | null,
): UploadColumnMapping {
  return {
    email: saved?.email ?? suggested.email ?? null,
    cost: saved?.cost ?? suggested.cost ?? null,
    model: saved?.model ?? suggested.model ?? null,
    input_tokens: saved?.input_tokens ?? suggested.input_tokens ?? null,
    output_tokens: saved?.output_tokens ?? suggested.output_tokens ?? null,
    tokens: saved?.tokens ?? suggested.tokens ?? null,
    timestamp: saved?.timestamp ?? suggested.timestamp ?? null,
    tool: saved?.tool ?? suggested.tool ?? null,
  };
}

export function UploadMappingPage() {
  const { uploadId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [mapping, setMapping] = useState<UploadColumnMapping>({});

  const mappingQuery = useQuery({
    queryKey: ["uploads", uploadId, "mapping"],
    queryFn: () => fetchUploadMapping(uploadId),
    enabled: Boolean(uploadId),
  });

  useEffect(() => {
    if (!mappingQuery.data) {
      return;
    }
    setMapping(
      buildInitialMapping(
        mappingQuery.data.suggestedMapping,
        mappingQuery.data.columnMapping,
      ),
    );
  }, [mappingQuery.data]);

  const applyMutation = useMutation({
    mutationFn: () => applyUploadMapping(uploadId, mapping),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["uploads"] });
      navigate(`/uploads/${uploadId}/preview`);
    },
  });

  const samplePreview = useMemo(() => {
    if (!mappingQuery.data) {
      return [];
    }
    const { sampleRow, fields } = mappingQuery.data;
    return fields
      .map((field) => {
        const header = mapping[field.key as keyof UploadColumnMapping];
        if (!header) {
          return null;
        }
        const value = sampleRow[header];
        return {
          key: field.key,
          label: field.label,
          value: value == null || value === "" ? "—" : String(value),
        };
      })
      .filter((row): row is NonNullable<typeof row> => row !== null);
  }, [mapping, mappingQuery.data]);

  if (!uploadId) {
    return (
      <EmptyState
        title="Upload not found"
        description="Select an upload from the uploads list."
      />
    );
  }

  const headers = mappingQuery.data?.headers ?? [];
  const fields = mappingQuery.data?.fields ?? [];
  const emailMapped = Boolean(mapping.email);

  return (
    <Box>
      <Button
        variant="text"
        startIcon={<IconArrowLeft size={14} />}
        onClick={() => navigate("/uploads")}
        sx={{ mb: 1, ml: -0.5 }}
      >
        Back to Uploads
      </Button>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Map CSV columns
        </Typography>
        <Typography variant="body2" sx={{ color: tokens.textMuted }}>
          {mappingQuery.data?.fileName ?? "Loading…"} — choose which column
          contains each field before extracting usage data.
        </Typography>
      </Box>

      {mappingQuery.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load column mapping. The upload may already be processed.
        </Alert>
      )}

      {mappingQuery.isPending ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
              gap: 2,
              mb: 3,
            }}
          >
            <Box
              sx={{
                border: `1px solid ${tokens.border}`,
                borderRadius: "10px",
                p: 2,
                backgroundColor: "#FFFFFF",
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
                Detected headers ({headers.length})
              </Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                {headers.map((header) => (
                  <Typography
                    key={header}
                    variant="caption"
                    sx={{
                      px: 1,
                      py: 0.25,
                      borderRadius: "6px",
                      backgroundColor: tokens.bgDefault,
                      border: `1px solid ${tokens.border}`,
                    }}
                  >
                    {header}
                  </Typography>
                ))}
              </Box>
            </Box>

            <Box
              sx={{
                border: `1px solid ${tokens.border}`,
                borderRadius: "10px",
                p: 2,
                backgroundColor: "#FFFFFF",
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
                Sample row preview
              </Typography>
              {samplePreview.length === 0 ? (
                <Typography variant="body2" sx={{ color: tokens.textMuted }}>
                  Select columns below to preview the first data row.
                </Typography>
              ) : (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  {samplePreview.map((row) => (
                    <Box
                      key={row.key}
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 2,
                      }}
                    >
                      <Typography variant="caption" sx={{ color: tokens.textMuted }}>
                        {row.label}
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 500 }}>
                        {row.value}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          </Box>

          <Box
            sx={{
              border: `1px solid ${tokens.border}`,
              borderRadius: "10px",
              p: 2,
              mb: 3,
              backgroundColor: "#FFFFFF",
            }}
          >
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Column mapping
            </Typography>
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" },
                gap: 2,
              }}
            >
              {fields.map((field) => (
                <FormControl key={field.key} fullWidth size="small">
                  <InputLabel id={`map-${field.key}`}>
                    {field.label}
                    {field.required ? " *" : ""}
                  </InputLabel>
                  <Select
                    labelId={`map-${field.key}`}
                    label={`${field.label}${field.required ? " *" : ""}`}
                    value={
                      mapping[field.key as keyof UploadColumnMapping] ??
                      EMPTY_OPTION
                    }
                    onChange={(event) => {
                      const value = event.target.value;
                      setMapping((current) => ({
                        ...current,
                        [field.key]:
                          value === EMPTY_OPTION ? null : value,
                      }));
                    }}
                  >
                    <MenuItem value={EMPTY_OPTION}>
                      <em>Not mapped</em>
                    </MenuItem>
                    {headers.map((header) => (
                      <MenuItem key={header} value={header}>
                        {header}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              ))}
            </Box>
          </Box>

          {applyMutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {applyMutation.error instanceof Error
                ? applyMutation.error.message
                : "Failed to apply column mapping."}
            </Alert>
          )}

          <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1 }}>
            <Button variant="outlined" onClick={() => navigate("/uploads")}>
              Cancel
            </Button>
            <Button
              variant="contained"
              disabled={!emailMapped || applyMutation.isPending}
              onClick={() => applyMutation.mutate()}
              startIcon={
                applyMutation.isPending ? (
                  <CircularProgress size={14} color="inherit" />
                ) : undefined
              }
            >
              Apply & Preview
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
}

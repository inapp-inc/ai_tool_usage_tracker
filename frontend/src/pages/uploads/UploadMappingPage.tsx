import { IconArrowLeft } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  applyUploadMapping,
  fetchUploadMapping,
  type UploadColumnMapping,
} from "@/api/uploads";
import { EmptyState } from "@/components/feedback/EmptyState";
import { tokens } from "@/theme/palette";

import {
  buildInitialColumnMapping,
  isColumnMappingReady,
  UploadColumnMappingForm,
} from "./UploadColumnMappingForm";

const UPLOAD_STEPS = ["Upload file", "Map columns", "Preview & import"];

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
      buildInitialColumnMapping(
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

  if (!uploadId) {
    return (
      <EmptyState
        title="Upload not found"
        description="Select an upload from the uploads list."
      />
    );
  }

  const mappingReady = isColumnMappingReady(mapping, mappingQuery.data?.fields);

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

      <Stepper activeStep={1} alternativeLabel sx={{ mb: 3 }}>
        {UPLOAD_STEPS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Map CSV columns
        </Typography>
        <Typography variant="body2" sx={{ color: tokens.textMuted }}>
          {mappingQuery.data?.fileName ?? "Loading…"} — choose which CSV column
          belongs to each field, then preview and choose rows to import.
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
          <UploadColumnMappingForm
            headers={mappingQuery.data?.headers ?? []}
            fields={mappingQuery.data?.fields ?? []}
            mapping={mapping}
            suggestedMapping={mappingQuery.data?.suggestedMapping ?? {}}
            sampleRow={mappingQuery.data?.sampleRow ?? {}}
            onMappingChange={setMapping}
          />

          {applyMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {applyMutation.error instanceof Error
                ? applyMutation.error.message
                : "Failed to validate upload."}
            </Alert>
          )}

          {!mappingReady && mappingQuery.data && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              Map at least one CSV column to continue.
            </Alert>
          )}

          <Box
            sx={{
              display: "flex",
              justifyContent: "flex-end",
              gap: 1,
              mt: 3,
            }}
          >
            <Button variant="outlined" onClick={() => navigate("/uploads")}>
              Cancel
            </Button>
            <Button
              variant="contained"
              disabled={!mappingReady || applyMutation.isPending}
              onClick={() => applyMutation.mutate()}
              startIcon={
                applyMutation.isPending ? (
                  <CircularProgress size={14} color="inherit" />
                ) : undefined
              }
            >
              Preview rows
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
}

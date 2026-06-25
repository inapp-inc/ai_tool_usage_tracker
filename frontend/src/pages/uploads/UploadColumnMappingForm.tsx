import {
  Alert,
  Box,
  Chip,
  FormControl,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import type { UploadColumnMapping, UploadMappingField } from "@/api/uploads";
import { tokens } from "@/theme/palette";

const EMPTY_OPTION = "";

const FIELD_HINTS: Record<string, string> = {
  email: "User email address",
  tool: "AI tool or vendor name",
  model: "Model used for the request",
  input_tokens: "Prompt / input token count",
  output_tokens: "Completion / output token count",
  tokens: "Total tokens (if not split in/out)",
  cost: "Cost or spend amount",
  timestamp: "When the usage occurred",
  sku: "GitHub billing SKU (e.g. copilot_for_business)",
  unit_type: "Billing unit type (ai_credits or user-months)",
  monthly_amount: "Monthly cost limit from GitHub invoice",
  net_amount: "Net charge for additional usage or credits",
  quantity: "Seat count or credit quantity",
  billing_period_start: "Billing period start date",
  billing_period_end: "Billing period end date",
  user_login: "GitHub user login (optional)",
  user_id: "Figma user ID",
  user_email: "User email address",
  user_name: "User display name",
  seat_type: "Seat type (full or view)",
  seat_credits_used: "Seat credits consumed",
  paid_credits_used: "Paid credits consumed",
  last_activity: "Last activity timestamp",
  usage_period_start: "Usage period start date",
  usage_period_end: "Usage period end date",
};

export function buildInitialColumnMapping(
  suggested: UploadColumnMapping,
  saved: UploadColumnMapping | null,
): UploadColumnMapping {
  const keys = new Set([
    ...Object.keys(suggested),
    ...(saved ? Object.keys(saved) : []),
  ]) as Set<keyof UploadColumnMapping>;

  const merged = {} as UploadColumnMapping;
  for (const key of keys) {
    merged[key] = saved?.[key] ?? suggested[key] ?? null;
  }
  return merged;
}

interface UploadColumnMappingFormProps {
  headers: string[];
  fields: UploadMappingField[];
  mapping: UploadColumnMapping;
  suggestedMapping: UploadColumnMapping;
  sampleRow: Record<string, unknown>;
  onMappingChange: (mapping: UploadColumnMapping) => void;
}

function formatSampleValue(value: unknown): string {
  if (value == null || value === "") {
    return "—";
  }
  return String(value);
}

export function UploadColumnMappingForm({
  headers,
  fields,
  mapping,
  suggestedMapping,
  sampleRow,
  onMappingChange,
}: UploadColumnMappingFormProps) {
  const requiredFields = fields.filter((field) => field.required);
  const optionalFields = fields.filter((field) => !field.required);
  const displayFields = fields.length > 0 ? fields : [];

  const usedHeaders = new Set(
    Object.values(mapping).filter((value): value is string => Boolean(value)),
  );
  const duplicateHeaders = Object.values(mapping).filter(
    (value, index, values) =>
      value && values.indexOf(value) !== index,
  );

  const updateField = (fieldKey: string, header: string | null) => {
    onMappingChange({
      ...mapping,
      [fieldKey]: header,
    });
  };

  const renderRows = (rows: UploadMappingField[]) =>
    rows.map((field) => {
      const selectedHeader =
        mapping[field.key as keyof UploadColumnMapping] ?? EMPTY_OPTION;
      const sampleValue =
        selectedHeader && selectedHeader !== EMPTY_OPTION
          ? formatSampleValue(sampleRow[selectedHeader])
          : "—";
      const autoDetected =
        suggestedMapping[field.key as keyof UploadColumnMapping] ===
          selectedHeader && selectedHeader !== EMPTY_OPTION;

      return (
        <TableRow key={field.key} hover>
          <TableCell sx={{ width: "34%", verticalAlign: "top" }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {field.label}
              {field.required ? " *" : ""}
            </Typography>
            <Typography variant="caption" sx={{ color: tokens.textMuted }}>
              {FIELD_HINTS[field.key] ?? "Optional usage field"}
            </Typography>
          </TableCell>
          <TableCell sx={{ width: "38%", verticalAlign: "top" }}>
            <FormControl fullWidth size="small">
              <Select
                displayEmpty
                value={selectedHeader}
                onChange={(event) => {
                  const value = event.target.value;
                  updateField(
                    field.key,
                    value === EMPTY_OPTION ? null : value,
                  );
                }}
                renderValue={(value) =>
                  value === EMPTY_OPTION ? (
                    <Typography variant="body2" sx={{ color: tokens.textMuted }}>
                      Choose a CSV column…
                    </Typography>
                  ) : (
                    value
                  )
                }
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
            {autoDetected && (
              <Chip
                size="small"
                label="Auto-detected"
                sx={{
                  mt: 0.75,
                  height: 20,
                  fontSize: "0.65rem",
                  backgroundColor: "#EFF6FF",
                  color: "#2563EB",
                }}
              />
            )}
          </TableCell>
          <TableCell sx={{ verticalAlign: "top" }}>
            <Typography
              variant="body2"
              sx={{
                color:
                  sampleValue === "—" ? tokens.textMuted : tokens.textPrimary,
                wordBreak: "break-word",
              }}
            >
              {sampleValue}
            </Typography>
          </TableCell>
        </TableRow>
      );
    });

  return (
    <Box>
      <Alert severity="info" sx={{ mb: 2 }}>
        Match each app field to a column from your CSV. We auto-select likely
        matches — adjust anything that looks wrong, then preview your rows.
      </Alert>

      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          gap: 0.75,
          mb: 2,
        }}
      >
        <Typography variant="caption" sx={{ color: tokens.textMuted, mr: 0.5 }}>
          Columns in your file:
        </Typography>
        {headers.map((header) => (
          <Chip
            key={header}
            size="small"
            label={header}
            variant={usedHeaders.has(header) ? "filled" : "outlined"}
            sx={{
              height: 22,
              fontSize: "0.6875rem",
              ...(usedHeaders.has(header)
                ? { backgroundColor: "#EFF6FF", color: "#2563EB" }
                : {}),
            }}
          />
        ))}
      </Box>

      {duplicateHeaders.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          The same CSV column is mapped to more than one field. Each field should
          use a different column when possible.
        </Alert>
      )}

      <Box
        sx={{
          border: `1px solid ${tokens.border}`,
          borderRadius: "10px",
          overflow: "hidden",
        }}
      >
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: tokens.bgDefault }}>
              <TableCell>App field</TableCell>
              <TableCell>CSV column</TableCell>
              <TableCell>Sample value</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {requiredFields.length > 0 && renderRows(requiredFields)}
            {optionalFields.length > 0 && requiredFields.length > 0 && (
              <TableRow>
                <TableCell colSpan={3} sx={{ backgroundColor: tokens.bgDefault }}>
                  <Typography
                    variant="caption"
                    sx={{ fontWeight: 600, color: tokens.textMuted }}
                  >
                    Other fields
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {renderRows(optionalFields.length > 0 ? optionalFields : displayFields)}
          </TableBody>
        </Table>
      </Box>
    </Box>
  );
}

export function isColumnMappingReady(
  mapping: UploadColumnMapping,
  fields?: UploadMappingField[],
): boolean {
  if (fields && fields.length > 0) {
    const required = fields.filter((field) => field.required);
    if (required.length > 0) {
      return required.every((field) =>
        Boolean(mapping[field.key as keyof UploadColumnMapping]),
      );
    }
  }
  return Object.values(mapping).some((value) => Boolean(value));
}

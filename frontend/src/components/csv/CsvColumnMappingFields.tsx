import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  FormControlLabel,
  FormHelperText,
  InputLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Typography,
} from "@mui/material";

import type { ToolCsvColumnMapping, ToolCsvFormatHint } from "@/api/tools";
import { CSV_NONE_OPTION } from "@/components/csv/csvImportUtils";
import { tokens } from "@/theme/palette";

function ColumnSelect({
  label,
  value,
  headers,
  required = false,
  onChange,
}: {
  label: string;
  value: string;
  headers: string[];
  required?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <FormControl fullWidth size="small" required={required}>
      <InputLabel id={`${label}-label`}>{label}</InputLabel>
      <Select
        labelId={`${label}-label`}
        label={label}
        value={value || CSV_NONE_OPTION}
        onChange={(event) => {
          const next = event.target.value;
          onChange(next === CSV_NONE_OPTION ? "" : next);
        }}
      >
        {!required && <MenuItem value={CSV_NONE_OPTION}>None</MenuItem>}
        {headers.map((header) => (
          <MenuItem key={header} value={header}>
            {header}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export interface CsvColumnMappingFieldsProps {
  headers: string[];
  formatHint: ToolCsvFormatHint;
  columnMapping: ToolCsvColumnMapping;
  onFormatHintChange: (value: ToolCsvFormatHint) => void;
  onMappingChange: (patch: Partial<ToolCsvColumnMapping>) => void;
  onPreview?: () => void;
  previewPending?: boolean;
  mappingReady?: boolean;
  showPreviewButton?: boolean;
}

export function CsvColumnMappingFields({
  headers,
  formatHint,
  columnMapping,
  onFormatHintChange,
  onMappingChange,
  onPreview,
  previewPending = false,
  mappingReady = false,
  showPreviewButton = true,
}: CsvColumnMappingFieldsProps) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
        Map CSV columns
      </Typography>

      <FormControl fullWidth size="small">
        <Typography variant="caption" sx={{ color: tokens.textMuted, mb: 0.5 }}>
          CSV layout
        </Typography>
        <RadioGroup
          row
          value={formatHint}
          onChange={(event) => {
            onFormatHintChange(event.target.value as ToolCsvFormatHint);
          }}
        >
          <FormControlLabel
            value="daily"
            control={<Radio size="small" />}
            label="One row per day"
          />
          <FormControlLabel
            value="summary"
            control={<Radio size="small" />}
            label="Summary row"
          />
        </RadioGroup>
      </FormControl>

      <ColumnSelect
        label="Token used"
        value={columnMapping.tokenColumn}
        headers={headers}
        required
        onChange={(value) => onMappingChange({ tokenColumn: value })}
      />

      <ColumnSelect
        label="Total cost"
        value={columnMapping.costColumn}
        headers={headers}
        onChange={(value) => onMappingChange({ costColumn: value })}
      />

      {formatHint === "daily" ? (
        <ColumnSelect
          label="Date"
          value={columnMapping.dateColumn}
          headers={headers}
          required
          onChange={(value) => onMappingChange({ dateColumn: value })}
        />
      ) : (
        <>
          <ColumnSelect
            label="Date from"
            value={columnMapping.dateFromColumn}
            headers={headers}
            onChange={(value) => onMappingChange({ dateFromColumn: value })}
          />
          <ColumnSelect
            label="Date to"
            value={columnMapping.dateToColumn}
            headers={headers}
            onChange={(value) => onMappingChange({ dateToColumn: value })}
          />
          <FormHelperText sx={{ mt: -1 }}>
            Select at least one of date-from or date-to for summary CSVs.
          </FormHelperText>
        </>
      )}

      {showPreviewButton && onPreview && (
        <Button
          variant="outlined"
          size="small"
          disabled={!mappingReady || previewPending}
          onClick={onPreview}
          startIcon={
            previewPending ? <CircularProgress size={14} color="inherit" /> : undefined
          }
          sx={{ alignSelf: "flex-start" }}
        >
          Preview extraction
        </Button>
      )}
    </Box>
  );
}

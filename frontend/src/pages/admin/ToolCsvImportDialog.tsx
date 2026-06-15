import { IconUpload } from "@tabler/icons-react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef, useState, type DragEvent } from "react";

import { ApiClientError } from "@/api/client";
import {
  EMPTY_CSV_COLUMN_MAPPING,
  importToolCsv,
  inspectToolCsvImport,
  previewToolCsvImport,
  type AiTool,
  type ToolCsvColumnMapping,
  type ToolCsvFormatHint,
  type ToolCsvImportMode,
  type ToolCsvImportPreview,
} from "@/api/tools";
import type { Provider } from "@/api/providers";
import { CsvColumnMappingFields } from "@/components/csv/CsvColumnMappingFields";
import { csvMappingIsComplete } from "@/components/csv/csvImportUtils";
import { tokens } from "@/theme/palette";
import { formatCost, formatTokens } from "@/utils/formatters";

interface ToolCsvImportDialogProps {
  open: boolean;
  onClose: () => void;
  providers: Provider[];
  tools: AiTool[];
  initialTool?: AiTool | null;
  onSuccess: (message: string) => void;
}

export function ToolCsvImportDialog({
  open,
  onClose,
  providers,
  tools,
  initialTool = null,
  onSuccess,
}: ToolCsvImportDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("");
  const [mode, setMode] = useState<ToolCsvImportMode>("create");
  const [toolId, setToolId] = useState("");
  const [replaceExisting, setReplaceExisting] = useState(true);
  const [headers, setHeaders] = useState<string[]>([]);
  const [formatHint, setFormatHint] = useState<ToolCsvFormatHint>("daily");
  const [columnMapping, setColumnMapping] = useState<ToolCsvColumnMapping>(
    EMPTY_CSV_COLUMN_MAPPING,
  );
  const [preview, setPreview] = useState<ToolCsvImportPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    if (initialTool) {
      setMode("update");
      setToolId(initialTool.id);
      setName(initialTool.name);
      setProvider(initialTool.provider);
    } else {
      setMode("create");
      setToolId("");
      setName("");
      setProvider(providers[0]?.slug ?? "");
    }
    setSelectedFile(null);
    setHeaders([]);
    setFormatHint("daily");
    setColumnMapping(EMPTY_CSV_COLUMN_MAPPING);
    setPreview(null);
    setPreviewError(null);
    setReplaceExisting(true);
  }, [open, initialTool, providers]);

  useEffect(() => {
    if (mode === "update" && toolId) {
      const tool = tools.find((item) => item.id === toolId);
      if (tool) {
        setName(tool.name);
        setProvider(tool.provider);
      }
    }
  }, [mode, toolId, tools]);

  const inspectMutation = useMutation({
    mutationFn: inspectToolCsvImport,
    onSuccess: (result) => {
      setHeaders(result.headers);
      setFormatHint(result.formatHint);
      setColumnMapping(result.suggestedMapping);
      setPreview(null);
      setPreviewError(null);
    },
    onError: (error: Error) => {
      setHeaders([]);
      setPreview(null);
      setPreviewError(
        error instanceof ApiClientError
          ? error.apiError.detail
          : error.message || "Could not read CSV headers.",
      );
    },
  });

  const previewMutation = useMutation({
    mutationFn: ({
      file,
      mapping,
    }: {
      file: File;
      mapping: ToolCsvColumnMapping;
    }) => previewToolCsvImport(file, mapping),
    onSuccess: (result) => {
      setPreview(result);
      setPreviewError(null);
    },
    onError: (error: Error) => {
      setPreview(null);
      setPreviewError(
        error instanceof ApiClientError
          ? error.apiError.detail
          : error.message || "Could not parse CSV file.",
      );
    },
  });

  const importMutation = useMutation({
    mutationFn: importToolCsv,
    onSuccess: (result) => {
      onSuccess(result.message);
      onClose();
    },
  });

  useEffect(() => {
    if (!selectedFile || !csvMappingIsComplete(formatHint, columnMapping)) {
      return;
    }
    if (previewMutation.isPending || inspectMutation.isPending) {
      return;
    }
    previewMutation.mutate({ file: selectedFile, mapping: columnMapping });
  }, [selectedFile, formatHint, columnMapping]);

  const handleFileSelect = (file: File | null) => {
    if (!file || !file.name.toLowerCase().endsWith(".csv")) {
      setPreviewError("Please select a CSV file.");
      return;
    }
    setSelectedFile(file);
    setPreview(null);
    setPreviewError(null);
    inspectMutation.mutate(file);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    handleFileSelect(event.dataTransfer.files.item(0));
  };

  const updateMapping = (patch: Partial<ToolCsvColumnMapping>) => {
    setColumnMapping((current) => ({ ...current, ...patch }));
    setPreview(null);
    setPreviewError(null);
  };

  const handlePreview = () => {
    if (!selectedFile || !csvMappingIsComplete(formatHint, columnMapping)) {
      return;
    }
    previewMutation.mutate({ file: selectedFile, mapping: columnMapping });
  };

  const mappingReady = csvMappingIsComplete(formatHint, columnMapping);
  const canImport =
    Boolean(selectedFile && mappingReady && name.trim() && provider) &&
    (mode === "create" || Boolean(toolId));

  const importError =
    importMutation.error instanceof ApiClientError
      ? importMutation.error.apiError.detail
      : importMutation.error instanceof Error
        ? importMutation.error.message
        : null;

  const isBusy =
    inspectMutation.isPending ||
    previewMutation.isPending ||
    importMutation.isPending;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Import usage from CSV</DialogTitle>
      <DialogContent>
        <Typography variant="body2" sx={{ color: tokens.textMuted, mb: 2 }}>
          Upload a CSV, map your column headers to tokens, cost, and dates, then
          create or update a tool.
        </Typography>

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          hidden
          onChange={(event) => {
            handleFileSelect(event.target.files?.item(0) ?? null);
            event.target.value = "";
          }}
        />

        <Box
          onClick={() => {
            if (!selectedFile) {
              fileInputRef.current?.click();
            }
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          sx={{
            border: `2px dashed ${isDragOver ? tokens.primary : tokens.border}`,
            borderRadius: "10px",
            p: 3,
            textAlign: "center",
            cursor: selectedFile ? "default" : "pointer",
            backgroundColor: isDragOver ? "#EFF6FF" : tokens.bgDefault,
            mb: 2,
          }}
        >
          {inspectMutation.isPending ? (
            <CircularProgress size={24} />
          ) : selectedFile ? (
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {selectedFile.name}
              </Typography>
              <Button
                size="small"
                sx={{ mt: 1 }}
                onClick={(event) => {
                  event.stopPropagation();
                  fileInputRef.current?.click();
                }}
              >
                Choose another file
              </Button>
            </Box>
          ) : (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <IconUpload size={24} color={tokens.textMuted} />
              <Typography variant="body2">
                Drag and drop a CSV file, or click to browse
              </Typography>
            </Box>
          )}
        </Box>

        {(previewError || importError) && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {previewError ?? importError}
          </Alert>
        )}

        {headers.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <CsvColumnMappingFields
              headers={headers}
              formatHint={formatHint}
              columnMapping={columnMapping}
              onFormatHintChange={(value) => {
                setFormatHint(value);
                setPreview(null);
                setPreviewError(null);
              }}
              onMappingChange={updateMapping}
              onPreview={handlePreview}
              previewPending={previewMutation.isPending}
              mappingReady={mappingReady}
            />
          </Box>
        )}

        {preview && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Extracted {formatTokens(preview.tokenCount)} tokens and{" "}
            {formatCost(preview.costTotal)}
            {preview.dateFrom && preview.dateTo
              ? ` from ${preview.dateFrom} to ${preview.dateTo}`
              : ""}{" "}
            ({preview.rowCount} row{preview.rowCount === 1 ? "" : "s"}).
          </Alert>
        )}

        <FormControl fullWidth size="small" sx={{ mb: 2 }}>
          <Typography variant="caption" sx={{ color: tokens.textMuted, mb: 0.5 }}>
            Import mode
          </Typography>
          <RadioGroup
            row
            value={mode}
            onChange={(event) =>
              setMode(event.target.value as ToolCsvImportMode)
            }
          >
            <FormControlLabel
              value="create"
              control={<Radio size="small" />}
              label="Create new tool"
            />
            <FormControlLabel
              value="update"
              control={<Radio size="small" />}
              label="Update existing tool"
            />
          </RadioGroup>
        </FormControl>

        {mode === "update" && (
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel id="csv-tool-select-label">Existing tool</InputLabel>
            <Select
              labelId="csv-tool-select-label"
              label="Existing tool"
              value={toolId}
              onChange={(event) => setToolId(event.target.value)}
            >
              {tools.map((tool) => (
                <MenuItem key={tool.id} value={tool.id}>
                  {tool.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        <TextField
          fullWidth
          size="small"
          label="Tool name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          sx={{ mb: 2 }}
        />

        <FormControl fullWidth size="small" sx={{ mb: 2 }}>
          <InputLabel id="csv-provider-label">Provider</InputLabel>
          <Select
            labelId="csv-provider-label"
            label="Provider"
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
          >
            {providers.map((option) => (
              <MenuItem key={option.slug} value={option.slug}>
                {option.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {mode === "update" && (
          <FormControl fullWidth>
            <FormControlLabel
              control={
                <Switch
                  checked={replaceExisting}
                  onChange={(event) => setReplaceExisting(event.target.checked)}
                />
              }
              label="Replace current usage data"
            />
            <FormHelperText>
              {replaceExisting
                ? "Existing token and cost totals will be overwritten with CSV data."
                : "CSV data will be merged into existing daily usage by date."}
            </FormHelperText>
          </FormControl>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={isBusy}>
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={!canImport || isBusy}
          onClick={() => {
            if (!selectedFile || !preview) {
              return;
            }
            importMutation.mutate({
              file: selectedFile,
              name: name.trim(),
              provider,
              mode,
              toolId: mode === "update" ? toolId : undefined,
              replaceExisting,
              columnMapping,
            });
          }}
          startIcon={
            importMutation.isPending ? (
              <CircularProgress size={14} color="inherit" />
            ) : undefined
          }
        >
          {mode === "update" ? "Update tool" : "Create tool"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { IconChevronDown } from "@tabler/icons-react";
import { Controller, type Control, type FieldErrors } from "react-hook-form";

import { tokens } from "@/theme/palette";
import type { UsagePollingFormValues } from "@/types/integrationConfig";

export interface ToolFormWithPolling extends UsagePollingFormValues {
  name: string;
  parentProvider: string;
  provider: string;
  description: string;
  apiEndpoint?: string;
  organizationId?: string;
}

interface ToolUsagePollingFormProps {
  control: Control<ToolFormWithPolling>;
  errors: FieldErrors<ToolFormWithPolling>;
  enabled: boolean;
}

export function ToolUsagePollingForm({
  control,
  errors,
  enabled,
}: ToolUsagePollingFormProps) {
  return (
    <Accordion
      defaultExpanded
      disableGutters
      elevation={0}
      sx={{
        border: `1px solid ${tokens.border}`,
        borderRadius: "8px !important",
        "&:before": { display: "none" },
      }}
    >
      <AccordionSummary expandIcon={<IconChevronDown size={16} />}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          Usage polling
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 0 }}>
        <Controller
          name="enabled"
          control={control}
          render={({ field }) => (
            <FormControlLabel
              control={
                <Switch
                  checked={field.value}
                  onChange={(_, checked) => field.onChange(checked)}
                  size="small"
                />
              }
              label="Poll usage from API endpoint"
            />
          )}
        />

        {!enabled ? (
          <Typography variant="caption" sx={{ color: tokens.textMuted }}>
            Disabled — legacy built-in adapter may run if available for this provider label.
          </Typography>
        ) : (
          <>
            <Controller
              name="authType"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="auth-type-label">Auth type</InputLabel>
                  <Select {...field} labelId="auth-type-label" label="Auth type">
                    <MenuItem value="bearer">Bearer token</MenuItem>
                    <MenuItem value="api_key_header">API key header</MenuItem>
                  </Select>
                </FormControl>
              )}
            />

            <Controller
              name="authHeader"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Auth header name"
                  error={Boolean(errors.authHeader)}
                  helperText={errors.authHeader?.message}
                />
              )}
            />

            <Controller
              name="authPrefix"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Auth prefix"
                  helperText='e.g. "Bearer " (for bearer auth)'
                />
              )}
            />

            <Controller
              name="method"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="usage-method-label">HTTP method</InputLabel>
                  <Select {...field} labelId="usage-method-label" label="HTTP method">
                    <MenuItem value="GET">GET</MenuItem>
                    <MenuItem value="POST">POST</MenuItem>
                  </Select>
                </FormControl>
              )}
            />

            <Controller
              name="usageUrl"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Usage URL"
                  placeholder="{api_endpoint}"
                  error={Boolean(errors.usageUrl)}
                  helperText={
                    errors.usageUrl?.message ??
                    "Use {api_endpoint} to reuse the API Endpoint URL above."
                  }
                />
              )}
            />

            <Controller
              name="querySinceName"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Query param name (start)"
                  placeholder="since"
                  helperText="Vendor-specific parameter name for range start"
                />
              )}
            />

            <Controller
              name="querySinceValue"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Query param value (start)"
                  placeholder="{since_iso}"
                />
              )}
            />

            <Controller
              name="queryUntilName"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Query param name (end)"
                  placeholder="until"
                />
              )}
            />

            <Controller
              name="queryUntilValue"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Query param value (end)"
                  placeholder="{until_iso}"
                />
              )}
            />

            <Controller
              name="extraHeadersJson"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Extra HTTP headers (JSON)"
                  multiline
                  minRows={3}
                  helperText='e.g. {"Accept": "application/vnd.github+json"} — any vendor headers'
                />
              )}
            />

            <Controller
              name="responseType"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth size="small">
                  <InputLabel id="response-type-label">Response type</InputLabel>
                  <Select {...field} labelId="response-type-label" label="Response type">
                    <MenuItem value="json_array">JSON array</MenuItem>
                    <MenuItem value="json_object">JSON object</MenuItem>
                  </Select>
                </FormControl>
              )}
            />

            <Controller
              name="recordsPath"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Records path"
                  placeholder="data.items"
                  helperText="Dot path to the array of usage rows (leave empty if root is the array)."
                />
              )}
            />

            <Typography variant="caption" sx={{ color: tokens.textMuted, fontWeight: 600 }}>
              Field mapping (dot paths on each record)
            </Typography>

            <Controller
              name="fieldEventId"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Event ID"
                  required
                  error={Boolean(errors.fieldEventId)}
                  helperText={errors.fieldEventId?.message ?? "e.g. id or {date}"}
                />
              )}
            />

            <Controller
              name="fieldOccurredAt"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Occurred at"
                  required
                  error={Boolean(errors.fieldOccurredAt)}
                  helperText={errors.fieldOccurredAt?.message}
                />
              )}
            />

            <Controller
              name="fieldInputTokens"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Input tokens"
                  required
                  error={Boolean(errors.fieldInputTokens)}
                  helperText={errors.fieldInputTokens?.message}
                />
              )}
            />

            <Controller
              name="fieldOutputTokens"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Output tokens"
                  helperText="Dot path or literal 0"
                />
              )}
            />

            <Controller
              name="fieldCost"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Estimated cost"
                  helperText="Dot path or literal 0"
                />
              )}
            />

            <Controller
              name="fieldModel"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="Model"
                  helperText="Dot path or literal name"
                />
              )}
            />

            <Controller
              name="fieldUserEmail"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="User email"
                  placeholder="email"
                  helperText="Dot path, e.g. email, user_email, user.login"
                />
              )}
            />

            <Controller
              name="fieldUserName"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  size="small"
                  label="User name"
                  placeholder="name"
                  helperText="Dot path, e.g. name, user_name, display_name"
                />
              )}
            />
          </>
        )}
      </AccordionDetails>
    </Accordion>
  );
}

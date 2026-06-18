/** Tool integration_config — usage polling (matches backend schema). */

export type AuthType = "bearer" | "api_key_header";

export type UsageResponseType = "json_array" | "json_object";

export interface ToolIntegrationAuth {
  type: AuthType;
  header: string;
  prefix: string;
}

export interface ToolIntegrationUsageFields {
  vendor_event_id: string;
  occurred_at: string;
  input_tokens: string;
  output_tokens?: string;
  estimated_cost?: string;
  model?: string;
  user_email?: string;
  user_name?: string;
}

export interface ToolIntegrationUsage {
  method: "GET" | "POST";
  url: string;
  query?: Record<string, string>;
  response: {
    type: UsageResponseType;
    records_path?: string;
    fields: ToolIntegrationUsageFields;
  };
}

export interface ToolIntegrationConfig {
  version: 1;
  auth: ToolIntegrationAuth;
  headers: Record<string, string>;
  usage: ToolIntegrationUsage;
}

export interface UsagePollingFormValues {
  enabled: boolean;
  authType: AuthType;
  authHeader: string;
  authPrefix: string;
  method: "GET" | "POST";
  usageUrl: string;
  querySinceName: string;
  querySinceValue: string;
  queryUntilName: string;
  queryUntilValue: string;
  extraHeadersJson: string;
  responseType: UsageResponseType;
  recordsPath: string;
  fieldEventId: string;
  fieldOccurredAt: string;
  fieldInputTokens: string;
  fieldOutputTokens: string;
  fieldCost: string;
  fieldModel: string;
  fieldUserEmail: string;
  fieldUserName: string;
}

export function defaultUsagePollingFormValues(): UsagePollingFormValues {
  return {
    enabled: false,
    authType: "bearer",
    authHeader: "Authorization",
    authPrefix: "Bearer ",
    method: "GET",
    usageUrl: "{api_endpoint}",
    querySinceName: "since",
    querySinceValue: "{since_iso}",
    queryUntilName: "until",
    queryUntilValue: "{until_iso}",
    extraHeadersJson: '{\n  "Accept": "application/json"\n}',
    responseType: "json_array",
    recordsPath: "",
    fieldEventId: "id",
    fieldOccurredAt: "timestamp",
    fieldInputTokens: "tokens_used",
    fieldOutputTokens: "0",
    fieldCost: "0",
    fieldModel: "default",
    fieldUserEmail: "email",
    fieldUserName: "name",
  };
}

export function parseExtraHeaders(json: string): Record<string, string> {
  const trimmed = json.trim();
  if (!trimmed) {
    return { Accept: "application/json" };
  }
  try {
    const parsed = JSON.parse(trimmed) as Record<string, unknown>;
    const headers: Record<string, string> = {};
    for (const [key, value] of Object.entries(parsed)) {
      if (value != null && String(value).trim()) {
        headers[key] = String(value);
      }
    }
    return Object.keys(headers).length > 0 ? headers : { Accept: "application/json" };
  } catch {
    return { Accept: "application/json" };
  }
}

export function isIntegrationConfigEmpty(
  config: ToolIntegrationConfig | null | undefined,
): boolean {
  return !config?.usage?.url;
}

export function formValuesToIntegrationConfig(
  values: UsagePollingFormValues,
): ToolIntegrationConfig | null {
  if (!values.enabled) {
    return null;
  }

  const query: Record<string, string> = {};
  const sinceName = values.querySinceName.trim();
  const untilName = values.queryUntilName.trim();
  if (sinceName && values.querySinceValue.trim()) {
    query[sinceName] = values.querySinceValue.trim();
  }
  if (untilName && values.queryUntilValue.trim()) {
    query[untilName] = values.queryUntilValue.trim();
  }

  return {
    version: 1,
    auth: {
      type: values.authType,
      header: values.authHeader.trim() || "Authorization",
      prefix: values.authPrefix,
    },
    headers: parseExtraHeaders(values.extraHeadersJson),
    usage: {
      method: values.method,
      url: values.usageUrl.trim() || "{api_endpoint}",
      query: Object.keys(query).length > 0 ? query : undefined,
      response: {
        type: values.responseType,
        records_path: values.recordsPath.trim() || undefined,
        fields: {
          vendor_event_id: values.fieldEventId.trim(),
          occurred_at: values.fieldOccurredAt.trim(),
          input_tokens: values.fieldInputTokens.trim(),
          output_tokens: values.fieldOutputTokens.trim() || "0",
          estimated_cost: values.fieldCost.trim() || "0",
          model: values.fieldModel.trim() || "default",
          user_email: values.fieldUserEmail.trim() || undefined,
          user_name: values.fieldUserName.trim() || undefined,
        },
      },
    },
  };
}

function pickQueryEntry(
  query: Record<string, string> | undefined,
  preferredKey: string,
  fallbackIndex: number,
): [string, string] {
  const entries = Object.entries(query ?? {});
  const match = entries.find(([key]) => key === preferredKey);
  if (match) {
    return match;
  }
  const fallback = entries[fallbackIndex];
  if (fallback) {
    return fallback;
  }
  return [preferredKey, preferredKey === "since" ? "{since_iso}" : "{until_iso}"];
}

export function integrationConfigToFormValues(
  config: ToolIntegrationConfig | null | undefined,
): UsagePollingFormValues {
  const defaults = defaultUsagePollingFormValues();
  if (!config?.usage) {
    return { ...defaults, enabled: false };
  }

  const usage = config.usage;
  const fields = usage.response?.fields ?? ({} as ToolIntegrationUsageFields);
  const [sinceName, sinceValue] = pickQueryEntry(usage.query, "since", 0);
  const [untilName, untilValue] = pickQueryEntry(usage.query, "until", 1);

  return {
    enabled: true,
    authType: config.auth?.type ?? "bearer",
    authHeader: config.auth?.header ?? "Authorization",
    authPrefix: config.auth?.prefix ?? "Bearer ",
    method: usage.method ?? "GET",
    usageUrl: usage.url ?? "{api_endpoint}",
    querySinceName: sinceName,
    querySinceValue: sinceValue,
    queryUntilName: untilName,
    queryUntilValue: untilValue,
    extraHeadersJson: JSON.stringify(config.headers ?? { Accept: "application/json" }, null, 2),
    responseType: usage.response?.type ?? "json_array",
    recordsPath: usage.response?.records_path ?? "",
    fieldEventId: fields.vendor_event_id ?? "id",
    fieldOccurredAt: fields.occurred_at ?? "timestamp",
    fieldInputTokens: fields.input_tokens ?? "tokens_used",
    fieldOutputTokens: fields.output_tokens ?? "0",
    fieldCost: fields.estimated_cost ?? "0",
    fieldModel: fields.model ?? "default",
    fieldUserEmail: fields.user_email ?? "email",
    fieldUserName: fields.user_name ?? "name",
  };
}

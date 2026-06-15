import type { ToolCsvColumnMapping, ToolCsvFormatHint } from "@/api/tools";

export const CSV_NONE_OPTION = "__none__";

export function csvMappingIsComplete(
  formatHint: ToolCsvFormatHint,
  mapping: ToolCsvColumnMapping,
): boolean {
  if (!mapping.tokenColumn) {
    return false;
  }
  if (formatHint === "daily") {
    return Boolean(mapping.dateColumn);
  }
  return Boolean(mapping.dateFromColumn || mapping.dateToColumn);
}

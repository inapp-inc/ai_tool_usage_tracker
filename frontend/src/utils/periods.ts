/** UTC period helpers aligned with backend team metrics. */

import type { DateRange } from "@/types";

/** Calendar month start (UTC) through now — matches Teams page total cost. */
export function currentMonthUtcRange(): DateRange {
  const now = new Date();
  const monthStart = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1, 0, 0, 0, 0),
  );
  return {
    from: monthStart.toISOString(),
    to: now.toISOString(),
  };
}

/** UTC period helpers aligned with backend team metrics. */

import { endOfDay, startOfDay } from "date-fns";

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

function clampDay(year: number, monthIndex: number, day: number): Date {
  const lastDay = new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
  return new Date(Date.UTC(year, monthIndex, Math.min(day, lastDay)));
}

function nextSubscriptionPeriodStart(anchor: Date, periodStart: Date): Date {
  const monthIndex = periodStart.getUTCMonth() + 1;
  const year = periodStart.getUTCFullYear() + (monthIndex > 11 ? 1 : 0);
  const normalizedMonth = monthIndex % 12;
  return clampDay(year, normalizedMonth, anchor.getUTCDate());
}

/** Subscription billing period containing ``onDate`` (UTC, inclusive end). */
export function subscriptionPeriodForDate(anchorIso: string, onDate: Date): { from: Date; to: Date } {
  const anchor = new Date(`${anchorIso.slice(0, 10)}T00:00:00.000Z`);
  const anchorDay = anchor.getUTCDate();
  let start = clampDay(onDate.getUTCFullYear(), onDate.getUTCMonth(), anchorDay);
  if (onDate < start) {
    const monthIndex = onDate.getUTCMonth() - 1;
    const year = onDate.getUTCFullYear() + (monthIndex < 0 ? -1 : 0);
    const normalizedMonth = (monthIndex + 12) % 12;
    start = clampDay(year, normalizedMonth, anchorDay);
  }
  const nextStart = nextSubscriptionPeriodStart(anchor, start);
  const end = new Date(nextStart.getTime() - 24 * 60 * 60 * 1000);
  return { from: start, to: end };
}

/** Current subscription billing cycle as an Insights date range. */
export function currentSubscriptionPeriodRange(anchorIso: string, onDate = new Date()): DateRange {
  const { from, to } = subscriptionPeriodForDate(anchorIso, onDate);
  return {
    from: startOfDay(from).toISOString(),
    to: endOfDay(to).toISOString(),
  };
}

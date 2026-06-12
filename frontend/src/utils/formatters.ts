import {
  format,
  formatDistanceToNow,
  parseISO,
} from "date-fns";

export function formatTokens(n: number): string {
  if (n >= 1_000_000) {
    const value = n / 1_000_000;
    return `${value % 1 === 0 ? value.toFixed(0) : value.toFixed(1)}M`;
  }
  if (n >= 1_000) {
    return `${Math.round(n / 1_000)}K`;
  }
  return n.toLocaleString("en-US");
}

export function formatCost(n: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(n);
}

export function formatPercent(n: number, decimals = 1): string {
  return `${(n * 100).toFixed(decimals)}%`;
}

export function formatRelativeTime(isoDate: string): string {
  return formatDistanceToNow(parseISO(isoDate), { addSuffix: true });
}

export function formatDate(isoDate: string): string {
  return format(parseISO(isoDate), "MMM d, yyyy");
}

export function formatDateTime(isoDate: string): string {
  return format(parseISO(isoDate), "MMM d, yyyy · HH:mm");
}

import { endOfDay, parseISO, startOfDay } from "date-fns";

const MOCK_LATENCY_MS = 400;

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), ms);
  });
}

export type AuditAction =
  | "user.invite"
  | "user.remove"
  | "user.role_change"
  | "team.create"
  | "team.update"
  | "team.delete"
  | "tool.connect"
  | "tool.update"
  | "tool.delete"
  | "credential.generate"
  | "credential.revoke"
  | "alert.create"
  | "alert.update"
  | "alert.delete"
  | "upload.submit"
  | "upload.delete"
  | "report.generate"
  | "report.delete"
  | "auth.login"
  | "auth.logout";

export type AuditCategory =
  | "auth"
  | "user"
  | "team"
  | "tool"
  | "credential"
  | "alert"
  | "upload"
  | "report";

export interface AuditLogEntry {
  id: string;
  action: AuditAction;
  category: AuditCategory;
  actorName: string;
  actorEmail: string;
  actorRole: string;
  targetType: string | null;
  targetName: string | null;
  description: string;
  ipAddress: string;
  createdAt: string;
}

export interface AuditLogFilters {
  search: string;
  category: AuditCategory | "";
  from: string;
  to: string;
}

function daysAgo(days: number, hours = 0): string {
  return new Date(
    Date.now() - days * 24 * 60 * 60 * 1000 - hours * 60 * 60 * 1000,
  ).toISOString();
}

const mockAuditLog: AuditLogEntry[] = [
  {
    id: "audit_1",
    action: "auth.login",
    category: "auth",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: null,
    targetName: null,
    description: "Signed in to the platform",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(0, 2),
  },
  {
    id: "audit_2",
    action: "user.invite",
    category: "user",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "User",
    targetName: "alice@co.com",
    description: "Invited alice@co.com as Team Admin",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(1, 4),
  },
  {
    id: "audit_3",
    action: "team.create",
    category: "team",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "Team",
    targetName: "Platform Engineering",
    description: "Created team Platform Engineering with a 5M token budget",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(2, 1),
  },
  {
    id: "audit_4",
    action: "tool.connect",
    category: "tool",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Tool",
    targetName: "OpenAI Production",
    description: "Connected OpenAI Production integration",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(3, 6),
  },
  {
    id: "audit_5",
    action: "credential.generate",
    category: "credential",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "Credential",
    targetName: "Engineering API Key",
    description: "Generated new API credential for Engineering team",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(4, 3),
  },
  {
    id: "audit_6",
    action: "alert.create",
    category: "alert",
    actorName: "Sam Rivera",
    actorEmail: "sam.rivera@acme.com",
    actorRole: "Team Admin",
    targetType: "Alert",
    targetName: "Engineering Budget Threshold",
    description: "Created budget alert at 80% for Engineering team",
    ipAddress: "172.16.0.55",
    createdAt: daysAgo(5, 8),
  },
  {
    id: "audit_7",
    action: "upload.submit",
    category: "upload",
    actorName: "Taylor Kim",
    actorEmail: "taylor.kim@acme.com",
    actorRole: "Team Admin",
    targetType: "Upload",
    targetName: "june-usage-export.csv",
    description: "Submitted usage upload june-usage-export.csv for import",
    ipAddress: "192.168.2.14",
    createdAt: daysAgo(6, 2),
  },
  {
    id: "audit_8",
    action: "report.generate",
    category: "report",
    actorName: "Morgan Patel",
    actorEmail: "morgan.patel@acme.com",
    actorRole: "Finance Viewer",
    targetType: "Report",
    targetName: "June Usage Summary",
    description: "Generated June Usage Summary PDF report",
    ipAddress: "10.0.1.77",
    createdAt: daysAgo(7, 5),
  },
  {
    id: "audit_9",
    action: "auth.logout",
    category: "auth",
    actorName: "Riley Brooks",
    actorEmail: "riley.brooks@acme.com",
    actorRole: "Auditor",
    targetType: null,
    targetName: null,
    description: "Signed out of the platform",
    ipAddress: "192.168.3.9",
    createdAt: daysAgo(8, 11),
  },
  {
    id: "audit_10",
    action: "user.remove",
    category: "user",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "User",
    targetName: "bob@co.com",
    description: "Removed user bob@co.com from the organization",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(9, 7),
  },
  {
    id: "audit_11",
    action: "team.update",
    category: "team",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "Team",
    targetName: "Data Science",
    description: "Updated Data Science team budget to $250/month",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(10, 4),
  },
  {
    id: "audit_12",
    action: "tool.update",
    category: "tool",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Tool",
    targetName: "Anthropic Dev",
    description: "Updated Anthropic Dev tool configuration",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(11, 9),
  },
  {
    id: "audit_13",
    action: "credential.revoke",
    category: "credential",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "Credential",
    targetName: "Legacy Integration Key",
    description: "Revoked API credential Legacy Integration Key",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(12, 1),
  },
  {
    id: "audit_14",
    action: "alert.update",
    category: "alert",
    actorName: "Sam Rivera",
    actorEmail: "sam.rivera@acme.com",
    actorRole: "Team Admin",
    targetType: "Alert",
    targetName: "Org Token Spike",
    description: "Updated Org Token Spike alert threshold to 12M tokens",
    ipAddress: "172.16.0.55",
    createdAt: daysAgo(13, 6),
  },
  {
    id: "audit_15",
    action: "upload.delete",
    category: "upload",
    actorName: "Taylor Kim",
    actorEmail: "taylor.kim@acme.com",
    actorRole: "Team Admin",
    targetType: "Upload",
    targetName: "corrupted-export.csv",
    description: "Deleted upload corrupted-export.csv before import",
    ipAddress: "192.168.2.14",
    createdAt: daysAgo(14, 3),
  },
  {
    id: "audit_16",
    action: "report.delete",
    category: "report",
    actorName: "Morgan Patel",
    actorEmail: "morgan.patel@acme.com",
    actorRole: "Finance Viewer",
    targetType: "Report",
    targetName: "Weekly Cost Breakdown",
    description: "Deleted Weekly Cost Breakdown report",
    ipAddress: "10.0.1.77",
    createdAt: daysAgo(15, 8),
  },
  {
    id: "audit_17",
    action: "user.role_change",
    category: "user",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "User",
    targetName: "dana.wolfe@acme.com",
    description: "Changed Dana Wolfe role from Team Member to Finance Viewer",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(16, 2),
  },
  {
    id: "audit_18",
    action: "team.delete",
    category: "team",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "Team",
    targetName: "Legacy Ops",
    description: "Deleted team Legacy Ops and unassigned all members",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(17, 10),
  },
  {
    id: "audit_19",
    action: "tool.delete",
    category: "tool",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Tool",
    targetName: "Old Cohere Sandbox",
    description: "Deleted Old Cohere Sandbox integration",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(18, 5),
  },
  {
    id: "audit_20",
    action: "alert.delete",
    category: "alert",
    actorName: "Sam Rivera",
    actorEmail: "sam.rivera@acme.com",
    actorRole: "Team Admin",
    targetType: "Alert",
    targetName: "Design User Overage",
    description: "Deleted alert rule Design User Overage",
    ipAddress: "172.16.0.55",
    createdAt: daysAgo(19, 7),
  },
  {
    id: "audit_21",
    action: "auth.login",
    category: "auth",
    actorName: "Riley Brooks",
    actorEmail: "riley.brooks@acme.com",
    actorRole: "Auditor",
    targetType: null,
    targetName: null,
    description: "Signed in to the platform",
    ipAddress: "192.168.3.9",
    createdAt: daysAgo(20, 4),
  },
  {
    id: "audit_22",
    action: "user.invite",
    category: "user",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "User",
    targetName: "carlos.mendez@acme.com",
    description: "Invited carlos.mendez@acme.com as Team Member",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(21, 6),
  },
  {
    id: "audit_23",
    action: "team.create",
    category: "team",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Team",
    targetName: "Customer Success",
    description: "Created team Customer Success with no budget cap",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(22, 1),
  },
  {
    id: "audit_24",
    action: "tool.connect",
    category: "tool",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "Tool",
    targetName: "Google Gemini Enterprise",
    description: "Connected Google Gemini Enterprise integration",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(23, 9),
  },
  {
    id: "audit_25",
    action: "credential.generate",
    category: "credential",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Credential",
    targetName: "Reporting Service Key",
    description: "Generated org-wide Reporting Service Key credential",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(24, 3),
  },
  {
    id: "audit_26",
    action: "alert.create",
    category: "alert",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Alert",
    targetName: "Monthly Org Cost Cap",
    description: "Created critical cost alert at $5,000 org-wide",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(25, 8),
  },
  {
    id: "audit_27",
    action: "upload.submit",
    category: "upload",
    actorName: "Sam Rivera",
    actorEmail: "sam.rivera@acme.com",
    actorRole: "Team Admin",
    targetType: "Upload",
    targetName: "engineering-usage.json",
    description: "Submitted usage upload engineering-usage.json for import",
    ipAddress: "172.16.0.55",
    createdAt: daysAgo(26, 2),
  },
  {
    id: "audit_28",
    action: "report.generate",
    category: "report",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Report",
    targetName: "Team Comparison Q2",
    description: "Generated Team Comparison Q2 XLSX report",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(27, 5),
  },
  {
    id: "audit_29",
    action: "auth.logout",
    category: "auth",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: null,
    targetName: null,
    description: "Signed out of the platform",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(28, 11),
  },
  {
    id: "audit_30",
    action: "user.remove",
    category: "user",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "User",
    targetName: "temp.contractor@acme.com",
    description: "Removed user temp.contractor@acme.com from the organization",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(29, 7),
  },
  {
    id: "audit_31",
    action: "team.update",
    category: "team",
    actorName: "Sam Rivera",
    actorEmail: "sam.rivera@acme.com",
    actorRole: "Team Admin",
    targetType: "Team",
    targetName: "Engineering",
    description: "Updated Engineering team description and member cap",
    ipAddress: "172.16.0.55",
    createdAt: daysAgo(5, 14),
  },
  {
    id: "audit_32",
    action: "tool.update",
    category: "tool",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "Tool",
    targetName: "OpenAI Production",
    description: "Rotated API key for OpenAI Production tool",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(8, 3),
  },
  {
    id: "audit_33",
    action: "credential.revoke",
    category: "credential",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Credential",
    targetName: "Marketing Read Key",
    description: "Revoked API credential Marketing Read Key",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(11, 12),
  },
  {
    id: "audit_34",
    action: "alert.update",
    category: "alert",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Alert",
    targetName: "Marketing Budget Alert",
    description: "Disabled Marketing Budget Alert rule",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(14, 1),
  },
  {
    id: "audit_35",
    action: "upload.delete",
    category: "upload",
    actorName: "Taylor Kim",
    actorEmail: "taylor.kim@acme.com",
    actorRole: "Team Admin",
    targetType: "Upload",
    targetName: "pending-import.json",
    description: "Discarded upload pending-import.json during preview",
    ipAddress: "192.168.2.14",
    createdAt: daysAgo(2, 8),
  },
  {
    id: "audit_36",
    action: "report.delete",
    category: "report",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Report",
    targetName: "Support Team Activity",
    description: "Deleted Support Team Activity PDF report",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(4, 16),
  },
  {
    id: "audit_37",
    action: "user.role_change",
    category: "user",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "User",
    targetName: "sam.rivera@acme.com",
    description: "Changed Sam Rivera role from Team Member to Team Admin",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(6, 10),
  },
  {
    id: "audit_38",
    action: "team.delete",
    category: "team",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Team",
    targetName: "Pilot Program",
    description: "Deleted team Pilot Program after project completion",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(12, 6),
  },
  {
    id: "audit_39",
    action: "tool.delete",
    category: "tool",
    actorName: "Jordan Lee",
    actorEmail: "jordan.lee@acme.com",
    actorRole: "Super Admin",
    targetType: "Tool",
    targetName: "Mistral Trial",
    description: "Deleted Mistral Trial integration",
    ipAddress: "10.0.0.18",
    createdAt: daysAgo(19, 4),
  },
  {
    id: "audit_40",
    action: "alert.delete",
    category: "alert",
    actorName: "Alan Chen",
    actorEmail: "alan.chen@acme.com",
    actorRole: "Super Admin",
    targetType: "Alert",
    targetName: "Data Science Cost Limit",
    description: "Deleted alert rule Data Science Cost Limit",
    ipAddress: "192.168.1.42",
    createdAt: daysAgo(24, 9),
  },
];

function matchesSearch(entry: AuditLogEntry, search: string): boolean {
  if (!search.trim()) {
    return true;
  }

  const query = search.trim().toLowerCase();
  const fields = [
    entry.actorName,
    entry.actorEmail,
    entry.description,
    entry.targetName ?? "",
  ];

  return fields.some((field) => field.toLowerCase().includes(query));
}

function matchesDateRange(
  createdAt: string,
  from: string,
  to: string,
): boolean {
  const entryDate = parseISO(createdAt);

  if (from) {
    const fromDate = startOfDay(parseISO(from));
    if (entryDate < fromDate) {
      return false;
    }
  }

  if (to) {
    const toDate = endOfDay(parseISO(to));
    if (entryDate > toDate) {
      return false;
    }
  }

  return true;
}

function filterAuditLog(
  entries: AuditLogEntry[],
  filters: AuditLogFilters,
): AuditLogEntry[] {
  return entries.filter((entry) => {
    if (filters.category && entry.category !== filters.category) {
      return false;
    }

    if (!matchesSearch(entry, filters.search)) {
      return false;
    }

    if (!matchesDateRange(entry.createdAt, filters.from, filters.to)) {
      return false;
    }

    return true;
  });
}

export async function fetchAuditLog(
  filters: AuditLogFilters,
): Promise<AuditLogEntry[]> {
  const filtered = filterAuditLog(mockAuditLog, filters);
  return delay(
    filtered.sort(
      (a, b) =>
        parseISO(b.createdAt).getTime() - parseISO(a.createdAt).getTime(),
    ),
  );
}

export const auditLogApi = {
  fetchAuditLog,
};

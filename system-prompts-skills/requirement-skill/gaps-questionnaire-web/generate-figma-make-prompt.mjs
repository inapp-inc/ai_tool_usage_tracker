import { promises as fs } from "node:fs";
import path from "node:path";

const MAX_CHARS = 4950;

function parseArgs(argv) {
  const args = { projectDir: null, out: null, fsd: null, architecture: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--projectDir") args.projectDir = argv[++i];
    else if (a === "--out") args.out = argv[++i];
    else if (a === "--fsd") args.fsd = argv[++i];
    else if (a === "--architecture") args.architecture = argv[++i];
  }
  if (!args.projectDir && !args.out) {
    throw new Error(
      'Usage: node generate-figma-make-prompt.mjs (--projectDir "<projectDir>" | --out "<path>") [--fsd "<FSD.md>"] [--architecture "<architecture.md>"]'
    );
  }
  return args;
}

async function safeRead(p) {
  if (!p) return "";
  try {
    return await fs.readFile(path.resolve(p), "utf-8");
  } catch {
    return "";
  }
}

function compact(s) {
  return String(s ?? "")
    .replace(/\r/g, "")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function takeTopSentences(text, maxChars) {
  const t = compact(text);
  if (!t) return "";
  if (t.length <= maxChars) return t;
  return t.slice(0, maxChars).replace(/\s+\S*$/, "").trim() + "…";
}

function buildPrompt({ projectName, fsdText, archText }) {
  const fsdSnippet = takeTopSentences(fsdText, 1200);
  const archSnippet = takeTopSentences(archText, 900);

  const parts = [];
  parts.push(`You are Figma Make. Create a complete UI for the project "${projectName}".`);
  parts.push("");
  parts.push("## Output expectations");
  parts.push("- Provide high-fidelity UI screens with components, auto-layout, and reusable styles.");
  parts.push("- Use a modern, enterprise SaaS aesthetic: clean, dense-but-readable, accessible.");
  parts.push("- Include empty/loading/error states, validation, and permissions-aware UI where relevant.");
  parts.push("- Make the UI production-oriented: consistent spacing, typographic scale, and tokens.");
  parts.push("");
  parts.push("## Core screens (create all)");
  parts.push("1) Authentication: sign-in, forgot password (if applicable).");
  parts.push("2) Primary dashboard: KPIs + overview cards + key alerts.");
  parts.push("3) Main workspace: list + detail + create/edit flows for core entities.");
  parts.push("4) Settings: org/project settings, user management (if in scope), integrations.");
  parts.push("5) Activity/audit/logs (if applicable) and sync status views.");
  parts.push("");
  parts.push("## UX requirements");
  parts.push("- Global nav with clear IA; breadcrumbs where needed; command palette optional.");
  parts.push("- Tables: sticky header, filtering, sorting, pagination, bulk actions.");
  parts.push("- Forms: inline help, required indicators, field-level errors, confirm destructive actions.");
  parts.push("- Notifications: toast + inline banners; clear retry paths for failures.");
  parts.push("- Accessibility: WCAG AA contrast, keyboard focus states, sensible aria labels.");
  parts.push("");
  parts.push("## Component system (create as a library)");
  parts.push("- Tokens: color (light+dark), type scale, spacing, radius, shadow.");
  parts.push("- Components: buttons, inputs, selects, date pickers, modals, drawers, tabs, badges, tooltips, toasts, data table, cards, charts placeholders, empty states.");
  parts.push("");
  if (fsdSnippet) {
    parts.push("## Features (from spec)");
    parts.push(fsdSnippet);
    parts.push("");
  }
  if (archSnippet) {
    parts.push("## Architecture/integration cues (for UI)");
    parts.push("- Reflect async states for integrations (connect/sync/status/errors/retry).");
    parts.push(archSnippet);
    parts.push("");
  } else {
    parts.push("## Architecture/integration cues (for UI)");
    parts.push("- Reflect async states for integrations (connect/sync/status/errors/retry).");
    parts.push("- Assume API-driven app with role-based access; design for multi-tenant where applicable.");
    parts.push("");
  }
  parts.push("## Deliverables");
  parts.push("- A clickable prototype with happy path + key error paths.");
  parts.push("- A component library page with variants and guidelines.");

  let prompt = compact(parts.join("\n"));
  if (prompt.length <= MAX_CHARS) return prompt;

  // Trim optional sections first.
  const trimmed = compact(
    [
      `You are Figma Make. Create a complete UI for the project "${projectName}".`,
      "",
      "Create high-fidelity enterprise SaaS UI screens + component library.",
      "",
      "Screens: Auth, Dashboard, Core entity list/detail/create-edit, Settings, Sync/Status/Errors.",
      "",
      "UX: tables (filter/sort/paginate), forms (validation/errors), empty/loading/error states, toasts/banners, keyboard focus, WCAG AA.",
      "",
      "Components: tokens, buttons, inputs, modals, drawers, tabs, badges, tooltips, toasts, data table, cards, chart placeholders, empty states.",
      "",
      fsdSnippet ? `Features:\n${fsdSnippet}` : "",
      archSnippet ? `Integration cues:\n${archSnippet}` : "Integration cues: async connect/sync/status/errors/retry; RBAC; multi-tenant.",
      "",
      "Deliverables: clickable prototype + component library page.",
    ].filter(Boolean).join("\n")
  );

  return trimmed.length <= MAX_CHARS ? trimmed : trimmed.slice(0, MAX_CHARS).trimEnd();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const projectDir = args.projectDir ? path.resolve(args.projectDir) : null;
  const projectName = projectDir ? path.basename(projectDir) : "Project";

  const defaultOut = projectDir
    ? path.join(projectDir, "Discovery and Design", "FigmaMake_UI_Prompt.txt")
    : "FigmaMake_UI_Prompt.txt";
  const outPath = path.resolve(args.out ?? defaultOut);

  const fsdGuess = args.fsd ?? (projectDir ? path.join(projectDir, "Docs", "FSD.md") : null);
  const archGuess = args.architecture ?? (projectDir ? path.join(projectDir, "Discovery and Design", "architecture.md") : null);

  const fsdText = await safeRead(fsdGuess);
  const archText = await safeRead(archGuess);

  const prompt = buildPrompt({ projectName, fsdText, archText });
  await fs.mkdir(path.dirname(outPath), { recursive: true });
  await fs.writeFile(outPath, prompt, "utf-8");
  console.log(`Wrote: ${outPath}`);
  console.log(`Chars: ${prompt.length} (limit ${MAX_CHARS})`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


import { promises as fs } from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const args = { in: null, outDir: null, projectDir: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--in") args.in = argv[++i];
    else if (a === "--outDir") args.outDir = argv[++i];
    else if (a === "--projectDir") args.projectDir = argv[++i];
  }
  if (!args.in || (!args.outDir && !args.projectDir)) {
    throw new Error(
      'Usage: node generate-gap-md.mjs --in "<path/to/gap-questionnaire.json>" (--projectDir "<projectDir>" | --outDir "<dir>")'
    );
  }
  return args;
}

function mdEscapePipes(s) {
  return String(s ?? "").replaceAll("|", "\\|").replaceAll("\n", "<br/>");
}

function titleCase(s) {
  return String(s ?? "")
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0]?.toUpperCase() + w.slice(1))
    .join(" ");
}

function buildQuestionnaireMd(data) {
  const lines = [];
  lines.push(`# Gaps Questionnaire: ${data.title ?? "Untitled"}`);
  lines.push("");
  lines.push(
    `**Purpose:** Capture unknowns, assumptions, and gaps between stated needs and current system behavior before writing the Functional Specification Document (FSD). Once filled, this questionnaire is the primary input for FSD creation.`
  );
  lines.push("");
  lines.push(`**Version:** ${data.version ?? "1.0"}  `);
  lines.push(`**Date:** ${data.date ?? ""}  `);
  lines.push(`**Status:** ${data.status ?? "Draft"}`);
  if (Array.isArray(data.sourceDocs) && data.sourceDocs.length) {
    lines.push(`**Source docs:** ${data.sourceDocs.map((d) => `\`${d}\``).join(", ")}`);
  }
  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push("## How to use");
  lines.push("");
  lines.push("1. Fill **Answer / Owner / Confidence** for each row.");
  lines.push(
    '2. Any item left at **Confidence = L** is treated as a **blocked spec** for the impacted epic/slice.'
  );
  lines.push(
    "3. When answered, translate each item into either an FSD requirement/acceptance criterion, or an explicit assumption/constraint in the FSD."
  );
  lines.push("");

  const sections = Array.isArray(data.sections) ? data.sections : [];
  let sectionNumber = 1;
  for (const section of sections) {
    const isDecisions = !!section.isDecisions;
    lines.push("---");
    lines.push("");
    lines.push(`## ${sectionNumber}. ${section.title ?? titleCase(section.id ?? "Section")}`);
    lines.push("");

    if (isDecisions) {
      lines.push("| ID | Decision needed | Options | Owner | Due |");
      lines.push("|----|-----------------|---------|-------|-----|");
      for (const row of section.rows ?? []) {
        lines.push(
          `| ${mdEscapePipes(row.id)} | ${mdEscapePipes(row.decision)} | ${mdEscapePipes(
            row.options
          )} | ${mdEscapePipes(row.owner)} | ${mdEscapePipes(row.due)} |`
        );
      }
    } else {
      lines.push("| ID | Question / Gap | Answer | Owner | Confidence (H/M/L) |");
      lines.push("|----|----------------|--------|-------|--------------------|");
      for (const row of section.rows ?? []) {
        lines.push(
          `| ${mdEscapePipes(row.id)} | ${mdEscapePipes(row.question)} | ${mdEscapePipes(
            row.answer
          )} | ${mdEscapePipes(row.owner)} | ${mdEscapePipes(row.confidence)} |`
        );
      }
      lines.push("");
      lines.push("*Add rows as needed. Confidence: H = decided/verified, M = assumed, L = unknown.*");
    }

    lines.push("");
    sectionNumber++;
  }

  lines.push("---");
  lines.push("");
  lines.push("## Traceability to FSD");
  lines.push("");
  lines.push("After FSD creation, optionally link questionnaire items to FSD sections:");
  lines.push("");
  lines.push("| Questionnaire ID | FSD section / requirement |");
  lines.push("|------------------|---------------------------|");
  lines.push("| F1, F2 | Section 5, Epic 1 |");
  lines.push("| D1 | Section 7, Data model |");
  lines.push("| I1, I2 | Section 7, Integration points; OpenAPI spec |");
  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push("*Keep this document updated when answers change so the FSD and implementation stay aligned.*");
  lines.push("");
  return lines.join("\n");
}

function buildAnswersOnlyMd(data) {
  const lines = [];
  lines.push(`# Gaps Answers: ${data.title ?? "Untitled"}`);
  lines.push("");
  lines.push(`**Version:** ${data.version ?? "1.0"}  `);
  lines.push(`**Date:** ${data.date ?? ""}  `);
  lines.push(`**Status:** ${data.status ?? "Draft"}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  const sections = Array.isArray(data.sections) ? data.sections : [];
  for (const section of sections) {
    const isDecisions = !!section.isDecisions;
    lines.push(`## ${section.title ?? titleCase(section.id ?? "Section")}`);
    lines.push("");

    const rows = Array.isArray(section.rows) ? section.rows : [];
    if (!rows.length) {
      lines.push("_No entries._");
      lines.push("");
      continue;
    }

    for (const row of rows) {
      const id = String(row.id ?? "").trim() || "(no id)";
      if (isDecisions) {
        lines.push(`### ${id} — ${row.decision ?? ""}`.trim());
        if (row.options) lines.push(`- **Options**: ${row.options}`);
        if (row.owner) lines.push(`- **Owner**: ${row.owner}`);
        if (row.due) lines.push(`- **Due**: ${row.due}`);
      } else {
        lines.push(`### ${id} — ${row.question ?? ""}`.trim());
        lines.push(`- **Answer**: ${row.answer ?? ""}`);
        if (row.owner) lines.push(`- **Owner**: ${row.owner}`);
        if (row.confidence) lines.push(`- **Confidence**: ${row.confidence}`);
      }
      lines.push("");
    }
  }

  return lines.join("\n");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const inPath = path.resolve(args.in);
  const outDir = path.resolve(args.outDir ?? path.join(args.projectDir, "Docs"));

  const raw = await fs.readFile(inPath, "utf-8");
  const data = JSON.parse(raw);

  await fs.mkdir(outDir, { recursive: true });

  const qPath = path.join(outDir, "SDD_Gaps_Questionnaire.md");
  const aPath = path.join(outDir, "SDD_Gaps_Answers.md");

  await fs.writeFile(qPath, buildQuestionnaireMd(data), "utf-8");
  await fs.writeFile(aPath, buildAnswersOnlyMd(data), "utf-8");

  console.log(`Wrote: ${qPath}`);
  console.log(`Wrote: ${aPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


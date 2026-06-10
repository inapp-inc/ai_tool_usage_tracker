import { promises as fs } from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const args = { in: null, projectDir: null, out: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--in") args.in = argv[++i];
    else if (a === "--projectDir") args.projectDir = argv[++i];
    else if (a === "--out") args.out = argv[++i];
  }
  if (!args.in || (!args.projectDir && !args.out)) {
    throw new Error(
      'Usage: node generate-assumptions-md.mjs --in "<path/to/gap-questionnaire.json>" (--projectDir "<projectDir>" | --out "<path/to/SDD_Assumptions.md>")'
    );
  }
  return args;
}

function isBlank(s) {
  return !String(s ?? "").trim();
}

function mdEscape(s) {
  return String(s ?? "").replaceAll("\n", "\n  ");
}

function collectUnresolved(data) {
  const items = [];
  const sections = Array.isArray(data.sections) ? data.sections : [];

  for (const section of sections) {
    const isDecisions = !!section.isDecisions;
    const rows = Array.isArray(section.rows) ? section.rows : [];
    for (const row of rows) {
      const id = String(row.id ?? "").trim();
      if (!id) continue;

      if (isDecisions) {
        if (isBlank(row.decision)) continue;
        // Open decisions are unresolved by definition unless explicitly handled elsewhere.
        items.push({
          id,
          type: "decision",
          prompt: row.decision,
          current: isBlank(row.options) ? "" : `Options: ${row.options}`,
          owner: String(row.owner ?? "").trim(),
          confidence: "",
        });
        continue;
      }

      const question = String(row.question ?? "").trim();
      const answer = String(row.answer ?? "").trim();
      const confidence = String(row.confidence ?? "").trim();
      const owner = String(row.owner ?? "").trim();

      // "Not properly addressed" heuristic:
      // - missing answer, OR
      // - confidence is L (unknown)
      if (isBlank(question)) continue;
      if (isBlank(answer) || confidence === "L") {
        items.push({
          id,
          type: "gap",
          prompt: question,
          current: answer,
          owner,
          confidence,
        });
      }
    }
  }

  return items;
}

function buildAssumptionsMd(data) {
  const title = data.title ?? "Untitled";
  const version = data.version ?? "1.0";
  const date = data.date ?? "";
  const status = data.status ?? "Draft";

  const items = collectUnresolved(data);

  const lines = [];
  lines.push(`# Assumptions & Gap Handling: ${title}`);
  lines.push("");
  lines.push(`**Source:** \`Discovery and Design/gap-questionnaire.json\``);
  lines.push(`**Gaps version:** ${version}  `);
  lines.push(`**Date:** ${date}  `);
  lines.push(`**Gaps status:** ${status}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  if (!items.length) {
    lines.push("## Summary");
    lines.push("");
    lines.push("No unresolved gaps detected (all questions answered and no items at confidence L).");
    lines.push("");
    return lines.join("\n");
  }

  lines.push("## Summary");
  lines.push("");
  lines.push(
    `The following items were **not fully addressed** in the gaps questionnaire (missing answer and/or confidence L, plus open decisions). They are handled as explicit assumptions so the SDD process can remain traceable.`
  );
  lines.push("");

  lines.push("## Unresolved items → handling");
  lines.push("");
  lines.push(
    "For each item below, choose one handling approach and keep it consistent with the FSD and implementation plan:"
  );
  lines.push("");
  lines.push("- **Assume & proceed**: state the assumption clearly; implement to that assumption; revisit later.");
  lines.push("- **Defer**: mark out of scope for current phase; add to backlog.");
  lines.push("- **Block**: stop downstream work until resolved (recommended for high-risk unknowns).");
  lines.push("");

  for (const item of items) {
    lines.push(`### ${item.id}`);
    lines.push(`- **Type**: ${item.type}`);
    lines.push(`- **Item**: ${mdEscape(item.prompt)}`);
    if (!isBlank(item.current)) lines.push(`- **Current answer/options**: ${mdEscape(item.current)}`);
    if (!isBlank(item.owner)) lines.push(`- **Owner**: ${mdEscape(item.owner)}`);
    if (!isBlank(item.confidence)) lines.push(`- **Confidence**: ${mdEscape(item.confidence)}`);
    lines.push("- **Handling**: _[Assume & proceed | Defer | Block]_");
    lines.push("- **Assumption statement**: _[what we will assume]_");
    lines.push("- **Impact**: _[what could change if assumption is wrong]_");
    lines.push("- **Follow-up**: _[who + when + how to validate]_");
    lines.push("");
  }

  return lines.join("\n");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const inPath = path.resolve(args.in);
  const outPath = path.resolve(args.out ?? path.join(args.projectDir, "Docs", "SDD_Assumptions.md"));

  const raw = await fs.readFile(inPath, "utf-8");
  const data = JSON.parse(raw);

  await fs.mkdir(path.dirname(outPath), { recursive: true });
  await fs.writeFile(outPath, buildAssumptionsMd(data), "utf-8");
  console.log(`Wrote: ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


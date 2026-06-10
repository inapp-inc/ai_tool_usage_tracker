import { promises as fs } from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const args = { projectDir: null, out: null, title: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--projectDir") args.projectDir = argv[++i];
    else if (a === "--out") args.out = argv[++i];
    else if (a === "--title") args.title = argv[++i];
  }
  if (!args.projectDir && !args.out) {
    throw new Error('Usage: node init-gap-json.mjs --projectDir "<dir>" [--out "<path/to/gap-questionnaire.json>"] [--title "..."]');
  }
  return args;
}

function defaultQuestionnaire(title) {
  return {
    title: title || "Gaps Questionnaire",
    version: "1.0",
    date: new Date().toISOString().slice(0, 10),
    status: "Draft",
    sourceDocs: [],
    sections: [
      {
        id: "functional",
        title: "Functional gaps",
        prefix: "F",
        rows: [
          {
            id: "F1",
            question: "Which user roles must be supported in v1?",
            answer: "",
            owner: "",
            confidence: "",
          },
        ],
      },
      { id: "data", title: "Data and domain gaps", prefix: "D", rows: [] },
      { id: "integration", title: "Integration and API gaps", prefix: "I", rows: [] },
      { id: "nonfunctional", title: "Non-functional and constraints", prefix: "N", rows: [] },
      { id: "scope", title: "Scope and out-of-scope", prefix: "S", rows: [] },
      { id: "decisions", title: "Open decisions", prefix: "O", isDecisions: true, rows: [] },
    ],
  };
}

async function exists(p) {
  try {
    await fs.stat(p);
    return true;
  } catch {
    return false;
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const projectDir = args.projectDir ? path.resolve(args.projectDir) : null;
  const defaultOut =
    projectDir ? path.join(projectDir, "Discovery and Design", "gap-questionnaire.json") : "gap-questionnaire.json";
  const outPath = path.resolve(args.out ?? defaultOut);

  if (await exists(outPath)) {
    console.log(`Exists (no-op): ${outPath}`);
    return;
  }

  await fs.mkdir(path.dirname(outPath), { recursive: true });
  const title = args.title ?? (projectDir ? `Gaps Questionnaire: ${path.basename(projectDir)}` : "Gaps Questionnaire");
  await fs.writeFile(outPath, JSON.stringify(defaultQuestionnaire(title), null, 2) + "\n", "utf-8");
  console.log(`Created: ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


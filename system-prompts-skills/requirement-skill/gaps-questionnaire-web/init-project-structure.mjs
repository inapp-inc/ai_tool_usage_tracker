import { promises as fs } from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const args = { projectDir: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--projectDir") args.projectDir = argv[++i];
  }
  if (!args.projectDir) {
    throw new Error('Usage: node init-project-structure.mjs --projectDir "<dir>"');
  }
  return args;
}

async function ensureDir(p) {
  await fs.mkdir(p, { recursive: true });
}

async function ensureGitkeep(dir) {
  const p = path.join(dir, ".gitkeep");
  try {
    await fs.stat(p);
  } catch {
    await fs.writeFile(p, "", "utf-8");
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const projectDir = path.resolve(args.projectDir);

  const discovery = path.join(projectDir, "Discovery and Design");
  const docs = path.join(projectDir, "Docs");
  const codebase = path.join(projectDir, "codebase");

  await ensureDir(discovery);
  await ensureDir(docs);
  await ensureDir(codebase);

  await ensureGitkeep(discovery);
  await ensureGitkeep(docs);
  await ensureGitkeep(codebase);

  console.log(`Ensured: ${discovery}`);
  console.log(`Ensured: ${docs}`);
  console.log(`Ensured: ${codebase}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


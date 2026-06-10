import http from "node:http";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT ?? 4317);
const WORKSPACE_ROOT = process.env.WORKSPACE_ROOT
  ? path.resolve(process.env.WORKSPACE_ROOT)
  : path.resolve(__dirname, "..", "..", "..");

const REGISTRY_PATH = path.join(__dirname, "registry.json");

const DEFAULT_PROJECT = {
  name: "default",
  jsonPath: "system-prompts-skills/requirement-skill/gaps-questionnaire-web/gap-questionnaire.json",
};

const CONTENT_TYPES = new Map([
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".css", "text/css; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".svg", "image/svg+xml"],
  [".png", "image/png"],
]);

function sendJson(res, statusCode, body) {
  const payload = JSON.stringify(body, null, 2);
  res.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  res.end(payload);
}

function defaultQuestionnaire() {
  return {
    title: "Gaps Questionnaire",
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
      {
        id: "data",
        title: "Data and domain gaps",
        prefix: "D",
        rows: [],
      },
      {
        id: "integration",
        title: "Integration and API gaps",
        prefix: "I",
        rows: [],
      },
      {
        id: "nonfunctional",
        title: "Non-functional and constraints",
        prefix: "N",
        rows: [],
      },
      {
        id: "scope",
        title: "Scope and out-of-scope",
        prefix: "S",
        rows: [],
      },
      {
        id: "decisions",
        title: "Open decisions",
        prefix: "O",
        rows: [],
        isDecisions: true,
      },
    ],
  };
}

async function readRegistry() {
  try {
    const raw = await fs.readFile(REGISTRY_PATH, "utf-8");
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed.projects)) parsed.projects = [];
    return parsed;
  } catch (err) {
    if (err && err.code === "ENOENT") {
      return { version: "1.0", updatedAt: "", projects: [] };
    }
    throw err;
  }
}

async function writeRegistry(registry) {
  registry.updatedAt = new Date().toISOString();
  await fs.writeFile(REGISTRY_PATH, JSON.stringify(registry, null, 2) + "\n", "utf-8");
}

function resolveProjectPath(jsonPath) {
  const abs = path.isAbsolute(jsonPath) ? jsonPath : path.resolve(WORKSPACE_ROOT, jsonPath);
  const normRoot = WORKSPACE_ROOT.endsWith(path.sep) ? WORKSPACE_ROOT : WORKSPACE_ROOT + path.sep;
  if (!abs.startsWith(normRoot)) {
    throw new Error(`Project jsonPath must be inside workspace root (${WORKSPACE_ROOT})`);
  }
  return abs;
}

function resolveWorkspaceFile(filePath) {
  const abs = path.isAbsolute(filePath) ? filePath : path.resolve(WORKSPACE_ROOT, filePath);
  const normRoot = WORKSPACE_ROOT.endsWith(path.sep) ? WORKSPACE_ROOT : WORKSPACE_ROOT + path.sep;
  if (!abs.startsWith(normRoot)) {
    throw new Error(`Path must be inside workspace root (${WORKSPACE_ROOT})`);
  }
  return abs;
}

async function ensureRegistered({ name, jsonPath }) {
  const registry = await readRegistry();
  const existing = registry.projects.find((p) => p.name === name);
  const now = new Date().toISOString();

  if (existing) {
    existing.jsonPath = jsonPath;
    existing.lastRegisteredAt = now;
  } else {
    registry.projects.push({
      name,
      jsonPath,
      createdAt: now,
      lastRegisteredAt: now,
      artifacts: {},
    });
  }

  await writeRegistry(registry);
  return registry;
}

async function upsertArtifacts({ name, jsonPath, questionnaireMdPath, answersMdPath }) {
  const registry = await ensureRegistered({ name, jsonPath });
  const project = registry.projects.find((p) => p.name === name);
  if (!project) return registry;

  project.artifacts = project.artifacts && typeof project.artifacts === "object" ? project.artifacts : {};
  project.artifacts.questionnaireMdPath = questionnaireMdPath || project.artifacts.questionnaireMdPath || "";
  project.artifacts.answersMdPath = answersMdPath || project.artifacts.answersMdPath || "";
  project.artifacts.lastArtifactRegisteredAt = new Date().toISOString();

  await writeRegistry(registry);
  return registry;
}

function inferProjectNameFromJsonPath(jsonPath) {
  const norm = jsonPath.replaceAll("\\", "/");
  const parts = norm.split("/").filter(Boolean);
  // Preferred layout:
  // <projectDir>/Discovery and Design/gap-questionnaire.json -> project = <projectDir name>
  if (parts.length >= 3 && parts[parts.length - 2] === "Discovery and Design") {
    return parts[parts.length - 3];
  }

  // Legacy layout:
  // Foo/bar/gap-questionnaire.json -> project = "bar"
  if (parts.length >= 2) return parts[parts.length - 2];
  return parts[0] || "default";
}

async function readProjectJsonOrDefault(absPath) {
  try {
    const raw = await fs.readFile(absPath, "utf-8");
    return JSON.parse(raw);
  } catch (err) {
    if (err && (err.code === "ENOENT" || err.code === "ENOTDIR")) {
      return defaultQuestionnaire();
    }
    throw err;
  }
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf-8");
}

function safeJoin(root, requestPath) {
  const resolved = path.resolve(root, "." + requestPath);
  if (!resolved.startsWith(root)) return null;
  return resolved;
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);
    const pathname = url.pathname;

    // API
    if (pathname === "/api/registry" && req.method === "GET") {
      const registry = await readRegistry();
      return sendJson(res, 200, { ok: true, registryPath: REGISTRY_PATH, registry });
    }

    if (pathname === "/api/register" && req.method === "POST") {
      const body = await readBody(req);
      let parsed;
      try {
        parsed = JSON.parse(body);
      } catch {
        return sendJson(res, 400, { ok: false, error: "Invalid JSON" });
      }
      const name = String(parsed?.name ?? "").trim();
      const jsonPath = String(parsed?.jsonPath ?? "").trim();
      if (!name) return sendJson(res, 400, { ok: false, error: "Missing name" });
      if (!jsonPath) return sendJson(res, 400, { ok: false, error: "Missing jsonPath" });

      // Validate path (must be within workspace)
      resolveProjectPath(jsonPath);
      const registry = await ensureRegistered({ name, jsonPath });
      return sendJson(res, 200, { ok: true, registry });
    }

    // Register a project by jsonPath, inferring name from containing folder.
    // Body: { jsonPath }
    if (pathname === "/api/register-from-path" && req.method === "POST") {
      const body = await readBody(req);
      let parsed;
      try {
        parsed = JSON.parse(body);
      } catch {
        return sendJson(res, 400, { ok: false, error: "Invalid JSON" });
      }

      const jsonPath = String(parsed?.jsonPath ?? "").trim();
      if (!jsonPath) return sendJson(res, 400, { ok: false, error: "Missing jsonPath" });

      resolveProjectPath(jsonPath);
      const name = inferProjectNameFromJsonPath(jsonPath);
      const registry = await ensureRegistered({ name, jsonPath });
      return sendJson(res, 200, { ok: true, name, registry });
    }

    // Register a generated Markdown artifact (auto-registration use case)
    // Body: { name, jsonPath, questionnaireMdPath, answersMdPath? }
    if (pathname === "/api/register-artifact" && req.method === "POST") {
      const body = await readBody(req);
      let parsed;
      try {
        parsed = JSON.parse(body);
      } catch {
        return sendJson(res, 400, { ok: false, error: "Invalid JSON" });
      }

      const name = String(parsed?.name ?? "").trim();
      const jsonPath = String(parsed?.jsonPath ?? "").trim();
      const questionnaireMdPath = String(parsed?.questionnaireMdPath ?? "").trim();
      const answersMdPath = String(parsed?.answersMdPath ?? "").trim();

      if (!name) return sendJson(res, 400, { ok: false, error: "Missing name" });
      if (!jsonPath) return sendJson(res, 400, { ok: false, error: "Missing jsonPath" });
      if (!questionnaireMdPath) return sendJson(res, 400, { ok: false, error: "Missing questionnaireMdPath" });

      resolveProjectPath(jsonPath);
      resolveWorkspaceFile(questionnaireMdPath);
      if (answersMdPath) resolveWorkspaceFile(answersMdPath);

      const registry = await upsertArtifacts({ name, jsonPath, questionnaireMdPath, answersMdPath });
      return sendJson(res, 200, { ok: true, registry });
    }

    if (pathname === "/api/project/load" && req.method === "GET") {
      const name = String(url.searchParams.get("name") ?? "").trim();
      if (!name) return sendJson(res, 400, { ok: false, error: "Missing name" });

      const registry = await readRegistry();
      const project =
        registry.projects.find((p) => p.name === name) ??
        (name === DEFAULT_PROJECT.name ? DEFAULT_PROJECT : null);
      if (!project) return sendJson(res, 404, { ok: false, error: "Project not registered" });

      // Auto-register each time the portal accesses a project
      await ensureRegistered({ name: project.name, jsonPath: project.jsonPath });

      const abs = resolveProjectPath(project.jsonPath);
      const data = await readProjectJsonOrDefault(abs);
      return sendJson(res, 200, {
        ok: true,
        project: { name: project.name, jsonPath: project.jsonPath, absPath: abs },
        data,
      });
    }

    if (pathname === "/api/project/save" && req.method === "POST") {
      const body = await readBody(req);
      let parsed;
      try {
        parsed = JSON.parse(body);
      } catch {
        return sendJson(res, 400, { ok: false, error: "Invalid JSON" });
      }

      const name = String(parsed?.name ?? "").trim();
      const jsonPath = String(parsed?.jsonPath ?? "").trim();
      const data = parsed?.data;
      if (!name) return sendJson(res, 400, { ok: false, error: "Missing name" });
      if (!jsonPath) return sendJson(res, 400, { ok: false, error: "Missing jsonPath" });
      if (!data || typeof data !== "object") return sendJson(res, 400, { ok: false, error: "Missing data" });

      const abs = resolveProjectPath(jsonPath);
      await fs.mkdir(path.dirname(abs), { recursive: true });
      await fs.writeFile(abs, JSON.stringify(data, null, 2) + "\n", "utf-8");

      // Register/update every save
      await ensureRegistered({ name, jsonPath });

      return sendJson(res, 200, { ok: true, project: { name, jsonPath, absPath: abs } });
    }

    if (pathname === "/api/project/finalize" && req.method === "POST") {
      const body = await readBody(req);
      let parsed;
      try {
        parsed = JSON.parse(body);
      } catch {
        return sendJson(res, 400, { ok: false, error: "Invalid JSON" });
      }

      const name = String(parsed?.name ?? "").trim();
      if (!name) return sendJson(res, 400, { ok: false, error: "Missing name" });

      const registry = await readRegistry();
      const project =
        registry.projects.find((p) => p.name === name) ??
        (name === DEFAULT_PROJECT.name ? DEFAULT_PROJECT : null);
      if (!project) return sendJson(res, 404, { ok: false, error: "Project not registered" });

      const abs = resolveProjectPath(project.jsonPath);
      const data = await readProjectJsonOrDefault(abs);
      data.status = "Complete";
      data.date = data.date || new Date().toISOString().slice(0, 10);
      await fs.mkdir(path.dirname(abs), { recursive: true });
      await fs.writeFile(abs, JSON.stringify(data, null, 2) + "\n", "utf-8");

      await ensureRegistered({ name: project.name, jsonPath: project.jsonPath });

      return sendJson(res, 200, { ok: true, project: { name: project.name, jsonPath: project.jsonPath, absPath: abs }, data });
    }

    // Back-compat (single project endpoints)
    if (pathname === "/api/load" && req.method === "GET") {
      const abs = resolveProjectPath(DEFAULT_PROJECT.jsonPath);
      const json = await readProjectJsonOrDefault(abs);
      await ensureRegistered(DEFAULT_PROJECT);
      return sendJson(res, 200, { ok: true, dataPath: abs, data: json });
    }

    if (pathname === "/api/save" && req.method === "POST") {
      const body = await readBody(req);
      let parsed;
      try {
        parsed = JSON.parse(body);
      } catch {
        return sendJson(res, 400, { ok: false, error: "Invalid JSON" });
      }
      const abs = resolveProjectPath(DEFAULT_PROJECT.jsonPath);
      await fs.mkdir(path.dirname(abs), { recursive: true });
      await fs.writeFile(abs, JSON.stringify(parsed, null, 2) + "\n", "utf-8");
      await ensureRegistered(DEFAULT_PROJECT);
      return sendJson(res, 200, { ok: true, dataPath: abs });
    }

    // Static
    let filePath = pathname === "/" ? "/index.html" : pathname;
    const resolved = safeJoin(__dirname, filePath);
    if (!resolved) {
      res.writeHead(403, { "content-type": "text/plain; charset=utf-8" });
      return res.end("Forbidden");
    }

    try {
      const ext = path.extname(resolved);
      const contentType = CONTENT_TYPES.get(ext) ?? "application/octet-stream";
      const content = await fs.readFile(resolved);
      res.writeHead(200, {
        "content-type": contentType,
        "cache-control": "no-store",
      });
      return res.end(content);
    } catch (err) {
      if (err && err.code === "ENOENT") {
        res.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
        return res.end("Not found");
      }
      throw err;
    }
  } catch (err) {
    res.writeHead(500, { "content-type": "application/json; charset=utf-8" });
    res.end(JSON.stringify({ ok: false, error: err?.message ?? String(err) }));
  }
});

server.listen(PORT, () => {
  // Intentionally minimal output (avoid noisy logs).
  console.log(`Gap manager portal: http://localhost:${PORT}`);
  console.log(`Registry: ${REGISTRY_PATH}`);
  console.log(`Workspace root: ${WORKSPACE_ROOT}`);
});


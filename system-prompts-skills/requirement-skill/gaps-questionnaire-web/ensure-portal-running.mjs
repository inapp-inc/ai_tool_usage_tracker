import { spawn, execFileSync } from "node:child_process";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = Number(process.env.PORT ?? 4317);

function httpGetJson(url, timeoutMs = 800) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => {
        const raw = Buffer.concat(chunks).toString("utf-8");
        try {
          resolve({ statusCode: res.statusCode ?? 0, json: JSON.parse(raw) });
        } catch (e) {
          reject(new Error(`Non-JSON response (${res.statusCode}): ${raw.slice(0, 200)}`));
        }
      });
    });
    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error("timeout"));
    });
    req.on("error", reject);
  });
}

async function isPortalRunning() {
  try {
    const { statusCode, json } = await httpGetJson(`http://localhost:${PORT}/api/registry`);
    return (
      statusCode === 200 &&
      json &&
      json.ok === true &&
      typeof json.registryPath === "string" &&
      json.registry &&
      typeof json.registry === "object"
    );
  } catch {
    return false;
  }
}

function pidsListeningOnPort() {
  try {
    const out = execFileSync("lsof", ["-nP", `-iTCP:${PORT}`, "-sTCP:LISTEN", "-t"], {
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    });
    return out
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => Number(s))
      .filter((n) => Number.isFinite(n));
  } catch {
    return [];
  }
}

function killPids(pids) {
  for (const pid of pids) {
    try {
      process.kill(pid, "SIGTERM");
    } catch {}
  }
}

function startPortal() {
  const serverPath = path.join(__dirname, "server.mjs");
  const child = spawn(process.execPath, [serverPath], {
    env: { ...process.env, PORT: String(PORT) },
    detached: true,
    stdio: "ignore",
  });
  child.unref();
}

async function main() {
  if (await isPortalRunning()) {
    console.log(`Portal already running on ${PORT} (no-op).`);
    return;
  }

  const pids = pidsListeningOnPort();
  if (pids.length) {
    killPids(pids);
    // small grace period
    await new Promise((r) => setTimeout(r, 250));
  }

  startPortal();

  // Wait briefly for readiness
  const deadline = Date.now() + 3000;
  while (Date.now() < deadline) {
    if (await isPortalRunning()) {
      console.log(`Portal started on ${PORT}.`);
      return;
    }
    await new Promise((r) => setTimeout(r, 150));
  }

  console.log(`Started portal process, but readiness check timed out on ${PORT}.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


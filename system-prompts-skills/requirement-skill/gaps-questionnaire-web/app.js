const $ = (id) => document.getElementById(id);

const els = {
  title: $("title"),
  projectSelect: $("projectSelect"),
  version: $("version"),
  date: $("date"),
  status: $("status"),
  sections: $("sections"),
  sourceDocs: $("sourceDocs"),
  addSourceDocBtn: $("addSourceDocBtn"),
  reloadBtn: $("reloadBtn"),
  saveBtn: $("saveBtn"),
  registryHint: $("registryHint"),
  toast: $("toast"),
};

let state = null;
let project = { name: "default", jsonPath: "system-prompts-skills/requirement-skill/gaps-questionnaire-web/gap-questionnaire.json" };
let registry = null;
let registryPath = null;
let dirty = false;

function toast(msg, kind = "info") {
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const label = kind === "error" ? "Error" : "Saved";
  els.toast.innerHTML = `<strong>${label}</strong> · ${msg} <span class="mono">(${now})</span>`;
}

function markDirty(next = true) {
  dirty = next;
  els.saveBtn.textContent = dirty ? "Save JSON (unsaved changes)" : "Save JSON";
}

function setTitle() {
  const name = project?.name ?? "default";
  els.title.textContent = `Gap questionnaire — ${name}`;
}

function normalizeRow(row) {
  return {
    id: row?.id ?? "",
    question: row?.question ?? "",
    answer: row?.answer ?? "",
    owner: row?.owner ?? "",
    confidence: row?.confidence ?? "",
    options: row?.options ?? "",
    due: row?.due ?? "",
  };
}

function renderSourceDocs() {
  els.sourceDocs.innerHTML = "";
  const docs = Array.isArray(state.sourceDocs) ? state.sourceDocs : [];
  for (const [idx, doc] of docs.entries()) {
    const chip = document.createElement("div");
    chip.className = "chip";
    chip.innerHTML = `
      <span class="mono">${escapeHtml(doc)}</span>
      <span class="x" title="Remove">×</span>
    `;
    chip.querySelector(".x").addEventListener("click", () => {
      state.sourceDocs.splice(idx, 1);
      renderSourceDocs();
      markDirty(true);
    });
    els.sourceDocs.appendChild(chip);
  }
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function render() {
  if (!state) return;

  document.body.classList.toggle("statusComplete", state.status === "Complete");

  setTitle();
  els.version.value = state.version ?? "";
  els.date.value = state.date ?? "";
  els.status.value = state.status ?? "Draft";

  renderSourceDocs();
  renderSections();
  markDirty(false);
}

function renderSections() {
  els.sections.innerHTML = "";

  for (const section of state.sections ?? []) {
    const wrapper = document.createElement("section");
    wrapper.className = "section";

    const left = document.createElement("div");
    left.className = "left";
    left.innerHTML = `
      <h2>${escapeHtml(section.title ?? "")}</h2>
      <span class="badge mono">${escapeHtml(section.prefix ?? "")}</span>
    `;

    const head = document.createElement("div");
    head.className = "sectionHead";
    head.appendChild(left);

    const btns = document.createElement("div");
    btns.className = "row";
    btns.style.justifyContent = "flex-end";
    btns.style.gap = "10px";

    const addBtn = document.createElement("button");
    addBtn.className = "secondary small";
    addBtn.textContent = "Add row";
    addBtn.addEventListener("click", () => {
      const nextId = suggestNextId(section);
      section.rows = Array.isArray(section.rows) ? section.rows : [];
      section.rows.push(
        section.isDecisions
          ? { id: nextId, decision: "", options: "", owner: "", due: "" }
          : { id: nextId, question: "", answer: "", owner: "", confidence: "" }
      );
      renderSections();
      markDirty(true);
    });

    btns.appendChild(addBtn);
    head.appendChild(btns);
    wrapper.appendChild(head);

    wrapper.appendChild(renderTable(section));
    els.sections.appendChild(wrapper);
  }
}

function suggestNextId(section) {
  const prefix = section.prefix ?? "X";
  const rows = Array.isArray(section.rows) ? section.rows : [];
  const nums = rows
    .map((r) => String(r.id ?? ""))
    .filter((id) => id.startsWith(prefix))
    .map((id) => Number(id.slice(prefix.length)))
    .filter((n) => Number.isFinite(n));
  const next = (nums.length ? Math.max(...nums) : 0) + 1;
  return `${prefix}${next}`;
}

function renderTable(section) {
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const tbody = document.createElement("tbody");
  const rows = (section.rows ?? []).map(normalizeRow);

  const isDecisions = !!section.isDecisions;

  thead.innerHTML = isDecisions
    ? `
      <tr>
        <th class="idCell">ID</th>
        <th>Decision needed</th>
        <th>Options</th>
        <th class="ownerCell">Owner</th>
        <th class="confCell">Due</th>
        <th class="ctlCell"></th>
      </tr>
    `
    : `
      <tr>
        <th class="idCell">ID</th>
        <th>Question / Gap</th>
        <th>Answer</th>
        <th class="ownerCell">Owner</th>
        <th class="confCell">Confidence</th>
        <th class="ctlCell"></th>
      </tr>
    `;

  for (const [idx, row] of rows.entries()) {
    const tr = document.createElement("tr");

    const idTd = document.createElement("td");
    idTd.className = "idCell mono";
    idTd.innerHTML = `<input value="${escapeHtml(row.id)}" />`;
    idTd.querySelector("input").addEventListener("input", (e) => {
      section.rows[idx].id = e.target.value;
      markDirty(true);
    });

    const qTd = document.createElement("td");
    qTd.innerHTML = `<textarea>${escapeHtml(isDecisions ? section.rows[idx].decision ?? "" : row.question)}</textarea>`;
    qTd.querySelector("textarea").addEventListener("input", (e) => {
      if (isDecisions) section.rows[idx].decision = e.target.value;
      else section.rows[idx].question = e.target.value;
      markDirty(true);
    });

    const aTd = document.createElement("td");
    aTd.innerHTML = `<textarea>${escapeHtml(isDecisions ? section.rows[idx].options ?? "" : row.answer)}</textarea>`;
    aTd.querySelector("textarea").addEventListener("input", (e) => {
      if (isDecisions) section.rows[idx].options = e.target.value;
      else section.rows[idx].answer = e.target.value;
      markDirty(true);
    });

    const ownerTd = document.createElement("td");
    ownerTd.className = "ownerCell";
    ownerTd.innerHTML = `<input value="${escapeHtml(row.owner)}" />`;
    ownerTd.querySelector("input").addEventListener("input", (e) => {
      section.rows[idx].owner = e.target.value;
      markDirty(true);
    });

    const confTd = document.createElement("td");
    confTd.className = "confCell";
    if (isDecisions) {
      confTd.innerHTML = `<input value="${escapeHtml(row.due ?? "")}" placeholder="YYYY-MM-DD or milestone" />`;
      confTd.querySelector("input").addEventListener("input", (e) => {
        section.rows[idx].due = e.target.value;
        markDirty(true);
      });
    } else {
      confTd.innerHTML = `
        <select>
          <option value=""></option>
          <option value="H">H</option>
          <option value="M">M</option>
          <option value="L">L</option>
        </select>
      `;
      const select = confTd.querySelector("select");
      select.value = row.confidence ?? "";
      select.addEventListener("change", (e) => {
        section.rows[idx].confidence = e.target.value;
        markDirty(true);
      });
    }

    const ctlTd = document.createElement("td");
    ctlTd.className = "ctlCell";
    const delBtn = document.createElement("button");
    delBtn.className = "danger small";
    delBtn.textContent = "Delete";
    delBtn.addEventListener("click", () => {
      section.rows.splice(idx, 1);
      renderSections();
      markDirty(true);
    });
    ctlTd.appendChild(delBtn);

    tr.appendChild(idTd);
    tr.appendChild(qTd);
    tr.appendChild(aTd);
    tr.appendChild(ownerTd);
    tr.appendChild(confTd);
    tr.appendChild(ctlTd);
    tbody.appendChild(tr);
  }

  table.appendChild(thead);
  table.appendChild(tbody);
  return table;
}

async function apiLoad() {
  const res = await fetch(`/api/project/load?name=${encodeURIComponent(project.name)}`, { cache: "no-store" });
  const json = await res.json();
  if (!json.ok) throw new Error(json.error ?? "Load failed");
  project = { name: json.project.name, jsonPath: json.project.jsonPath };
  state = json.data;
  if (!Array.isArray(state.sourceDocs)) state.sourceDocs = [];
  if (!Array.isArray(state.sections)) state.sections = [];
  return state;
}

async function apiSave() {
  const res = await fetch("/api/project/save", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: project.name, jsonPath: project.jsonPath, data: state }, null, 2),
  });
  const json = await res.json();
  if (!json.ok) throw new Error(json.error ?? "Save failed");
  project = { name: json.project.name, jsonPath: json.project.jsonPath };
}

async function apiRegistry() {
  const res = await fetch("/api/registry", { cache: "no-store" });
  const json = await res.json();
  if (!json.ok) throw new Error(json.error ?? "Registry load failed");
  registry = json.registry;
  registryPath = json.registryPath;
  return registry;
}

async function apiFinalize() {
  const res = await fetch("/api/project/finalize", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name: project.name }),
  });
  const json = await res.json();
  if (!json.ok) throw new Error(json.error ?? "Finalize failed");
  project = { name: json.project.name, jsonPath: json.project.jsonPath };
  state = json.data;
  return state;
}

function renderRegistry() {
  const count = Array.isArray(registry?.projects) ? registry.projects.length : 0;
  els.registryHint.textContent = registryPath ? `${count} project(s) · ${registryPath}` : `${count} project(s)`;
}

function renderProjectSelect() {
  els.projectSelect.innerHTML = "";

  const projects = Array.isArray(registry?.projects) ? registry.projects : [];
  const options = [
    { name: "default", jsonPath: "system-prompts-skills/requirement-skill/gaps-questionnaire-web/gap-questionnaire.json" },
    ...projects.map((p) => ({ name: p.name, jsonPath: p.jsonPath })),
  ];

  const seen = new Set();
  for (const opt of options) {
    if (!opt?.name || seen.has(opt.name)) continue;
    seen.add(opt.name);
    const o = document.createElement("option");
    o.value = opt.name;
    o.textContent = opt.name;
    els.projectSelect.appendChild(o);
  }

  els.projectSelect.value = project.name;
}

function bind() {
  els.version.addEventListener("input", (e) => {
    state.version = e.target.value;
    markDirty(true);
  });
  els.date.addEventListener("input", (e) => {
    state.date = e.target.value;
    markDirty(true);
  });
  els.status.addEventListener("change", async (e) => {
    const next = e.target.value;
    const prev = state.status ?? "Draft";

    // Completion gate: confirm + finalize (server saves + sets status=Complete)
    if (next === "Complete" && prev !== "Complete") {
      const ok = confirm(
        `Finalize gaps for "${project.name}"?\n\nThis will set status=Complete and save the project JSON.\nAfter this, requirements can proceed to FSD/architecture/coding.`
      );
      if (!ok) {
        els.status.value = prev;
        return;
      }

      try {
        await apiFinalize();
        await apiRegistry();
        renderRegistry();
        renderProjectSelect();
        render();
        toast(`Finalized ${project.name} (status=Complete)`, "info");
        return;
      } catch (err) {
        els.status.value = prev;
        toast(err.message, "error");
        return;
      }
    }

    // Guardrail: changing away from Complete should be explicit.
    if (prev === "Complete" && next !== "Complete") {
      const ok = confirm(
        `Change status away from Complete for "${project.name}"?\n\nThis may re-block downstream work until finalized again.`
      );
      if (!ok) {
        els.status.value = prev;
        return;
      }
    }

    state.status = next;
    document.body.classList.toggle("statusComplete", state.status === "Complete");
    markDirty(true);
  });

  els.addSourceDocBtn.addEventListener("click", () => {
    const next = prompt("Add a source doc (file name or link):", "");
    if (!next) return;
    state.sourceDocs.push(next.trim());
    renderSourceDocs();
    markDirty(true);
  });

  els.reloadBtn.addEventListener("click", async () => {
    if (dirty && !confirm("Discard unsaved changes and reload?")) return;
    try {
      await apiRegistry();
      renderRegistry();
      renderProjectSelect();
      await apiLoad();
      render();
      toast(`Loaded ${project.name} (${project.jsonPath})`, "info");
    } catch (e) {
      toast(e.message, "error");
    }
  });

  els.saveBtn.addEventListener("click", async () => {
    try {
      await apiSave();
      await apiRegistry();
      renderRegistry();
      renderProjectSelect();
      markDirty(false);
      toast(`Saved ${project.name} (${project.jsonPath})`, "info");
    } catch (e) {
      toast(e.message, "error");
    }
  });

  els.projectSelect.addEventListener("change", async (e) => {
    const next = e.target.value;
    if (!next) return;
    if (dirty && !confirm("Switch projects and discard unsaved changes?")) {
      els.projectSelect.value = project.name;
      return;
    }
    project = { ...project, name: next };
    try {
      await apiLoad();
      render();
      toast(`Loaded ${project.name}`, "info");
    } catch (err) {
      toast(err.message, "error");
    }
  });

  window.addEventListener("beforeunload", (e) => {
    if (!dirty) return;
    e.preventDefault();
    e.returnValue = "";
  });
}

(async function main() {
  bind();
  try {
    await apiRegistry();
    renderRegistry();
    renderProjectSelect();
    await apiLoad();
    render();
    toast(`Loaded ${project.name} (${project.jsonPath})`, "info");
  } catch (e) {
    toast(e.message, "error");
  }
})();


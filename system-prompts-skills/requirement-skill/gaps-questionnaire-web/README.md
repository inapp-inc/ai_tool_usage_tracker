## Gap manager portal (global registry + per-project JSON → Markdown)

This folder contains a small local **Gap Manager Portal** to fill requirements gap questionnaires across multiple projects, using **one JSON per project** as the single source of truth.

### What you get

- **Portal UI** to manage multiple projects (edit + finalize)
- **Per-project JSON** that is the authoritative artifact for answers (each project owns its own `gap-questionnaire.json`)
- **Registry** (`registry.json`) that records registered projects (name → jsonPath)
- **Generator** that converts JSON into:
  - `SDD_Gaps_Questionnaire.md` (the full questionnaire with answers)
  - `SDD_Gaps_Answers.md` (answers-only view for review/workshops)

### Files

- `server.mjs`: local server that serves the UI and reads/writes JSON
- `index.html`, `app.js`, `styles.css`: the UI
- `registry.json`: global registry (managed by the portal)
- `gap-questionnaire.json`: default project sample JSON (for bootstrapping)
- `generate-gap-md.mjs`: converts JSON → Markdown outputs

### Run it

From repository root:

```bash
node "system-prompts-skills/requirement-skill/gaps-questionnaire-web/ensure-portal-running.mjs"
```

Then open `http://localhost:4317` in your browser.

### Registration (automatic)

Projects are considered “registered” once the portal has seen them (load/save/finalize), and the intended automation path is:

**Project root convention:** `<projectDir>` is the folder directly under the repo root (`Presales/<ProjectName>`). The **project name** is `<ProjectName>`.

1. Ensure the per-project folder layout exists:
   - `<projectDir>/Discovery and Design/`
   - `<projectDir>/Docs/`
   - `<projectDir>/codebase/`
2. Generate the **per-project gaps JSON** first (the “original” gap doc is JSON) at:
   - `<projectDir>/Discovery and Design/gap-questionnaire.json`
3. POST to `/api/register-from-path` with that JSON path. The portal derives **project name = `<projectDir>` folder name**.
3. (Optional) generate Markdown artifacts for review, then POST to `/api/register-artifact` with `SDD_Gaps_Questionnaire.md` (and optional answers path).

The portal updates `registry.json` every time it loads/saves/finalizes a project and whenever a registration artifact is posted.

### Generate Markdown outputs

```bash
node "system-prompts-skills/requirement-skill/gaps-questionnaire-web/generate-gap-md.mjs" \
  --in "<projectDir>/Discovery and Design/gap-questionnaire.json" \
  --projectDir "<projectDir>"
```

### Generate assumptions document for unresolved gaps (recommended)

If any gaps are not fully addressed (missing answers and/or confidence L, plus open decisions), generate an assumptions doc:

```bash
node "system-prompts-skills/requirement-skill/gaps-questionnaire-web/generate-assumptions-md.mjs" \
  --in "<projectDir>/Discovery and Design/gap-questionnaire.json" \
  --projectDir "<projectDir>"
```

### Generate a Figma Make UI prompt (required before development)

Before development starts, create a Figma Make-ready prompt (max 4950 characters) based on features (FSD) and architecture notes:

```bash
node "system-prompts-skills/requirement-skill/gaps-questionnaire-web/generate-figma-make-prompt.mjs" \
  --projectDir "<projectDir>"
```

Output:

- `<projectDir>/Discovery and Design/FigmaMake_UI_Prompt.txt`

### Register the generated questionnaire artifact (API)

```bash
curl -sS "http://localhost:4317/api/register-artifact" \
  -H "content-type: application/json" \
  -d '{"name":"my-project","jsonPath":"<projectDir>/Discovery and Design/gap-questionnaire.json","questionnaireMdPath":"<projectDir>/Docs/SDD_Gaps_Questionnaire.md","answersMdPath":"<projectDir>/Docs/SDD_Gaps_Answers.md"}'
```

### Register a project from its JSON path (API, name inferred)

```bash
curl -sS "http://localhost:4317/api/register-from-path" \
  -H "content-type: application/json" \
  -d '{"jsonPath":"<projectDir>/Discovery and Design/gap-questionnaire.json"}'
```

### Completion gate

The JSON has a top-level `status` field. The intended stage gate is controlled by setting **Status = Complete** in the portal (confirmation required; portal finalizes and saves):

- `status !== "Complete"` → **do not proceed** to FSD/architecture/coding
- `status === "Complete"` → proceed; generate Markdown outputs and use them as primary input to the FSD


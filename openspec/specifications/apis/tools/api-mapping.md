# Tools — API Mapping

Base path: `/api/v1`  
Frontend module: `frontend/src/api/tools.ts`  
OpenAPI tag: `Tools`

---

## Summary

| Function | Method | Path | OpenAPI `operationId` | Auth | Status |
|----------|--------|------|----------------------|------|--------|
| `fetchTools` | GET | `/tools` | `listTools` | Bearer JWT (read) | **wired** |
| `createTool` | POST | `/tools` | `createTool` | Bearer JWT (`super_admin`) | **wired** |
| `updateTool` | PATCH | `/tools/{toolId}` | `updateTool` | Bearer JWT (`super_admin`) | **wired** |
| `deleteTool` | DELETE | `/tools/{toolId}` | — | Bearer JWT (`super_admin`) | **wired** |
| `syncTool` | POST | `/tools/{toolId}/sync` | — | Bearer JWT (`super_admin`) | **wired** |

**Related (not in `tools.ts`):**

| Consumer | Method | Path | Notes |
|----------|--------|------|-------|
| `usage.fetchToolOptions` | GET | `/tools?active=true` | Dropdown `{ id, name }[]`; subset of list |

---

## `GET /tools` — `fetchTools` / `listTools`

**Query parameters**

| Param | Type | OpenAPI | Frontend |
|-------|------|---------|----------|
| `limit` | integer | `Limit` | not used (mock returns all) |
| `cursor` | string | `Cursor` | not used |
| `active` | boolean | optional filter | used by `fetchToolOptions` |

**Response:** `200` → `ToolListResponse`

```json
{
  "data": [ /* Tool[] */ ],
  "meta": { "limit": null, "next_cursor": null, "has_more": false }
}
```

Frontend mock returns bare `AiTool[]` (no envelope). Use `apiRequest` unwrap when wiring.

**Errors:** `401 Unauthorized`

---

## `POST /tools` — `createTool` / `createTool`

**Roles:** `super_admin`

**Request body:** `ToolCreateRequest` (OpenAPI) — see [payloads.md](./payloads.md)

**Response:** `201` → `Tool`

**Errors:**

| Status | When |
|--------|------|
| `400` | Invalid pricing combination |
| `401` | Not authenticated |
| `403` | Not super admin |
| `409` | Duplicate tool name in org |
| `422` | Validation failed |

**Frontend note:** Form includes `apiKey` — store via **Credentials API** after tool create (or composite backend transaction). Not part of OpenAPI `ToolCreateRequest`.

---

## `GET /tools/{toolId}` — `getTool`

Not called directly by frontend today (list satisfies Admin page). Available in OpenAPI for detail/edit prefetch.

**Response:** `200` → `Tool`  
**Errors:** `401`, `404`

---

## `PATCH /tools/{toolId}` — `updateTool` / `updateTool`

**Roles:** `super_admin`

**Request body:** `ToolUpdateRequest` (partial)

**Response:** `200` → `Tool`

**Deactivate:** set `active: false` (maps to frontend `status: "inactive"`). OpenAPI has no `error` status — frontend `status: "error"` is sync/health metadata (FE-only until sync endpoint exists).

**Errors:** `401`, `403`, `404`, `409`, `422`

---

## `DELETE /tools/{toolId}` — `deleteTool`

**Frontend:** hard-delete from mock list.  
**OpenAPI:** path **not defined** — recommend soft-delete via `PATCH { active: false }` per FR-ADM-001, or add `DELETE` returning `204`.

**Proposed:** `204 No Content` on success; historical usage retained (deactivate semantics).

---

## `POST /tools/{toolId}/sync` — `syncTool`

**Frontend:** updates `lastSyncAt` in mock; triggers manual usage pull.  
**OpenAPI:** path **not defined** — proposed in [frontend-mapping.md](../frontend-mapping.md#recommended-openapi-additions).

**Proposed request:** no body  
**Proposed response:** `200` → extended `Tool` or `AiTool` with sync metadata (`last_sync_at`, `status`)

---

## Page index

| Route | Functions |
|-------|-----------|
| `/admin/tools` | `tools.fetchTools`, `tools.createTool`, `tools.updateTool`, `tools.deleteTool`, `tools.syncTool` |

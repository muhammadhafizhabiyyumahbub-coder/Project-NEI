# NEI — API Specification

**Scope:** Phase 1–2 endpoints are FULLY specified (method, path, request/response, errors). Later phases list endpoints with target phase only.

**Conventions** (from `ARCHITECTURE_DECISIONS.md` D4):
- Base URL: `/api/v1`
- All responses use envelope: `{"ok": true, "data": ...}` or `{"ok": false, "error": {"code", "message", "details"}}`
- IDs: UUIDv4
- Timestamps: ISO 8601 UTC milliseconds
- Pagination: cursor-based `?cursor=<opaque>&limit=<int>` (default 50, max 200)
- Idempotency: `Idempotency-Key` header on all POST
- Auth: session token cookie (set on first visit); no token → `UNAUTHENTICATED`
- Content-Type: `application/json` unless stated

---

## Phase 1 — Backend foundation

### Health

#### GET `/api/v1/health`
Returns service health and connector availability.

**Response 200:**
```json
{
  "ok": true,
  "data": {
    "status": "healthy",
    "version": "0.1.0",
    "db_writable": true,
    "connectors": [
      {"id": "rhino6", "available": true, "version": "6.x", "locked": false}
    ]
  }
}
```

**Error cases:** `DB_UNAVAILABLE` (503), `CONNECTOR_ERROR` (degraded, 200 with `status: "degraded"`)

---

### Projects

#### POST `/api/v1/projects`
Create a new project.

**Request:**
```json
{
  "name": "My Hull Design",
  "description": "Optional"
}
```

**Response 201:**
```json
{
  "ok": true,
  "data": {
    "id": "<uuid>",
    "name": "My Hull Design",
    "created_at": "2026-11-02T05:00:00.000Z",
    "updated_at": "2026-11-02T05:00:00.000Z"
  }
}
```

**Errors:** `VALIDATION_FAILED` (422)

#### GET `/api/v1/projects`
List projects.

**Query params:** `cursor`, `limit`

**Response 200:**
```json
{
  "ok": true,
  "data": {
    "items": [/* project objects */],
    "next_cursor": null
  }
}
```

#### GET `/api/v1/projects/{project_id}`
Get one project.

**Errors:** `PROJECT_NOT_FOUND` (404)

#### DELETE `/api/v1/projects/{project_id}`
Delete a project and all its tasks, artifacts, audit events.

**Request:** Idempotency-Key required.

**Response 204:** no body.

**Errors:** `PROJECT_NOT_FOUND` (404), `PROJECT_HAS_ACTIVE_TASKS` (409)

---

### Tasks

#### POST `/api/v1/projects/{project_id}/tasks`
Create a new task.

**Request:**
```json
{
  "user_request": "Create a 10 x 3 x 1 box in Rhino 6",
  "task_type": "geometry",
  "domain": "geometry"
}
```

**Response 201:**
```json
{
  "ok": true,
  "data": {
    "id": "<uuid>",
    "project_id": "<uuid>",
    "state": "PENDING",
    "created_at": "..."
  }
}
```

**Errors:** `PROJECT_NOT_FOUND` (404), `VALIDATION_FAILED` (422)

> `risk_level` is derived by the planner from `task_type` and the tool actions in the plan. It is not supplied by the user in the request body.
List tasks in a project.

**Query params:** `cursor`, `limit`, `state` (filter, optional)

#### GET `/api/v1/projects/{project_id}/tasks/{task_id}`
Get full task record including plan, state, errors.

**Response 200:**
```json
{
  "ok": true,
  "data": {
    "id": "...",
    "state": "RUNNING",
    "user_request": "...",
    "plan": { /* Plan JSON */ },
    "errors": [],
    "warnings": [],
    "created_at": "..."
  }
}
```

**Errors:** `TASK_NOT_FOUND` (404)

#### POST `/api/v1/projects/{project_id}/tasks/{task_id}/cancel`
Cancel an active task.

**Request:** Idempotency-Key required.

**Response 200:** task object with `state: "CANCELLED"`.

**Errors:** `TASK_NOT_FOUND` (404), `STATE_TRANSITION_INVALID` (409 — task already terminal)

#### POST `/api/v1/projects/{project_id}/tasks/{task_id}/provide-input`
Provide missing inputs for a task in `NEEDS_INPUT` state.

**Request:**
```json
{
  "inputs": {
    "length": 10.0,
    "width": 3.0,
    "height": 1.0,
    "document_units": "m"
  }
}
```

**Response 200:** task object with `state: "PLANNING"` (re-entered).

**Errors:** `TASK_NOT_FOUND` (404), `STATE_TRANSITION_INVALID` (409 — not in NEEDS_INPUT)

#### POST `/api/v1/projects/{project_id}/tasks/{task_id}/retry`
Create a new execution attempt for a failed/recovered task.

**Response 201:** new task object linked via `parent_task_id`.

**Errors:** `TASK_NOT_FOUND` (404), `STATE_TRANSITION_INVALID` (409 — only from FAILED/NEEDS_REVIEW)

---

### Approvals

#### GET `/api/v1/projects/{project_id}/tasks/{task_id}/approvals`
List approval requests for a task.

#### POST `/api/v1/projects/{project_id}/tasks/{task_id}/approvals`
Submit an approval decision.

**Request:**
```json
{
  "action": "approve" | "reject",
  "reason": "Optional reason for reject"
}
```

**Response 200:**
```json
{
  "ok": true,
  "data": {
    "approval_id": "<uuid>",
    "task_state": "QUEUED"
  }
}
```

**Errors:** `TASK_NOT_FOUND` (404), `STATE_TRANSITION_INVALID` (409), `APPROVAL_PAYLOAD_MISMATCH` (409 — payload hash changed since request)

---

### SSE Events

#### GET `/api/v1/events`
Server-Sent Events stream of task state changes.

**Query params:** `task_id` (optional filter), `project_id` (optional filter)

**Event format:**
```
event: task_state_changed
data: {"task_id":"<uuid>","from_state":"QUEUED","to_state":"RUNNING","timestamp":"..."}

event: task_error
data: {"task_id":"<uuid>","error":{"code":"TIMEOUT","message":"..."}}

event: task_completed
data: {"task_id":"<uuid>","state":"COMPLETED","artifact_ids":[...]}
```

**Keepalive:** `: ping` every 30s.

**Errors:** `UNAUTHENTICATED` (401)

---

## Phase 2 — Frontend foundation (no new API endpoints)

Phase 2 adds no new backend endpoints. The frontend consumes Phase 1 endpoints plus SSE.

---

## Phase 3 — Verification + Rhino 6

### Connectors

#### GET `/api/v1/connectors`
List all registered connectors with capability status.

**Response 200:**
```json
{
  "ok": true,
  "data": [
    {
      "id": "rhino6",
      "name": "Rhino 6",
      "status": "SUPPORTED",
      "version": "6.x",
      "locked": false,
      "capabilities": [
        {"name": "rhino.detect", "status": "SUPPORTED"},
        {"name": "rhino.create_box_test", "status": "SUPPORTED"},
        {"name": "rhino.export_copy", "status": "SUPPORTED"}
      ]
    }
  ]
}
```

**Capability status values:** `SUPPORTED`, `UNSUPPORTED`, `UNKNOWN`, `UNAVAILABLE`

#### GET `/api/v1/connectors/{connector_id}`
Get one connector with full capability detail.

#### POST `/api/v1/connectors/{connector_id}/probe`
Run a read-only probe (detect, version, health).

**Request:**
```json
{"probe": "detect"}
```

**Response 200:**
```json
{
  "ok": true,
  "data": {
    "connector_id": "rhino6",
    "detected": true,
    "version": "6.x",
    "bitness": "UNVERIFIED",
    "exe_path": "...",
    "running": true,
    "timestamp": "..."
  }
}
```

---

### Verification

#### GET `/api/v1/projects/{project_id}/tasks/{task_id}/verification`
Get verification record for a task.

**Response 200:**
```json
{
  "ok": true,
  "data": {
    "task_id": "...",
    "status": "PASSED" | "FAILED" | "INCOMPLETE",
    "checks": [
      {
        "target": "bounding_box",
        "expected": {"l":10.0,"w":3.0,"h":1.0},
        "actual": {"l":10.0,"w":3.0,"h":1.0},
        "tolerance": 0.001,
        "method": "geometric_inspection",
        "result": "PASSED",
        "evidence": "rhino_object_id=...",
        "timestamp": "..."
      }
    ],
    "software_version": "Rhino 6.x",
    "timestamp": "..."
  }
}
```

---

## Phase 4 — Evidence engine + EEP

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/evidence/sources` | Ingest a source document |
| GET | `/api/v1/evidence/sources` | List sources |
| GET | `/api/v1/evidence/sources/{source_id}` | Get source metadata + status |
| POST | `/api/v1/evidence/search` | Lexical/semantic search |
| POST | `/api/v1/formulas` | Register a formula record |
| GET | `/api/v1/formulas` | List formulas |
| GET | `/api/v1/formulas/{formula_id}` | Get formula record |

---

## Phase 5 — Engineering core

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/calculations` | Run a registered formula with inputs |
| GET | `/api/v1/calculations/{run_id}` | Get calculation result + trace |
| POST | `/api/v1/calculations/verify` | Verify a calculation against reference case |

---

## Phase 6 — SOLIDWORKS connector

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/connectors/solidworks2022/probe` | Detect + version + COM availability |
| POST | `/api/v1/connectors/solidworks2022/actions` | Execute allowlisted SW operation |

---

## Phase 7 — Maxsurf connector

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/connectors/maxsurf_v8i/probe` | Detect + version + format capabilities |
| POST | `/api/v1/connectors/maxsurf_v8i/actions` | Execute allowlisted Maxsurf operation |

---

## Error schema (all endpoints)

```json
{
  "ok": false,
  "error": {
    "code": "STATE_TRANSITION_INVALID",
    "message": "Task is in terminal state COMPLETED; cannot transition to QUEUED",
    "details": {
      "task_id": "...",
      "current_state": "COMPLETED",
      "requested_transition": "QUEUED"
    }
  }
}
```

**Error code list (non-exhaustive):**
- `UNAUTHENTICATED` (401)
- `VALIDATION_FAILED` (422)
- `PROJECT_NOT_FOUND` (404)
- `TASK_NOT_FOUND` (404)
- `STATE_TRANSITION_INVALID` (409)
- `APPROVAL_REQUIRED` (409)
- `APPROVAL_PAYLOAD_MISMATCH` (409)
- `CONNECTOR_UNAVAILABLE` (503)
- `CONNECTOR_ERROR` (500)
- `TIMEOUT` (504)
- `PATH_FORBIDDEN` (403)
- `IDEMPOTENCY_CONFLICT` (409)
- `DB_UNAVAILABLE` (503)

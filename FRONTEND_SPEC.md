# NEI — Frontend Specification

**Scope:** Phase 2 (full spec) + later phases (decision-level only).
**Stack:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide icons, TanStack Query.

> After Phase 1, TypeScript types are generated from the backend's OpenAPI spec via `openapi-typescript`. Do not hand-write API types.

---

## Phase 2 — Full specification

### Application shell

**Layout:** Fixed left sidebar (collapsible, 64px collapsed / 240px expanded) + main content area. Top bar shows project name and connector health indicators.

**Route structure:**
```
/                        → Dashboard
/projects                → Project list
/projects/:id            → Project workspace (tabs)
/projects/:id/tasks      → Task list + create
/projects/:id/tasks/:taskId  → Task detail (state, plan, verification, artifacts)
/connectors              → Connector health + capabilities
/settings                → LLM config, privacy mode, data root path
```

**Sidebar items (icon + label):**
- Dashboard (LayoutDashboard)
- Projects (Folder)
- Connectors (Plug)
- Settings (Settings)

### Dashboard

**Purpose:** Overview page. First screen the user sees.

**Sections (top to bottom):**
1. **System status** — 3 tiles: backend health, DB writable, active connector count. Green/amber/red.
2. **Active tasks** — Table of tasks in non-terminal states (last 20). Columns: symbol/task name, state (badge), risk level, started_at. Click → task detail.
3. **Recent artifacts** — Last 5 artifacts across all projects. Thumbnail + filename + project.
4. **Connector health** — Row of connector cards (Rhino, SOLIDWORKS, Maxsurf). Each shows: detected (✓/✗), version, locked state.

**States:**
| State | Behaviour |
|-------|-----------|
| Loading | Skeleton tiles + table placeholders |
| No projects | Empty state: "No projects yet. Create one to get started." + button |
| Backend offline | Red banner top: "NEI backend not reachable" + retry button |
| No active tasks | "No active tasks" in section 2 |

### Project workspace

**Tabs:** Overview | Tasks | Artifacts | Audit

- **Overview:** Project name, description, created_at, task count summary (by state), recent activity (last 10 audit events)
- **Tasks:** Full task list with state filter chips (All, Active, Completed, Failed). Create task button.
- **Artifacts:** Grid of artifact cards. Click → download or preview (image/PDF only).
- **Audit:** Chronological log of audit_events for this project. Filterable by task.

### Task detail page

**Layout:** State timeline (vertical, left) + detail panel (right).

**State timeline:** Each `task_events` row as a dot. Current state highlighted. Failed states in red.

**Detail panel sections:**
1. **Status banner** — large state badge + error/reason if any
2. **Plan** — collapsible steps list; each step shows tool name, risk level, parameters
3. **Approval** — if `WAITING_APPROVAL`: approval card with payload hash + approve/reject buttons
4. **Verification** — if `VERIFYING` or later: check table (target, expected, actual, result)
5. **Artifacts** — list of output artifacts with download links
6. **Raw data** — expandable JSON: `plan_json`, `tool_calls_json`, `errors_json`

**Actions available by state:**
| State | Buttons |
|-------|---------|
| NEEDS_INPUT | "Provide input" (inline form) |
| WAITING_APPROVAL | "Approve" / "Reject" |
| QUEUED / RUNNING / VERIFYING | "Cancel" |
| FAILED / NEEDS_REVIEW | "Retry" (creates new task) |
| CANCELLED | "Retry" |

### Connector health page

**Per connector card:**
- Name + detected status
- Version + bitness (if known)
- Capability list (SUPPORTED / UNSUPPORTED / UNKNOWN / UNAVAILABLE badges)
- "Run probe" button (POST /connectors/{id}/probe)
- Last probe timestamp

### Settings page

**Sections:**
1. **LLM** — Provider, model name, base URL, API key (password field, masked), timeout, daily token cap. "Test connection" button.
2. **Privacy mode** — Toggle `NEI_LLM_PRIVACY`. When on: shows "Template-only planner. No external LLM calls."
3. **Data root** — Path to `data/` directory. "Open folder" button.
4. **About** — NEI version, backend version, schema version.

### Design tokens

**Theme:** Dark-first. Light mode optional later.

```
--bg-primary:       hsl(220 20% 10%)   /* near-black */
--bg-secondary:     hsl(220 20% 14%)
--bg-card:          hsl(220 20% 12%)
--text-primary:     hsl(220 20% 90%)
--text-secondary:   hsl(220 10% 60%)
--accent:           hsl(200 80% 50%)   /* engineering blue */
--success:          hsl(140 60% 45%)
--warning:          hsl(40 90% 50%)
--error:            hsl(0 70% 55%)
--border:           hsl(220 15% 20%)
```

**Component library:** shadcn/ui — Button, Card, Badge, Table, Tabs, Dialog, Alert, Skeleton, Input, Select, Toggle, ScrollArea, Tooltip, Sheet.

**Icons:** Lucide only. No icon fonts.

### API integration

- TanStack Query for all data fetching
- Types generated from `/openapi.json` via `openapi-typescript` — no hand-written interfaces
- SSE: native `EventSource` for `/api/v1/events`; reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- Mutations: TanStack Query `useMutation`; invalidation on success

### Loading / empty / error states

| Pattern | Component | When |
|---------|-----------|------|
| Loading | Skeleton (shadcn) | Initial fetch, no data yet |
| Empty | EmptyState card | No items match filter |
| Error | Alert (destructive) + retry button | Fetch failed |
| Offline | Banner top (red) | Backend unreachable |
| Partial data | Show what's available + "some data unavailable" note | Connector probe partial |

### Responsive behavior

- **Desktop (≥ 1280px):** Full sidebar, multi-column layouts
- **Laptop (768–1279px):** Collapsed sidebar, single-column task detail
- **Mobile (< 768px):** **Not supported.** Decision: this is a desktop engineering tool. Show a notice on mobile: "NEI requires a desktop display." No mobile layout.

---

## Phase 3+ — Decision-level only (DEFERRED detail)

### AI Workspace (chat interface)

**Purpose:** Natural language task input. User types a request; planner produces a structured plan shown in the task detail.

**Key components:**
- Chat input (bottom, persistent)
- Plan preview (collapsible, before execution)
- Context: selected project shown in header

**Deferred:** Full chat history, multi-turn refinement, plan editing UI.

### Calculation Center

**Purpose:** Run registered formulas with inputs; show trace and result.

**Key components:** Formula selector, input form (generated from formula schema), result table with units, trace viewer.

**Deferred:** Formula registry management UI, reference case browser.

### Engineering Knowledge

**Purpose:** Search and browse sources, formulas, methods.

**Key components:** Search bar, source list with authority badges, formula detail view.

**Deferred:** Full evidence retrieval UI, citation export.

### Verification & Reports

**Purpose:** View verification records and export engineering reports.

**Key components:** Verification check table, report preview (HTML), export button (PDF).

**Deferred:** Multi-section report builder, PDF export engine.

### Software Control

**Purpose:** Manual connector operations outside of task execution.

**Key components:** Connector selector, action buttons (probe, detect, health), result panel.

**Deferred:** Batch operations, schedule monitoring.

### Project Manager

**Purpose:** Create, rename, delete projects; manage project files.

**Key components:** Project grid, create dialog, delete confirmation.

**Deferred:** Project import/export, cross-project search.

---

## Folder structure (`apps/ui/`)

```
apps/ui/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts          # fetch wrapper + auth token
│   │   ├── hooks/             # TanStack Query hooks per endpoint
│   │   └── types.ts           # generated from OpenAPI (check in, not auto at build)
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── TopBar.tsx
│   │   ├── dashboard/
│   │   ├── projects/
│   │   ├── tasks/
│   │   ├── connectors/
│   │   └── settings/
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Projects.tsx
│   │   ├── ProjectDetail.tsx
│   │   ├── TaskDetail.tsx
│   │   ├── Connectors.tsx
│   │   └── Settings.tsx
│   ├── hooks/
│   │   ├── useSse.ts         # SSE subscription
│   │   └── useAuth.ts
│   ├── lib/
│   │   ├── utils.ts
│   │   └── constants.ts
│   └── styles/
│       └── globals.css       # Tailwind + design tokens
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Milestone UI (Phase 2)

**Definition of done for Phase 2 frontend:**
- Dashboard loads and shows system status from `/health`
- Project list and create work via API
- Task list and detail page work (state, plan, errors)
- SSE updates task state live without page reload
- Connector health page shows probe results
- Settings page shows LLM config (read-only initially; write in Phase 3)
- All types from OpenAPI
- No TypeScript errors on build

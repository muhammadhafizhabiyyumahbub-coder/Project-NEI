# NEI — Architecture Audit

**Date:** 2026-11-02
**Repo status:** empty — 0 commits, 3 untracked files
**Files audited:**
| File | Size | Status |
|------|------|--------|
| `Arsitektur.py` | 52,347 B | Contains full ARCHITECTURE.md content as Python string literal; uses pypandoc to write to Linux path |
| `FrontEnd.py` | 0 B | Empty |
| `NEI_ARCHITECTURE_V2_PROMPT.md` | 17,993 B | Prompt document defining V2 audit/correction task |

---

## CRITICAL

**C1. No version-controlled content.**
Repo has 0 commits and no `.gitignore`. The 3 files are untracked. The entire architecture exists only in `Arsitektur.py` as a raw string literal embedded in a Python script. No one can diff, review, or revert architecture changes.

**C2. `Arsitektur.py` is not a source document — it is a build script with a broken target path.**
Line 1469: `out = "/mnt/data/ARCHITECTURE.md"` — Linux path on a Windows-only machine. The script also depends on `pypandoc` (PANDOC binary) for a Markdown→Markdown conversion that adds no value. The architecture content should exist as `ARCHITECTURE.md` directly in the repo, not behind a Python string + pypandoc pipeline.

**C3. No API contract exists.**
No OpenAPI spec, no endpoint definitions, no request/response schemas. Frontend (`FrontEnd.py`, 0 bytes) and backend cannot be built in parallel without a shared contract.

**C4. No database schema or migrations.**
No SQLite table definitions, no migration history. The storage layer (`nei/storage/`) in the repo structure is referenced but not defined.

---

## HIGH

**H1. `apps/ui` contradiction.**
`Arsitektur.py` line 297: `apps/ui/ # optional later`. But the Alpha 0.1 milestone (line 1384–1400) explicitly requires "User opens NEI dashboard" — a UI is mandatory for Alpha 0.1. These two statements contradict each other.

**H2. Alpha milestone ordering vs. roadmap ordering.**
Alpha 0.1 requires: dashboard + Rhino box test. In the roadmap, Rhino connector is Phase 4, but Evidence Engine is Phase 2 and Engineering Core is Phase 3 — both positioned *before* Rhino. Alpha 0.1 does not need Evidence Engine or Engineering Core, so the roadmap order forces unnecessary dependencies before the first visible milestone.

**H3. State machine has no transition table.**
The state list (PENDING → PLANNING → NEEDS_INPUT → VALIDATING → WAITING_APPROVAL → QUEUED → RUNNING → VERIFYING → COMPLETED, plus FAILED/CANCELLED/NEEDS_REVIEW/RECOVERING) is listed but no guard conditions, side effects, or failure behaviour are specified. "Active state" is not defined — which states are active, which are terminal, and what triggers RECOVERING are unspecified.

**H4. Rhino 6 transport method undecided.**
The old document lists four candidate interfaces (RhinoScript/RhinoPython, RhinoCommon, command-line, in-process helper over IPC) with no decision. No spike has been run. Without a resolved transport, the Alpha 0.1 Rhino box test cannot be implemented.

**H5. Verification Engine exists in the diagram but has no module or contract.**
The architecture diagram shows "Verification & Audit Engine" at the top level, but the repo structure only lists `engineering/validation/`. There is no `verification/` module, no `VerificationRecord` schema, no defined location.

**H6. `PLAN.md`, `IMPLEMENTATION_GUIDE.md`, `SECURITY.md`, `DATA_GOVERNANCE.md` do not exist.**
All four are referenced as required deliverables in `NEI_ARCHITECTURE_V2_PROMPT.md` §6 but are absent.

---

## MEDIUM

**M1. Process/session model for GUI automation is undefined.**
Rhino, SOLIDWORKS, and Maxsurf are desktop GUI applications. They cannot be automated from a Windows service — only from the user's interactive desktop session. The document does not specify: where the backend runs (user session vs. service), which COM/IPC apartment model, how per-application locks are enforced, what happens when the software hangs or shows a modal dialog, and how long-running jobs are managed. All of this is UNVERIFIED until tested on the target machine.

**M2. Edition and license compatibility is UNVERIFIED.**
Whether the installed Rhino 6, SOLIDWORKS 2022, or Maxsurf v8.1 editions (academic/student?) permit COM automation, scripting, or plugin loading is not confirmed. Vendor documentation must be checked before any integration claim. No bypass of licensing or protection is permitted.

**M3. Resource budget is undefined.**
Target machine: Core i3 gen 8, 8 GB RAM, MX230 GPU. Running Rhino + SOLIDWORKS + Maxsurf + backend + Vite dev server + browser simultaneously is likely to exceed available memory. A `resource_manager` module is listed in the repo structure but has no policy defined. LLM strategy (local vs. external provider, data sent, privacy mode) is mentioned but not decided.

**M4. Document drift risk.**
`Arsitektur.py` embeds the full architecture as a string. If a separate `ARCHITECTURE.md` is created, two sources of truth exist with no sync mechanism. The V2 prompt requires "every fact defined in exactly one document."

**M5. Local server security is unspecified.**
Binding to `localhost` only (vs. `0.0.0.0`), DNS rebinding protection, CSRF tokens, origin checks — none are defined. A local FastAPI server that accepts connections on all interfaces is a real risk on a shared machine.

**M6. SQLite concurrency mode is unspecified.**
WAL mode, single-writer constraint, backup strategy, and file artifact integrity (hash on write, verify on read) are not defined.

---

## LOW

**L1. `FrontEnd.py` is empty (0 bytes).**
No frontend specification exists. `NEI_ARCHITECTURE_V2_PROMPT.md` §6 item 3 requires a full `FRONTEND_SPEC.md`.

**L2. `Arsitektur.py` uses `pypandoc.convert_text(content, "md", format="md")` — a Markdown-to-Markdown conversion.**
This is a no-op that adds a PANDOC dependency for zero benefit. The content should be written directly as `.md`.

**L3. No `.gitignore`, no `README.md`, no `pyproject.toml`.**
The repo structure in `Arsitektur.py` lists these files but none exist.

**L4. Roadmap in `Arsitektur.py` uses 8 phases; V2 prompt proposes 10 phases (0–9).**
The phase numbers and boundaries differ. The V2 prompt's roadmap must be treated as the authority once Phase 2 decisions are approved.

---

## INFORMATIONAL

**I1. ANSYS is explicitly deferred.** Both documents agree on this. No action needed until the user confirms installation.

**I2. `Arsitektur.py` content is well-structured** — the embedded Markdown is a solid baseline. It should be extracted to `ARCHITECTURE.md` and the Python script archived to `docs/archive/`.

**I3. `NEI_ARCHITECTURE_V2_PROMPT.md` is a task specification, not a deliverable.** It defines the work to be done (Tahap 1–4) and the documents to produce. It should remain in the repo as `TASKS.md` or similar.

**I4. No tests exist.** No `tests/` directory. No reference cases. No CI.

---

## Open questions (blocking Tahap 2)

| # | Question | Owner |
|---|----------|-------|
| OQ1 | Where does the backend run: user desktop session (required for COM) or Windows service (cannot reach COM in interactive session)? | User decision |
| OQ2 | Which LLM provider: external API (data leaves machine) or local model (performance on i3/8GB)? | User decision |
| OQ3 | Are Rhino 6, SOLIDWORKS 2022, Maxsurf v8.1 academic/student or full licenses? Does the license permit automation? | User verification |
| OQ4 | Is Rhino 6 32-bit or 64-bit? (affects COM apartment and available scripting runtimes) | Environment probe (Phase 0) |
| OQ5 | Should the dashboard be a separate Vite React app, or a single-page app served by FastAPI? | Architecture decision |
| OQ6 | What is the project root path on this machine for `data/documents/`, `data/artifacts/`, etc.? | User decision |

---

**Audit complete. Stopping here — awaiting "lanjut" before proceeding to Tahap 2.**

import pypandoc, os, textwrap

content = r"""
# NEI — Nautical Engineering Intelligence
## Architecture & Implementation Specification
**Document:** `ARCHITECTURE.md`  
**Purpose:** Master technical specification for OpenCode / coding agents  
**Status:** Initial architecture baseline  
**Target platform:** Windows 11, single workstation, local-first  
**Primary language:** Indonesian for user-facing explanations; English identifiers and code  
**Architecture style:** Modular monolith with isolated software connectors

---

# 1. Mission and non-negotiable principles

NEI (Nautical Engineering Intelligence) is a local-first engineering assistant for naval architecture and marine engineering. It accepts natural-language instructions, retrieves traceable technical evidence, performs deterministic calculations, and operates supported engineering software through controlled connectors.

NEI is **not** an autonomous authority that certifies a ship design. It is an engineering assistance and workflow system. A qualified human remains responsible for design approval, regulatory interpretation, and release of engineering deliverables.

## 1.1 Core principles

1. **Evidence before assertion.** Technical claims and calculations must be tied to identifiable sources, equations, assumptions, and applicability conditions.
2. **Deterministic calculation.** Numeric calculations must be performed by tested code or engineering software, not by free-form LLM arithmetic.
3. **LLM as planner, not calculator.** The LLM interprets intent, plans work, selects approved tools, explains results, and identifies missing information.
4. **Local-first.** Project files, engineering documents, calculation results, logs, and indexes remain on the workstation by default.
5. **Explicit provenance.** Every input, equation, source revision, software version, script version, and output must be traceable.
6. **Fail closed.** If a source, input, method, license state, software capability, or validation condition is uncertain, NEI must stop or mark the result UNVERIFIED rather than inventing an answer.
7. **Human approval for consequential actions.** Destructive file operations, design modifications to controlled deliverables, and high-impact actions require explicit approval.
8. **No license circumvention.** NEI may use only capabilities legitimately available in the installed software environment. It must not bypass activation, licensing, access controls, or software protections.
9. **Reproducibility.** A calculation should be reproducible from stored inputs, method version, source revision, and code version.
10. **Modular growth.** ANSYS is intentionally out of scope until the user confirms it is installed and available.

## 1.2 Initial software environment

Known environment:
- Operating system: Windows 11.
- Rhino: Rhino 6.
- SOLIDWORKS: SOLIDWORKS 2022.
- Bentley Maxsurf: Maxsurf 20 V8i.
- ANSYS: not installed / not currently available; do not implement its connector yet.
- One computer; all software is local.
- Current software license status is not verified. Integration must not depend on bypassing licensing and must test only capabilities available in the installed environment.

Unknowns to discover during preflight:
- Exact Rhino 6 service release and bitness.
- Exact SOLIDWORKS 2022 service pack.
- Exact Maxsurf executable/build and available automation interfaces.
- Windows edition, CPU, RAM, GPU, storage, Python installations.
- Which software is installed, launchable, and usable in the current Windows session.

Do not infer current hardware from unrelated older conversations. Detect it.

---

# 2. Product scope

## 2.1 MVP scope

The first usable release should provide:

- Local web UI or lightweight desktop-accessible dashboard.
- Project creation and project workspace.
- Chat-style task input.
- Task planner that emits structured, inspectable plans.
- Evidence retrieval from a curated local document library.
- Engineering formula registry and deterministic calculation engine.
- Rhino 6 connector proof of concept.
- File-based project artifacts and immutable execution logs.
- Approval gates and task cancellation.
- Verification reports with source citations and calculation traces.
- SOLIDWORKS 2022 and Maxsurf v8.1 connector scaffolding, followed by capability probes and safe MVP integrations.
- Clear distinction between VERIFIED, CONDITIONAL, INVALID, and UNVERIFIED results.

## 2.2 Explicitly out of scope for the first release

- ANSYS integration. Add only after the user confirms an installed ANSYS product/version and a valid usable environment.
- Autonomous trading, external account actions, or unrelated crypto project features.
- Automatic regulatory certification or class approval.
- Unsupervised release of engineering drawings or calculations.
- Automatic deletion or overwrite of original CAD files.
- Running arbitrary LLM-generated code without validation.
- Distributed microservices or multi-computer orchestration.
- Always-on cloud upload of project data.
- Bypassing software license checks or protections.

## 2.3 Supported initial engineering domains

Build the framework so domains can be added independently. Initial priority:
1. Naval architecture fundamentals.
2. Geometry and unit handling.
3. Hydrostatics.
4. Initial stability calculations, with strict limits and warnings.
5. Ship design data management.
6. Marine engineering knowledge retrieval.
7. Structures and CFD knowledge retrieval, but do not claim solver-level validation until suitable tools and methods exist.

Do not implement advanced regulatory checks merely by copying a formula from a paper. Each method needs applicability, inputs, version, validation tests, and review.

---

# 3. High-level architecture

Use a **modular monolith** first. Keep clear module boundaries and stable interfaces. Do not split into microservices unless a later measured need justifies it.

```text
                         USER
                          |
                 NEI UI / Dashboard
                          |
                   Backend API
                          |
                Task / Session Manager
                          |
                  AI Orchestrator
             _____________|______________
            |             |              |
       Planner       Evidence Agent   Tool Router
            |             |              |
      Plan Schema    Retrieval Engine   Policy Gate
                          |              |
                 Document / Formula     |
                    Knowledge Base      |
                                         |
             ____________________________|____________________
            |                |                |                |
       Rhino 6         SOLIDWORKS 2022   Maxsurf v8.1    Local Tools
       Connector       Connector         Connector      / Python
            |                |                |
       Rhino process   SOLIDWORKS process  Maxsurf process
            |                |                |
            +----------------+----------------+
                             |
                    Artifact / Result Store
                             |
                  Verification & Audit Engine
                             |
                     Report / UI Response
```

## 3.1 Logical layers

### A. Presentation layer
Responsibilities:
- Chat interface.
- Project browser.
- Task timeline and status.
- Approval prompts.
- Evidence/source viewer.
- Calculation trace viewer.
- Artifact list and preview.
- Connector health page.
- Settings and model configuration.

The UI must never execute engineering operations directly. It sends requests to the backend.

### B. Backend/API layer
Responsibilities:
- Validate incoming requests.
- Authenticate local UI sessions if needed.
- Create tasks and sessions.
- Expose task state, artifacts, approvals, and evidence.
- Stream task events to UI.
- Enforce request-size and file-path policies.

### C. Orchestration layer
Responsibilities:
- Interpret the user request.
- Classify task domain and risk level.
- Create a structured execution plan.
- Retrieve evidence requirements.
- Select deterministic tools and connectors.
- Ask for missing inputs.
- Request approval when required.
- Summarize verified outputs without changing numeric results.

### D. Evidence and knowledge layer
Responsibilities:
- Manage source documents and versions.
- Extract text, tables, equations, figures, and page references.
- Index documents for lexical and semantic search.
- Maintain source authority, applicability, revision, and status.
- Store verified formula/method definitions.
- Provide exact citations to page/section/table/clause.

### E. Engineering calculation layer
Responsibilities:
- Unit-safe deterministic calculations.
- Formula/method implementations.
- Input validation and range checks.
- Numerical tests and reference cases.
- Calculation trace generation.
- Result status assignment.
- No LLM arithmetic.

### F. Connector and execution layer
Responsibilities:
- Discover installed software.
- Check process and application health.
- Report capabilities and versions.
- Execute allowlisted actions.
- Run scripts through supported application mechanisms.
- Inspect resulting objects/files.
- Capture screenshots when needed.
- Return structured results.

### G. Storage and audit layer
Responsibilities:
- Project data.
- Original and derived artifacts.
- Documents and indexes.
- Task records.
- Execution logs.
- Approvals.
- Calculation runs and evidence links.
- Versioned configuration.

---

# 4. Technology choices

Use conservative, maintainable tools. Verify package compatibility before pinning versions.

## 4.1 Initial stack

| Area | Recommended technology | Notes |
|---|---|---|
| Runtime | Python 3.12 | Main backend environment; separate from embedded CAD Python runtimes |
| API | FastAPI + Uvicorn | Local HTTP API |
| Schemas | Pydantic v2 | Strict typed request/result contracts |
| Configuration | pydantic-settings or python-dotenv | Secrets in `.env`, never commit |
| HTTP | httpx | LLM/provider calls and local services |
| Numerical | NumPy, SciPy | Deterministic calculations |
| Units | Pint | Unit-aware values; define canonical internal units |
| Database | SQLite initially | Single-user local MVP; migrate only if justified |
| Vector search | Qdrant local or SQLite FTS5 first | Start simple; vector DB only when useful |
| Document parsing | PyMuPDF, python-docx, openpyxl, python-pptx as needed | Preserve page/paragraph/table provenance |
| PDF OCR | OCRmyPDF/Tesseract optional | Only for scanned documents; retain original |
| GUI automation | Windows UI Automation / pywinauto; PyAutoGUI only as fallback | GUI automation is fragile; use only when necessary |
| Image inspection | OpenCV | For visual state checks, not as sole proof of engineering correctness |
| Frontend | Start with simple server-rendered or lightweight React UI | Do not overbuild before core workflow works |
| Testing | pytest | Unit, integration, fixture and regression tests |
| Logging | Python logging with structured JSON | Correlation IDs and redaction |
| Workflow | Explicit state machine first | Add LangGraph only if complexity warrants it |

Do not add Redis, PostgreSQL, Kubernetes, Docker orchestration, or multiple services in the MVP without a demonstrated need.

## 4.2 LLM provider abstraction

Create a provider-neutral interface. The system must work with a configured OpenAI-compatible endpoint or local model where supported.

Required settings:
- provider name
- base URL
- model identifier
- API key reference (never log key)
- request timeout
- maximum output tokens
- temperature
- retry policy
- budget/usage limit
- privacy mode

The LLM must not receive full source PDFs or entire CAD files by default. Send only the relevant extracted passages, metadata, and structured inputs.

---

# 5. Repository structure

Use this structure as the target. It can be adjusted after inspecting an existing repository, but do not discard existing working code without reviewing it.

```text
NEI/
├── README.md
├── PLAN.md
├── ARCHITECTURE.md
├── IMPLEMENTATION_GUIDE.md
├── SECURITY.md
├── DATA_GOVERNANCE.md
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.lock                 # generated/maintained after dependency review
│
├── apps/
│   ├── api/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── projects.py
│   │       ├── tasks.py
│   │       ├── approvals.py
│   │       ├── evidence.py
│   │       ├── calculations.py
│   │       └── connectors.py
│   └── ui/                            # optional later
│
├── nei/
│   ├── config/
│   │   ├── settings.py
│   │   └── logging_config.py
│   │
│   ├── core/
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   ├── task_manager.py
│   │   ├── state_machine.py
│   │   ├── tool_router.py
│   │   ├── model_router.py
│   │   └── prompt_templates/
│   │
│   ├── contracts/
│   │   ├── task.py
│   │   ├── plan.py
│   │   ├── tool.py
│   │   ├── connector.py
│   │   ├── evidence.py
│   │   ├── calculation.py
│   │   ├── artifact.py
│   │   └── events.py
│   │
│   ├── evidence/
│   │   ├── ingestion/
│   │   │   ├── pdf.py
│   │   │   ├── docx.py
│   │   │   ├── html.py
│   │   │   └── metadata.py
│   │   ├── extraction/
│   │   │   ├── sections.py
│   │   │   ├── tables.py
│   │   │   └── equations.py
│   │   ├── indexing/
│   │   │   ├── lexical.py
│   │   │   └── semantic.py
│   │   ├── retrieval.py
│   │   ├── authority.py
│   │   ├── applicability.py
│   │   └── citation_builder.py
│   │
│   ├── knowledge/
│   │   ├── source_registry.py
│   │   ├── formula_registry.py
│   │   ├── method_registry.py
│   │   ├── unit_registry.py
│   │   └── schemas/
│   │
│   ├── engineering/
│   │   ├── units/
│   │   ├── geometry/
│   │   ├── hydrostatics/
│   │   ├── stability/
│   │   ├── resistance/
│   │   ├── propulsion/
│   │   ├── structures/
│   │   └── validation/
│   │
│   ├── connectors/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── discovery.py
│   │   ├── rhino6/
│   │   │   ├── connector.py
│   │   │   ├── probe.py
│   │   │   ├── executor.py
│   │   │   ├── transport.py
│   │   │   ├── scripts/
│   │   │   │   ├── common/
│   │   │   │   ├── geometry/
│   │   │   │   ├── hull/
│   │   │   │   └── inspection/
│   │   │   └── tests/
│   │   ├── solidworks2022/
│   │   │   ├── connector.py
│   │   │   ├── probe.py
│   │   │   ├── com_client.py
│   │   │   ├── executor.py
│   │   │   ├── scripts/
│   │   │   └── tests/
│   │   └── maxsurf/
│   │       ├── connector.py
│   │       ├── probe.py
│   │       ├── file_exchange.py
│   │       ├── gui_adapter.py
│   │       ├── scripts/
│   │       └── tests/
│   │
│   ├── automation/
│   │   ├── desktop_session.py
│   │   ├── ui_automation.py
│   │   ├── screen_capture.py
│   │   ├── visual_observer.py
│   │   └── safety.py
│   │
│   ├── execution/
│   │   ├── policy.py
│   │   ├── approvals.py
│   │   ├── script_validator.py
│   │   ├── sandbox.py
│   │   ├── scheduler.py
│   │   └── resource_manager.py
│   │
│   ├── storage/
│   │   ├── database.py
│   │   ├── repositories/
│   │   ├── artifact_store.py
│   │   ├── project_store.py
│   │   └── migrations/
│   │
│   ├── reporting/
│   │   ├── engineering_report.py
│   │   ├── calculation_report.py
│   │   └── export.py
│   │
│   └── observability/
│       ├── audit.py
│       ├── metrics.py
│       └── event_bus.py
│
├── data/
│   ├── documents/                     # local source documents; do not commit by default
│   ├── indexes/
│   ├── formulas/
│   ├── projects/
│   ├── artifacts/
│   ├── logs/
│   └── backups/
│
├── scripts/
│   ├── preflight_windows.ps1
│   ├── check_environment.py
│   └── dev_start.ps1
│
└── tests/
    ├── unit/
    ├── integration/
    ├── fixtures/
    ├── engineering_reference_cases/
    └── security/
```

---

# 6. Core data contracts

All inter-module communication must use typed schemas. Do not pass unstructured natural-language strings between core modules when a structured object is appropriate.

## 6.1 Task schema

A task should include:
- `task_id`: UUID
- `schema_version`
- `project_id`
- `parent_task_id` optional
- `user_request`
- `task_type`
- `domain`
- `risk_level`
- `plan`
- `state`
- `created_at`, `started_at`, `completed_at`
- `connector_id` optional
- `tool_calls`
- `input_artifacts`
- `output_artifacts`
- `evidence_refs`
- `calculation_run_ids`
- `approval_ids`
- `software_versions`
- `errors` and `warnings`

## 6.2 Task state machine

Allowed states:

```text
PENDING
  -> PLANNING
  -> NEEDS_INPUT
  -> VALIDATING
  -> WAITING_APPROVAL
  -> QUEUED
  -> RUNNING
  -> VERIFYING
  -> COMPLETED

Any active state may transition to:
  FAILED
  CANCELLED
  NEEDS_REVIEW
  RECOVERING
```

Rules:
- A task cannot enter RUNNING until policy validation passes.
- A task requiring approval cannot enter QUEUED/RUNNING until approval is recorded.
- A failed verification must not be reported as successful.
- Retrying must create a new execution attempt linked to the original task.
- Every transition must be timestamped and audited.

## 6.3 Tool action schema

Each tool action must declare:
- `tool_name`
- `tool_version`
- `description`
- `input_schema`
- `output_schema`
- `risk_level`
- `requires_approval`
- `timeout_seconds`
- `allowed_project_paths`
- `idempotent`
- `preconditions`
- `postconditions`

Only registered tools may execute. The LLM must not invent tool names or invoke arbitrary Python, PowerShell, shell, COM, or filesystem operations.

## 6.4 Connector contract

Define a common abstract connector interface:

```python
class BaseConnector:
    connector_id: str

    def detect(self) -> "DetectionResult":
        ...

    def get_version(self) -> "SoftwareVersion | None":
        ...

    def get_capabilities(self) -> list["Capability"]:
        ...

    def health_check(self) -> "HealthResult":
        ...

    def execute(self, action: str, parameters: dict) -> "ToolResult":
        ...

    def inspect(self, target: dict) -> "InspectionResult":
        ...

    def shutdown_or_detach(self) -> None:
        ...
```

Do not assume every connector supports every operation. Capabilities must be discovered and reported at runtime.

---

# 7. Engineering Evidence Protocol (EEP)

EEP is mandatory for all technical calculations and material engineering claims.

## 7.1 Required output fields

Every calculation result must record:
1. Calculation name and purpose.
2. Method/formula ID and method version.
3. Input values.
4. Input units.
5. Input provenance (user, CAD import, measured, assumed, derived).
6. Equation and variable definitions.
7. Assumptions and applicability conditions.
8. Source references.
9. Source revision/edition/date.
10. Source location: page, section, clause, table, figure, or equation number.
11. Calculation steps or machine-readable trace.
12. Result and unit.
13. Validation checks performed.
14. Warnings and limitations.
15. Software/library/code version.
16. Result status.

## 7.2 Source authority and classification

Each source must have metadata:

```json
{
  "source_id": "IMO-IS-CODE-2008",
  "title": "International Code on Intact Stability, 2008",
  "publisher": "International Maritime Organization",
  "source_type": "regulation",
  "authority_level": "regulatory",
  "edition": "2008",
  "amendment_status": "must_be_verified",
  "publication_date": null,
  "effective_date": null,
  "jurisdiction": "international",
  "applicability": [],
  "official_url": null,
  "local_file_path": null,
  "checksum_sha256": null,
  "accessed_at": null,
  "verification_status": "unverified"
}
```

Never fill unknown fields with guesses. Store `null` or `unknown`.

Source types:
- `regulation`
- `class_rule`
- `standard`
- `textbook`
- `peer_reviewed_journal`
- `conference_paper`
- `technical_report`
- `manufacturer_documentation`
- `software_manual`
- `other`

Authority levels must not be treated as a universal ranking. A regulation is authoritative for its legal scope; a journal paper may be more appropriate for a research method; a software manual is authoritative for software behavior. Applicability matters more than a simple source score.

## 7.3 Source validation

For every source:
- Prefer official publisher, class society, IMO, IACS, university repository, DOI publisher page, or recognized journal.
- Record author, title, publisher/journal, year, DOI/URL, edition, access date.
- Verify that the file matches the metadata.
- Compute SHA-256 checksum for local copies.
- Preserve the original document.
- Record amendments, corrigenda, errata, and superseded status when known.
- Never silently replace an old edition with a newer one.
- Do not cite search snippets as proof of a technical requirement.
- If only an abstract is accessible, label evidence as abstract-only.
- If the document is paywalled, do not pretend to have read its full text.

## 7.4 Evidence retrieval

Retrieval should:
1. Filter by domain and source type.
2. Filter by applicability (ship type, size, operation, jurisdiction, design condition).
3. Prefer current applicable editions for regulatory compliance.
4. Search lexical terms and semantic similarity.
5. Return source passages with page/section metadata.
6. Return conflicting evidence when detected.
7. Return a confidence/evidence sufficiency assessment.

Do not let vector similarity determine legal applicability. Applicability must be an explicit structured check.

## 7.5 Evidence statuses

- `VERIFIED`: source identity, location, method, applicability, and required checks have been verified to the project's defined level.
- `CONDITIONAL`: valid only under stated assumptions or incomplete scope.
- `UNVERIFIED`: source, applicability, method, or independent validation is insufficient.
- `INVALID`: a known rule, input, unit, or validation check is violated.

A `VERIFIED` label is an internal evidence status, not official approval or class certification.

---

# 8. Formula and method registry

Store formulas as versioned, reviewed records. Do not let the LLM write directly into the trusted formula registry.

## 8.1 Formula record

Required fields:
- `formula_id`
- `name`
- `domain`
- `equation_text`
- `implementation_function`
- `variables`
- `canonical_units`
- `assumptions`
- `applicability`
- `source_refs`
- `validation_case_refs`
- `review_status`
- `version`
- `created_at`
- `reviewed_by` (human identity/role if available)
- `change_log`

## 8.2 Formula lifecycle

```text
DRAFT
 -> SOURCE_ATTACHED
 -> IMPLEMENTED
 -> UNIT_TESTED
 -> REFERENCE_CASE_TESTED
 -> TECHNICAL_REVIEW
 -> APPROVED_FOR_USE
```

Only `APPROVED_FOR_USE` formulas may be used for normal production calculations. Other statuses may be used in an explicitly marked research/sandbox mode, never silently as verified output.

## 8.3 Example: displacement formula

Illustrative method only:

\[
\Delta = \rho \nabla
\]

Where:
- \(\Delta\): mass displacement (kg) when using SI mass convention.
- \(\rho\): water density (kg/m³).
- \(\nabla\): displaced volume (m³).

The system must distinguish mass displacement from weight force. If weight is required:

\[
W = \rho \nabla g
\]

Do not mix tonnes, kilograms, kN, and metric tonnes without explicit conversion. The exact density must be selected based on the applicable water condition and documented source/input.

This example is not a substitute for a reviewed formula record with a real source and test cases.

---

# 9. Calculation engine and numerical integrity

## 9.1 Rules

- Use Pint or an equivalent unit system at input/output boundaries.
- Define canonical internal units, preferably SI.
- Reject dimensionally inconsistent operations.
- Avoid silent unit coercion.
- Preserve input precision and distinguish measured precision from display precision.
- Store unrounded values; round only for presentation according to an explicit rule.
- Validate finite numbers; reject NaN and infinity unless a method explicitly handles them.
- Validate ranges and physical constraints.
- Separate input validation, calculation, and engineering interpretation.
- Provide deterministic outputs for identical inputs and versions.

## 9.2 Required test types

1. Unit tests for each formula.
2. Dimensional consistency tests.
3. Boundary-condition tests.
4. Invalid-input tests.
5. Reference-case tests from trusted published examples.
6. Regression tests against previously reviewed outputs.
7. Cross-checks against independent calculations/software when feasible.
8. Property-based tests for mathematically valid invariants where appropriate.

## 9.3 No false certainty

A calculation engine passing software tests does not prove the engineering method is appropriate. A calculation matching one reference case does not validate every operating condition.

The result must state what has and has not been validated.

---

# 10. Initial engineering modules

Create module boundaries now, but implement only methods with sourced definitions and test cases.

## 10.1 Units and geometry

Implement:
- Length, area, volume, mass, force, pressure, density, angle, speed, power, energy.
- Coordinate-system metadata.
- Geometry bounding box.
- Curve/surface/solid validity checks where supported.
- Tolerance settings with explicit units.

## 10.2 Hydrostatics

Potential methods:
- Displacement.
- Buoyancy force.
- Center of buoyancy.
- Waterplane area.
- Longitudinal/transverse waterplane moments where supported.
- KB, BM, KM, GM with clearly documented definitions and sign conventions.

Do not claim a complete hydrostatic solver until numerical integration, geometry validity, coordinate conventions, waterline handling, and reference cases are implemented.

## 10.3 Stability

Potential methods:
- Initial metacentric height.
- Free-surface correction.
- GZ curve ingestion/analysis.
- Regulatory criteria checks only when the applicable rule and vessel scope have been established.

Do not conclude that a vessel is safe from positive GM alone. Stability compliance is condition- and vessel-specific and may require multiple criteria and loading conditions.

## 10.4 Resistance and propulsion

Keep as later modules until:
- Method selection logic is sourced.
- Applicability limits are implemented.
- Input requirements are explicit.
- Reference cases exist.
- Uncertainty/limitations are reported.

Do not choose a resistance prediction method solely because it is common in an LLM response.

## 10.5 Structures and CFD

Initially provide evidence retrieval, input checklists, and report interpretation. Do not claim structural or CFD verification without a validated solver workflow, mesh/boundary-condition checks, convergence review, and suitable validation data.

---

# 11. Software connectors

All connectors implement the common contract, but each exposes only tested capabilities.

## 11.1 Rhino 6 connector

### Known technical constraint
Rhino 6's built-in RhinoPython environment is based on Python 2.7. The NEI backend should use Python 3.12 separately. Do not import Rhino 6's embedded Python packages into the backend Python environment or assume Python 3 syntax works in Rhino 6's embedded interpreter.

### Integration strategy
1. Detect Rhino installation and executable path.
2. Detect running Rhino process.
3. Determine exact version/service release and bitness.
4. Probe supported command/script execution mechanisms.
5. Test a harmless read-only operation.
6. Test creating a new disposable geometry object in a test document.
7. Inspect object ID, bounding box, geometry validity, and document state.
8. Save only to a new NEI-controlled output path after approval.

Possible interfaces to evaluate:
- RhinoScript / RhinoPython.
- RhinoCommon APIs exposed inside Rhino.
- Rhino command-line/script invocation supported by the installed release.
- A small in-process Rhino-side helper script that communicates with the NEI backend over a local authenticated channel, if the installed Rhino 6 environment supports the required mechanism.

Do not assume Rhino 8-only features exist in Rhino 6.

### Rhino 6 MVP actions
- `rhino.detect`
- `rhino.health_check`
- `rhino.get_version`
- `rhino.get_document_info`
- `rhino.list_objects`
- `rhino.create_box_test`
- `rhino.inspect_object`
- `rhino.export_copy`
- `rhino.capture_viewport`

First integration test:
- Open or create a disposable test document.
- Create a simple 10 x 3 x 1 unit box in a clearly specified unit system.
- Read the resulting bounding box.
- Verify dimensions within document tolerance.
- Save a new test file under `data/projects/<project_id>/artifacts/`.
- Do not overwrite any user file.

### Rhino scripting safety
- Scripts must be generated from approved templates or validated AST/rules.
- No arbitrary imports, network access, shell commands, file deletion, registry access, or unrestricted filesystem access.
- Use allowlisted functions and parameters.
- Log the exact script hash and template/generator version.
- Preserve the script file used for every execution.

## 11.2 SOLIDWORKS 2022 connector

### Integration strategy
Investigate official SOLIDWORKS API/COM automation exposed by the installed version and environment. Do not assume every API call or license capability is available.

Possible implementation:
- Python `pywin32` COM client in backend, subject to compatibility testing.
- A small C#/.NET helper if COM interop is more stable for a specific operation.
- SOLIDWORKS macros only when their execution is supported and approved.

### Discovery and MVP actions
- Detect installation and executable path.
- Detect running process.
- Connect to an existing session or launch only with user approval.
- Read application version and active document metadata.
- Read-only list of supported document types and basic properties.
- Create a disposable test part only after a user-approved test.
- Inspect document title, units, feature tree, and saved path.
- Save test output to a new path.

Do not begin with automatic feature-tree edits on production files.

### Capability probing
For each candidate operation, record:
- API member/interface.
- Version and service pack.
- Required license/module if known.
- Whether operation was tested.
- Input/output schema.
- Known limitations.

## 11.3 Bentley Maxsurf 20 V8i connector

Maxsurf integration must be capability-driven because the exact automation/API availability for this installed release has not yet been established.

### Strategy
1. Detect installed executables and product components.
2. Record exact build/version.
3. Inspect official/vendor documentation available to the user.
4. Identify supported import/export formats and automation interfaces.
5. Prefer documented API or automation if available.
6. Otherwise use controlled file exchange.
7. Use GUI automation only for functions that cannot be accessed reliably through other means.

### Initial actions
- `maxsurf.detect`
- `maxsurf.health_check`
- `maxsurf.get_version`
- `maxsurf.get_capabilities`
- `maxsurf.inspect_project_file`
- `maxsurf.import_copy` only if format and operation are verified
- `maxsurf.export_copy` only if format and operation are verified

Never claim API support before a working probe confirms it. Do not reverse engineer license protection or undocumented protected interfaces.

## 11.4 ANSYS connector — deferred

Do not create a functioning ANSYS connector in the MVP. It may exist only as a disabled placeholder/interface note.

When the user later confirms ANSYS is installed, ask for:
- Product(s): Workbench, Mechanical, Fluent, SpaceClaim, etc.
- Exact release and service pack.
- Windows edition.
- License type/availability (do not ask for secrets).
- Installation path.
- Whether a simple licensed launch succeeds.

Then investigate supported APIs such as PyMechanical or PyFluent for the exact installed release. Do not install ANSYS Python integrations or assume compatibility before version confirmation.

---

# 12. Execution policy and safety model

## 12.1 Risk levels

| Level | Description | Default policy |
|---|---|---|
| L0 | Read-only inspection | May run automatically |
| L1 | Create new disposable output or safe analysis | May run after preflight |
| L2 | Modify an existing design/document | Explicit user approval |
| L3 | Delete, overwrite, replace, release, or irreversible action | Explicit approval immediately before action; prefer disallow in MVP |

## 12.2 File safety

- Original source files are read-only by default.
- All generated outputs go into a project-specific NEI artifact folder.
- Never overwrite an input artifact by default.
- Use unique versioned output names.
- Before writing, verify canonical path is inside an allowed project root.
- Reject path traversal (`..`), device paths, unexpected UNC paths, and symlink/reparse-point escapes unless explicitly supported and reviewed.
- Keep a manifest with SHA-256 hashes.
- Provide backup/checkpoint before approved modifications.
- Never delete source documents automatically.

## 12.3 Script execution safety

- The LLM cannot directly execute shell commands.
- The LLM cannot directly write arbitrary scripts to trusted execution directories.
- Generated scripts are staged in a temporary area.
- Validate syntax, imports, allowed APIs, path usage, and operation risk.
- Prefer templates and parameterized functions.
- Run with least privilege.
- Apply timeouts and cancellation.
- Capture stdout/stderr and application result.
- Record script hash and execution metadata.
- Require approval for scripts that modify existing documents.

## 12.4 Human approval

Approval request must show:
- Intended operation.
- Target software and document.
- Input file path.
- Output file path.
- Whether an existing file may be changed.
- Risk level.
- Relevant evidence/method.
- Expected changes.
- Rollback/checkpoint plan.

Approval must be tied to the exact action payload/hash. If payload changes, approval is invalidated.

## 12.5 Stop and recovery

Provide:
- Cancel task.
- Stop new task dispatch.
- Detach from software without force-killing it.
- Emergency stop for NEI-controlled automation.
- Recovery state when the software crashes or becomes unresponsive.

Do not force-close engineering software with unsaved user work.

---

# 13. AI orchestration and token efficiency

## 13.1 LLM responsibilities

The LLM may:
- Interpret user intent.
- Ask for missing engineering inputs.
- Produce a structured plan.
- Select from registered tools.
- Explain evidence and results.
- Identify conflicts or uncertainty.
- Propose alternatives for human review.

The LLM must not:
- Perform authoritative numeric calculations in prose.
- Invent citations, formula IDs, regulations, or source revisions.
- Directly execute arbitrary code.
- Decide that a regulatory requirement applies without applicability data.
- Claim software operations succeeded without connector verification.
- Change trusted formula/source records without human review.

## 13.2 Token-efficient workflow

1. Use deterministic rules for simple routing and validation.
2. Use small/low-cost models for classification and structured extraction where adequate.
3. Call a stronger model only for complex planning or interpretation.
4. Retrieve only relevant document chunks, not entire PDFs.
5. Cache stable source metadata and repeated retrievals.
6. Store reusable scripts and tools; do not regenerate identical code.
7. Use local Python for calculations.
8. Use connector status and structured outputs instead of screenshots whenever possible.
9. Use screenshots only when visual inspection is needed.
10. Do not ask the LLM to restate large logs; summarize deterministically first.
11. Limit retries and prevent infinite agent loops.
12. Record model, token usage, latency, and estimated cost per task.

## 13.3 Structured planner output

Planner must return JSON matching a Pydantic schema, for example:

```json
{
  "goal": "Create a disposable Rhino test geometry",
  "domain": "geometry",
  "required_inputs": ["length", "width", "height", "document_units"],
  "steps": [
    {
      "step_id": "S1",
      "tool": "rhino.get_document_info",
      "parameters": {},
      "risk_level": "L0",
      "expected_output": "document units and document state"
    },
    {
      "step_id": "S2",
      "tool": "rhino.create_box_test",
      "parameters": {
        "length": 10.0,
        "width": 3.0,
        "height": 1.0
      },
      "risk_level": "L1",
      "expected_output": "new test object id"
    },
    {
      "step_id": "S3",
      "tool": "rhino.inspect_object",
      "parameters": {
        "target": "created_object"
      },
      "risk_level": "L0",
      "expected_output": "bounding box dimensions"
    }
  ],
  "requires_approval": false,
  "success_criteria": [
    "object exists",
    "bounding box matches requested dimensions within tolerance"
  ]
}
```

The schema must reject unknown tool names and invalid parameters.

---

# 14. Task lifecycle

Every task follows this sequence:

1. Receive request.
2. Create task record.
3. Classify domain and risk.
4. Identify missing inputs.
5. Retrieve evidence and method requirements if technical.
6. Build a structured plan.
7. Validate tool names, parameters, paths, units, and preconditions.
8. Request human approval when required.
9. Acquire software/resource lock.
10. Execute allowlisted action.
11. Inspect connector result.
12. Run deterministic verification.
13. Store artifacts and logs.
14. Build evidence-linked report.
15. Mark task complete, failed, or needs review.

A task is not complete merely because a script returned exit code 0. The postconditions must be inspected.

---

# 15. Knowledge document ingestion and legal/copyright handling

## 15.1 Accepted sources

Examples:
- IMO official publications and circulars.
- BKI official rules and guidance.
- IACS Unified Requirements and Unified Interpretations.
- Other classification society rules when relevant.
- Peer-reviewed journals.
- University repositories and theses, clearly labeled by review status.
- Recognized naval architecture and marine engineering textbooks.
- Software vendor manuals for software behavior.

## 15.2 Ingestion rules

- Keep original file immutable.
- Store source metadata separately from extracted text.
- Record checksum and ingestion timestamp.
- Preserve page numbers and section headings.
- Preserve table structure and equation context.
- OCR is not authoritative; visually verify important OCR-derived equations/tables.
- Mark missing pages, extraction errors, and unreadable diagrams.
- Do not treat an LLM-generated summary as the source itself.
- Do not redistribute copyrighted source PDFs. Store only documents the user is entitled to use; retain citations and limited extracted evidence according to applicable rights.

## 15.3 Regulatory versioning

Regulatory records must include:
- Issuing organization.
- Instrument/rule name.
- Edition and amendment.
- Adoption/effective date where known.
- Vessel/operation applicability.
- Superseded/current/unknown status.
- Official source URL.
- Exact clause/table/page.

If current applicability cannot be established, output `UNVERIFIED` and request review.

---

# 16. Reporting requirements

## 16.1 Engineering report structure

Every substantive engineering result should be exportable as a report with:

1. Executive summary.
2. Task objective.
3. Software and version.
4. Project/document identifiers.
5. Input data and provenance.
6. Method and assumptions.
7. Source references and exact locations.
8. Equations and variable definitions.
9. Calculation steps.
10. Results with units and precision.
11. Validation checks and outcomes.
12. Warnings and limitations.
13. Artifacts and hashes.
14. Human approvals.
15. Reproducibility metadata.

## 16.2 Citation format

Use a consistent citation model. For example:
- Organization/author.
- Title.
- Edition/revision.
- Year.
- Section/clause/table/page.
- DOI or official URL.
- Local source ID.

Never fabricate page numbers or clauses. If the exact location is unavailable, cite the document at the highest verified granularity and mark the citation limitation.

---

# 17. Observability and audit

Every operation should record:
- Task ID and step ID.
- Timestamp.
- User request hash or safe request record.
- Model provider/model (if called).
- Prompt template version.
- Tool name/version.
- Connector/software version.
- Input parameter hash.
- Script hash.
- Source/evidence IDs.
- Approval ID.
- Output artifact paths and hashes.
- Result status.
- Error and warning details.
- Token usage and estimated cost where available.

Secrets must be redacted. Do not log API keys, license credentials, passwords, or private tokens.

---

# 18. Testing strategy

## 18.1 Test layers

### Unit tests
- Schemas.
- State transitions.
- Unit conversions.
- Formula implementations.
- Source applicability rules.
- Path validation.
- Script validation.
- Risk policy.

### Integration tests
- SQLite persistence.
- Evidence retrieval.
- LLM structured output parsing.
- Connector discovery.
- Connector timeouts and failures.
- Artifact manifest creation.

### Software connector tests
- Start with mock connectors.
- Add real software tests only on the user's workstation.
- Use disposable documents and test folders.
- Do not test destructive operations.
- Record tested version/service pack.

### Engineering reference tests
Each approved formula must have:
- At least one trusted reference case where available.
- Expected value and tolerance.
- Source citation for expected value.
- Unit and boundary tests.
- Independent cross-check where feasible.

## 18.2 Definition of done

A feature is not done until:
- Tests pass.
- Errors are handled.
- Logs are generated.
- Documentation is updated.
- Safety policy is enforced.
- Inputs and outputs are traceable.
- A manual test procedure exists for real software integration.

---

# 19. Implementation roadmap

Do not attempt all connectors and all engineering disciplines at once.

## Phase 0 — Repository and environment audit
Deliverables:
- Inspect existing repository before editing.
- Create environment report.
- Confirm Python 3.12 availability.
- Detect Rhino 6, SOLIDWORKS 2022, Maxsurf v8.1.
- Record exact versions/service packs and executable paths.
- Confirm which applications can launch normally.
- No software modification or license changes.

Acceptance:
- `environment.json` and human-readable report.
- Connector discovery report with unknowns explicitly marked.

## Phase 1 — NEI Core Alpha
Deliverables:
- Project configuration.
- FastAPI health endpoint.
- SQLite database.
- Pydantic contracts.
- Task manager and state machine.
- Structured logging.
- Local project/artifact store.
- Basic chat/planner interface using mock tools first.

Acceptance:
- Create a task.
- View task state.
- Cancel task.
- Persist audit records.
- No CAD software needed yet.

## Phase 2 — Evidence Engine and EEP
Deliverables:
- Source registry.
- PDF ingestion with page provenance.
- Exact/lexical search.
- Formula registry.
- Citation builder.
- Evidence status and applicability fields.
- Calculation report schema.

Acceptance:
- Ingest a permitted sample document.
- Retrieve a passage with correct page/section.
- Produce a citation without invented metadata.
- Mark an incomplete/uncertain source as UNVERIFIED.

## Phase 3 — Deterministic engineering core
Deliverables:
- Unit-safe calculation framework.
- Formula lifecycle.
- Initial reviewed geometry/hydrostatics formula(s).
- Reference cases and tests.
- Calculation trace.

Acceptance:
- Same inputs produce same result.
- Wrong units are rejected.
- Missing source or test case prevents VERIFIED status.

## Phase 4 — Rhino 6 connector
Deliverables:
- Detection/probe.
- Version reporting.
- Read-only health/document inspection.
- Controlled script execution proof of concept.
- Disposable box creation and inspection.
- New-file export and screenshot.

Acceptance:
- Verify object dimensions from Rhino result, not merely script stdout.
- Save to new path.
- Preserve script and audit trace.
- No original file overwritten.

## Phase 5 — SOLIDWORKS 2022 connector
Deliverables:
- Version/process probe.
- Read-only document inspection.
- API/COM capability probe.
- Disposable test part operation if supported.
- Structured capability report.

Acceptance:
- No unsupported API is assumed.
- Operations are version-tested and logged.
- Existing user files remain untouched.

## Phase 6 — Maxsurf v8.1 connector
Deliverables:
- Version/process probe.
- Documentation and format capability audit.
- File exchange proof of concept where supported.
- GUI fallback only for required gaps.

Acceptance:
- Every claimed capability has a reproducible test.
- No undocumented license/protection bypass.
- No production design overwritten.

## Phase 7 — Cross-software workflow
Deliverables:
- Controlled artifact handoff.
- Unit and coordinate-system mapping.
- Import/export validation.
- Provenance manifest.
- Human approval for design-changing steps.

Acceptance:
- A test artifact moves between two supported applications.
- Geometry/units are checked after transfer.
- Failure is recoverable and visible.

## Phase 8 — Advanced knowledge and engineering domains
Deliverables:
- More source collections.
- More approved formula/method records.
- Advanced hydrostatics/stability/resistance/propulsion methods only as evidence and tests mature.
- Report export.

ANSYS remains deferred until user confirmation.

---

# 20. Initial acceptance milestone: NEI Alpha 0.1

The first milestone is deliberately small:

1. User opens NEI dashboard.
2. User creates a project.
3. User asks NEI to create a simple test geometry in Rhino 6.
4. Planner produces a structured plan.
5. Policy gate checks action and path.
6. Rhino connector executes an approved script.
7. Rhino creates the object in a disposable document.
8. Connector inspects object ID and bounding box.
9. Verification engine checks dimensions and units.
10. Artifact store saves a new `.3dm` output and manifest.
11. Dashboard displays result, screenshot, script hash, and execution log.
12. User can inspect the exact script and cancel future actions.

This milestone does not require an LLM to write arbitrary code. A pre-tested template with parameter substitution is preferred.

---

# 21. Instructions to OpenCode / coding agent

The coding agent must follow these instructions exactly.

## 21.1 Before coding
1. Inspect the existing repository and current files.
2. Read `README.md`, `PLAN.md`, and this `ARCHITECTURE.md` if present.
3. Identify existing working features and tests.
4. Do not overwrite or delete existing project work.
5. Produce an implementation plan with files to create/change.
6. Identify unknown environment details; do not guess.
7. Ask before any destructive migration or file replacement.

## 21.2 During coding
1. Implement one phase at a time.
2. Use small, reviewable changes.
3. Keep modules and schemas typed.
4. Add tests with each feature.
5. Run tests after each meaningful change.
6. Do not add dependencies without explaining why.
7. Do not create fake connector success responses.
8. Use mocks for unavailable software during unit tests.
9. Keep real software integration behind capability checks.
10. Never hardcode API keys, passwords, license secrets, or personal paths.
11. Never bypass licensing or software protections.
12. Do not implement ANSYS until the user explicitly confirms it is installed.
13. Do not mark a formula verified without source metadata and validation tests.
14. Do not use an LLM to perform authoritative calculations.
15. Do not claim a regulatory compliance result unless applicability and required criteria are checked.

## 21.3 Required response after each phase
Report:
- What was implemented.
- Files created/changed.
- Tests run and results.
- Known limitations.
- Security/safety considerations.
- Next recommended phase.
- Any user action required.

## 21.4 First task for OpenCode

Start with **Phase 0 and Phase 1 only**:
- Inspect repository.
- Produce environment discovery scripts.
- Create core package, settings, schemas, SQLite persistence, task state machine, health endpoint, and tests.
- Do not yet implement full AI agent behavior, document vector search, or real CAD modification.
- Do not install ANSYS or create its connector.
- Do not assume Rhino 6, SOLIDWORKS 2022, or Maxsurf v8.1 API capability until probed.

Stop after Phase 1 and report results for review before proceeding.

---

# 22. Final architecture rule

NEI must optimize for **engineering correctness, traceability, reproducibility, and safe operation**, not for appearing autonomous.

When evidence is insufficient, ask for missing data or return `UNVERIFIED`.
When a calculation is uncertain, expose the uncertainty.
When software integration is unavailable, report the limitation.
When an operation could damage a design, request approval.
When a result is produced, preserve enough information for another engineer to reproduce and review it.
"""
out = "/mnt/data/ARCHITECTURE.md"
pypandoc.convert_text(content, "md", format="md", outputfile=out, extra_args=["--standalone"])
print(f"Created: {out}")
print(f"Size: {os.path.getsize(out):,} bytes")

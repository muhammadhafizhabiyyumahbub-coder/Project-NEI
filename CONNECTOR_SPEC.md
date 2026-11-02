# NEI — Connector Specification

**Scope:** Common connector contract + capability specs for Rhino 6, SOLIDWORKS 2022, Maxsurf v8.1. ANSYS is DEFERRED.

> Capability claims in this document are `UNKNOWN` until confirmed by a Phase 0 probe or Phase 3+ spike. Do not mark a capability `SUPPORTED` without a working test.

---

## Common connector contract

All connectors implement this interface (`nei/connectors/base.py`):

```python
class BaseConnector(ABC):
    connector_id: str
    name: str

    @abstractmethod
    def detect(self) -> DetectionResult:
        """Check if software is installed. No COM call. Filesystem + registry only."""
        ...

    @abstractmethod
    def get_version(self) -> SoftwareVersion | None:
        """Return exact version + service pack if known. None if undetectable."""
        ...

    @abstractmethod
    def get_capabilities(self) -> list[Capability]:
        """Return current capability status for all known operations."""
        ...

    @abstractmethod
    def health_check(self) -> HealthResult:
        """Lightweight liveness check. No document operations."""
        ...

    @abstractmethod
    def execute(self, action: str, parameters: dict, *, timeout_s: int) -> ToolResult:
        """Execute an allowlisted action. Must be idempotent-safe where possible."""
        ...

    @abstractmethod
    def inspect(self, target: dict) -> InspectionResult:
        """Read-only inspection of an object or document state."""
        ...

    @abstractmethod
    def detach(self) -> None:
        """Gracefully release COM/session handle. Do NOT close the software."""
        ...
```

### Capability status enum

```python
class CapabilityStatus(str, Enum):
    SUPPORTED   = "SUPPORTED"    # Tested and working on this machine
    UNSUPPORTED = "UNSUPPORTED"  # Confirmed not available (vendor doc or failed probe)
    UNKNOWN     = "UNKNOWN"      # Default; not yet probed
    UNAVAILABLE = "UNAVAILABLE"  # Software not installed or not running
```

**Rule:** Default is `UNKNOWN`. Never assume `SUPPORTED`.

### Capability record

```python
@dataclass
class Capability:
    name: str           # e.g. "rhino.create_box_test"
    status: CapabilityStatus
    version_tested: str | None   # software version where tested
    last_probe_ts: str | None
    notes: str | None
```

---

## Rhino 6 (`nei/connectors/rhino6/`)

**Phase:** 3 (spike in Phase 0)

### Known constraints

- Rhino 6 embedded RhinoPython is Python 2.7. **Do not** import Rhino 6 packages into the backend Python 3.12 environment.
- Rhino 6 bitness (32/64) is UNVERIFIED. Affects which RhinoCommon assemblies can be loaded.
- Exact service release is UNVERIFIED.

### MVP actions (Alpha 0.1)

| Action | Risk | Description | Status |
|--------|------|-------------|--------|
| `rhino.detect` | L0 | Find Rhino 6 exe on disk. No launch. | UNKNOWN |
| `rhino.health_check` | L0 | Is Rhino process running? Responsive? | UNKNOWN |
| `rhino.get_version` | L0 | Read version + service release + bitness | UNKNOWN |
| `rhino.get_document_info` | L0 | Active document path, units, object count | UNKNOWN |
| `rhino.list_objects` | L0 | List object IDs, types, layers | UNKNOWN |
| `rhino.create_box_test` | L1 | Create a 10×3×1 box in a **new disposable document** | UNKNOWN |
| `rhino.inspect_object` | L0 | Read bounding box, dimensions, unit of a given object ID | UNKNOWN |
| `rhino.export_copy` | L1 | Save document to a new `.3dm` path under `data/projects/<id>/artifacts/` | UNKNOWN |
| `rhino.capture_viewport` | L1 | Screenshot of current viewport to `data/projects/<id>/artifacts/` | UNKNOWN |

### Transport method

**UNVERIFIED — to be resolved by Phase 0 spike S2.**

Candidate methods (full comparison in `RHINO6_INTEGRATION_SPIKE.md`):
1. RhinoCommon .NET plugin (C#)
2. RhinoPython (embedded Python 2.7)
3. Command-line automation (`_RunPythonScript` or `_RunCommand`)
4. Local IPC channel (named pipe / HTTP) with in-process helper
5. GUI automation (pywinauto) — fallback only

**Decision rule:** Choose the method that successfully passes the spike test (create box, read bounding box, verify dimensions) with the least fragility. Do not pre-decide.

### Script safety

- Scripts generated from approved templates only
- No arbitrary imports, network, shell, file delete, registry access
- Allowlisted RhinoCommon functions only
- Script SHA-256 logged before execution
- Script file preserved at `data/projects/<id>/artifacts/scripts/<task_id>_<step_id>.py`

---

## SOLIDWORKS 2022 (`nei/connectors/solidworks2022/`)

**Phase:** 6

### Known constraints

- SOLIDWORKS automation is via COM (IDispatch). `pywin32` is the expected bridge — **UNVERIFIED** until tested.
- Exact service pack is UNVERIFIED.
- Academic/student editions may restrict API access — **UNVERIFIED** (check license: OQ3).
- SOLIDWORKS must be running for COM attach. Launching SOLIDWORKS programmatically requires license activation.

### MVP actions

| Action | Risk | Description | Status |
|--------|------|-------------|--------|
| `sw.detect` | L0 | Find SOLIDWORKS exe, check registry for version | UNKNOWN |
| `sw.get_version` | L0 | Read COM `IAppSW3.GetCurrentVersion` | UNKNOWN |
| `sw.health_check` | L0 | Is `swProcess` responsive? | UNKNOWN |
| `sw.get_document_info` | L0 | Active document title, type, saved path, units | UNKNOWN |
| `sw.list_features` | L0 | Feature tree top-level items (read-only) | UNKNOWN |
| `sw.create_test_part` | L2 | Create a new disposable part in a new document | UNKNOWN |
| `sw.inspect_feature` | L0 | Read dimensions of a selected feature | UNKNOWN |
| `sw.export_copy` | L1 | Save as `.sldprt` to `data/projects/<id>/artifacts/` | UNKNOWN |

### Discovery probe (Phase 6 entry criteria)

Before implementing any action:
1. Detect installation (registry + filesystem)
2. Confirm version and service pack
3. Confirm COM class `SldWorks.ApplicationPm` is accessible
4. Confirm license state (does launch succeed without activation prompt?)
5. Record all in `connector_probes` table

**No COM call is made on a production document without explicit user approval (L2+).**

---

## Maxsurf Enterprise v8.1 (`nei/connectors/maxsurf81/`)

**Phase:** 7

### Known constraints

- Exact automation interface is UNVERIFIED. Maxsurf is a Bentley product; automation may be via file exchange only.
- No public Python API is assumed without vendor documentation confirming it.
- GUI automation (pywinauto) is a last-resort fallback and is **not** the primary strategy.

### Strategy

1. Detect installation (filesystem + registry)
2. Record exact build/version
3. Identify supported file formats (`.max`, `.csv`, `.igs`, `.stp`, etc.) from installed documentation
4. If a documented API exists: use it
5. Otherwise: controlled file exchange (write input file, invoke Maxsurf, read output file)
6. GUI automation only for operations with no file or API equivalent

### MVP actions

| Action | Risk | Description | Status |
|--------|------|-------------|--------|
| `maxsurf.detect` | L0 | Find Maxsurf exe, check version | UNKNOWN |
| `maxsurf.get_version` | L0 | Read exact build | UNKNOWN |
| `maxsurf.get_capabilities` | L0 | Which file formats are importable/exportable | UNKNOWN |
| `maxsurf.inspect_project_file` | L0 | Read project file metadata without opening Maxsurf | UNKNOWN |
| `maxsurf.import_copy` | L1 | Copy a source file into Maxsurf workspace (if supported) | UNKNOWN |
| `maxsurf.export_copy` | L1 | Export result to `data/projects/<id>/artifacts/` | UNKNOWN |

**No capability is marked `SUPPORTED` until a reproducible test passes on this machine.**

---

## ANSYS — DEFERRED

**No code, no probe, no placeholder.**

When the user confirms ANSYS is installed:
- Confirm product (Workbench, Mechanical, Fluent, SpaceClaim, etc.)
- Confirm exact release + service pack
- Confirm Windows edition
- Confirm license state (can it launch without activation prompt?)
- Confirm installation path
- Investigate PyMechanical / PyFluent compatibility for the exact release

**Do not implement any ANSYS connector before this confirmation.**

---

## Capability registry

Stored in `connectors` table (Phase 1, migration 002). Populated by probes.

| Field | Type | Notes |
|-------|------|-------|
| id | TEXT(36) | UUID |
| connector_id | TEXT | e.g. `rhino6` |
| name | TEXT | Display name |
| status | TEXT | `INSTALLED` / `NOT_FOUND` / `RUNNING` / `LOCKED` |
| version | TEXT | Exact version if known, else `UNKNOWN` |
| bitness | TEXT | `32` / `64` / `UNKNOWN` |
| exe_path | TEXT | Absolute path |
| last_probe_ts | TEXT | |

Capability details stored in `connector_probes` table.

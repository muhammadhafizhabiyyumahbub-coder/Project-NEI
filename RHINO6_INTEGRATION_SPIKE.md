# NEI — Rhino 6 Integration Spike

**Status:** Design document. No method is recommended until experiments are run on the target machine.
**Phase:** 0 (spike), 3 (implementation)

---

## Known constraints (UNVERIFIED until Phase 0)

| Item | Status |
|------|--------|
| Rhino 6 exact service release | UNVERIFIED |
| Rhino 6 bitness (32-bit vs 64-bit) | UNVERIFIED |
| RhinoPython Python version | Known: Python 2.7 (do not use for backend) |
| RhinoCommon assembly path | UNVERIFIED (differs by bitness) |
| Whether Rhino 6 is running at spike time | UNVERIFIED |
| License state (academic vs full) | UNVERIFIED — affects automation permission |

---

## Candidate methods

### Method 1: RhinoCommon .NET plugin (C#)

**Mechanism:** Compile a C# Rhino plugin that loads RhinoCommon, exposes a named pipe or HTTP server, and executes NEI requests.

| Aspect | Detail |
|--------|--------|
| Rhino 6 compatibility | RhinoCommon 6 assemblies available in Rhino 6 install dir. UNVERIFIED: whether a third-party plugin can be loaded in the installed edition. |
| Runtime | .NET Framework 4.x (Rhino 6 uses .NET 4). Must match Rhino's bitness. |
| Strengths | Full RhinoCommon API access; strong typing; no Python 2.7 constraint; can run as in-process helper |
| Weaknesses | Requires C# build toolchain on dev machine; plugin must be signed/loaded; bitness must match Rhino |
| Security | Plugin runs with same privileges as Rhino process; sandbox required (no arbitrary file ops) |
| Stability | High if plugin is well-written; low if Rhino crashes (plugin dies with it) |
| Parameter passing | Named pipe (JSON) or local HTTP (127.0.0.1) |
| Result reception | Same channel; structured JSON response |
| Failure detection | Pipe disconnect / HTTP timeout → RECOVERING |
| Geometry verification | Full RhinoCommon: bounding box, object count, units — most reliable |
| Cost | Medium: C# project + .NET build + plugin loading test |

**UNVERIFIED:** Whether Rhino 6 academic edition allows third-party plugin loading.

---

### Method 2: RhinoPython (embedded Python 2.7)

**Mechanism:** Write Python 2.7 scripts that use Rhino's embedded Python environment (`rhinoScript`) to execute geometry operations.

| Aspect | Detail |
|--------|--------|
| Rhino 6 compatibility | RhinoPython is bundled with Rhino 6. Python 2.7 only. |
| Runtime | Embedded in Rhino process; no separate process |
| Strengths | No external build; scripts run inside Rhino's session; direct access to RhinoCommon via Python |
| Weaknesses | Python 2.7 is EOL; no f-strings; limited stdlib; cannot share packages with backend Python 3.13; script must be syntactically valid Python 2 |
| Security | Script executes in Rhino's Python env — sandbox required (no `import os`, no `subprocess`) |
| Stability | Script crash kills the RhinoPython session; Rhino process survives |
| Parameter passing | Write script to file, invoke via Rhino command or `_RunPythonScript` |
| Result reception | Script writes JSON to a known file; backend reads it |
| Failure detection | Missing or malformed result file → RECOVERING |
| Geometry verification | RhinoCommon available in Python 2.7 env — reliable |
| Cost | Low: no build step; but Python 2.7 syntax is a maintenance burden |

**UNVERIFIED:** Whether Rhino 6's `_RunPythonScript` command is available in the installed edition and whether it can be invoked without GUI interaction.

---

### Method 3: Command-line automation (`_RunCommand` / `_RunScriptFile`)

**Mechanism:** Invoke Rhino's command interface from the backend using `_RunCommand` or `_RunScriptFile` via the Rhino executable with command-line arguments.

| Aspect | Detail |
|--------|--------|
| Rhino 6 compatibility | Rhino 6 supports `_RunScriptFile` for RhinoScript (VB) and Python. UNVERIFIED: exact syntax and flags for the installed release. |
| Runtime | Launches a new Rhino process or attaches to running one (depending on invocation) |
| Strengths | No plugin build; no COM; script is a file on disk (auditable) |
| Weaknesses | Command-line flags are undocumented or poorly documented for Rhino 6; limited structured output; hard to read results back; GUI may flash |
| Security | Script file is auditable; but command-line injection risk if parameters are user-controlled (must be escaped) |
| Stability | New process launch is slow; result reading is fragile |
| Parameter passing | Script file with substituted parameters; result written to a known file |
| Result reception | File-based; polling required |
| Failure detection | Exit code + missing result file |
| Geometry verification | Limited — script must write dimensions to a file; backend reads file |
| Cost | Low implementation; high fragility |

**UNVERIFIED:** Whether Rhino 6's command-line script invocation works without GUI interaction (headless mode) and whether the installed edition permits it.

---

### Method 4: Local IPC channel (named pipe or HTTP)

**Mechanism:** A small in-process Rhino-side helper (C# or Python 2.7) listens on a local channel. Backend sends JSON commands; helper executes RhinoCommon calls and returns structured results.

| Aspect | Detail |
|--------|--------|
| Rhino 6 compatibility | Helper must be loaded into Rhino 6's process (as a plugin or RhinoPython script). Same constraints as Methods 1 and 2. |
| Runtime | Helper lives in Rhino's process; backend is a separate Python 3.13 process |
| Strengths | Clean separation; structured JSON in/out; no file polling; low latency |
| Weaknesses | Requires helper to be loaded at Rhino startup (user must start Rhino before NEI can use it); bitness must match for C# helper |
| Security | Named pipe with per-connection auth token; no public interface |
| Stability | Helper crash = Rhino crash; RECOVERING triggered |
| Parameter passing | JSON over named pipe or HTTP |
| Result reception | JSON response on same channel |
| Failure detection | Pipe disconnect / connection refused → software not running |
| Geometry verification | Full RhinoCommon in helper — most reliable |
| Cost | Medium: helper + channel setup + startup coordination |

**UNVERIFIED:** Whether Rhino 6 will keep a helper script loaded across sessions; whether user will accept the "start Rhino before NEI" requirement.

---

### Method 5: GUI automation (pywinauto) — fallback only

**Mechanism:** Automate Rhino's GUI using `pywinauto` (Win32 UI Automation). Click menus, type commands, read values from the interface.

| Aspect | Detail |
|--------|--------|
| Rhino 6 compatibility | Works with any GUI; no Rhino-specific API needed |
| Runtime | Separate Python process; no Rhino dependency |
| Strengths | No build; no plugin; works even if all other methods fail |
| Weaknesses | Extremely fragile (Rhino UI changes break it); slow; cannot reliably read geometry values; no structured output; screen resolution/DPI dependent |
| Security | Runs with user privileges; no sandboxing benefit |
| Stability | Lowest of all methods |
| Parameter passing | Click + type; no structured interface |
| Result reception | Screen scraping (unreliable for numeric values) |
| Failure detection | UI element not found → ambiguous |
| Geometry verification | Cannot reliably read bounding box from GUI |
| Cost | Low implementation; high maintenance; **not recommended as primary method** |

**This method is a last resort. Do not use it if any of Methods 1–4 work.**

---

## Spike test (safe, disposable)

For each method, run this sequence on a **new, disposable Rhino document** (never on a production file):

```
1. Detect Rhino 6: registry + exe path + version + bitness
   → record in environment.json

2. Launch or attach to Rhino 6
   → if launch fails: record reason, stop

3. Create a new empty document (in-memory or temp file)
   → do NOT open any existing document

4. Create a box: 10 × 3 × 1 units
   → use the method's parameter-passing mechanism

5. Read back:
   - Object ID
   - Bounding box (min, max)
   - Document units
   - Object count

6. Verify:
   - bounding_box.l == 10.0 ± 0.001
   - bounding_box.w == 3.0  ± 0.001
   - bounding_box.h == 1.0  ± 0.001
   - object_count == 1
   - units match requested unit

7. Save the document to:
   data/spike/rhino_<method>_<timestamp>.3dm

8. Record:
   - Method name
   - Success / fail
   - Time taken
   - Fragility notes
   - Any Rhino errors or dialog boxes encountered
```

**Do not touch any existing Rhino document. Do not modify Rhino settings. Do not install plugins without user approval.**

---

## Pass / fail criteria per method

| Criterion | Pass | Fail |
|-----------|------|------|
| Rhino detected | Version + bitness recorded | Not found |
| Document created | Disposable doc open, no production file touched | Cannot create doc |
| Box created | Object ID returned | Script error / no object |
| Bounding box read | Dimensions within 0.001 tolerance | Wrong dimensions / no read |
| Units correct | Document units match request | Unit mismatch |
| Artifact saved | `.3dm` file exists with correct SHA-256 | File missing / wrong |
| No production file touched | No existing file modified | Any existing file changed |
| No GUI dialog blocks | No modal dialog appeared during test | Dialog appeared |

**A method PASSES the spike only if all criteria are met.**
**Choose the passing method with the lowest fragility for Phase 3 implementation.**
**If no method passes: document why and escalate to user before Phase 3.**

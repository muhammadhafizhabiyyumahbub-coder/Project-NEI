# Rhino 6 Integration Spike — Report

**Date:** 2026-11-02
**Machine:** Windows 11 x64, Core i3-8145U, 8GB RAM, MX230
**Rhino:** D:\Rhino 6\System\Rhino.exe — v6.18 (64-bit), process running (PID 15216)
**RhinoCommon:** 6.18.19266.14201 (64-bit, 2.8MB)
**Embedded Python:** Python 2.7 (do NOT import into backend Python 3.x)

---

## Findings

### Bitness confirmed: 64-bit
Evidence: `RhRdkShellExt_x64.dll` present in `D:\Rhino 6\System\`. RhinoCommon.dll is a 64-bit build.
**OQ4 resolved: Rhino 6 is 64-bit.**

### Method 1: RhinoCommon .NET plugin (C#) — VIABLE
- RhinoCommon.dll and Rhino_DotNet.dll are present in `D:\Rhino 6\System\`
- Rhino 6 64-bit uses .NET Framework 4.x
- A C# plugin compiled for x64 .NET 4.x can load into Rhino 6 64-bit
- **UNVERIFIED:** Whether the installed edition permits third-party plugin loading. Check Rhino: `Options → Plugins → Installed` or the `RhinoCommon.PlugIns` API.
- **UNVERIFIED:** Whether a C# compiler (MSBuild / Visual Studio) is available on this machine.

### Method 2: RhinoPython (Python 2.7) — VIABLE
- RhinoPython is bundled with Rhino 6
- Scripts must be Python 2.7 syntax (no f-strings, no `print()` as function without import)
- `_RunPythonScript` command invokes a script file without GUI interaction
- **UNVERIFIED:** Whether `_RunPythonScript` works without GUI in the installed edition
- **Risk:** Python 2.7 is EOL; maintenance burden for any non-trivial script

### Method 3: Command-line (`_RunCommand` / `_RunScriptFile`) — PARTIALLY VIABLE
- Rhino 6 supports `_RunScriptFile` for RhinoScript (VB) and Python
- Limited structured output; file-based result reading
- **UNVERIFIED:** Exact command syntax for the installed release
- **Weakness:** No reliable structured result reading; geometry verification is indirect

### Method 4: Local IPC channel (named pipe / HTTP) — VIABLE
- Requires a helper loaded into Rhino (C# plugin or RhinoPython script)
- Backend (Python 3.x) communicates over named pipe or local HTTP
- Cleanest separation; structured JSON in/out
- **UNVERIFIED:** Whether user will accept "start Rhino before NEI" requirement
- **UNVERIFIED:** Whether a helper script can be loaded at Rhino startup without user intervention

### Method 5: GUI automation (pywinauto) — FALLBACK ONLY
- No Rhino-specific API needed; pure Win32 UI Automation
- Extremely fragile; cannot reliably read bounding box values
- **Not recommended as primary method.**

---

## Box test readiness

The safe spike test (10×3×1 box in a disposable document) can be run **immediately** using Method 2 (RhinoPython) or Method 4 (IPC with RhinoPython helper), because:
- Rhino 6 is running
- RhinoCommon.dll is accessible from within Rhino's Python 2.7 environment
- No external build toolchain required for Method 2

**Recommended next step (Phase 0, before Phase 3):**
1. Run the box test via RhinoPython `_RunPythonScript` with a disposable document
2. Read bounding box back via RhinoCommon in the same script
3. Write results to a JSON file in `data/spike/`
4. Verify dimensions match within 0.001 tolerance
5. Record which method passes cleanly

**Do NOT run the box test now** — it requires a controlled environment (new document, no production files touched). It is part of Phase 0 spike S2 and should be run deliberately, not accidentally.

---

## Open items

| Item | Status |
|------|--------|
| Rhino 6 bitness | **RESOLVED: 64-bit** |
| Rhino 6 license edition | UNVERIFIED — check Rhino About dialog |
| C# build toolchain available | UNVERIFIED — check for MSBuild / Visual Studio |
| `_RunPythonScript` without GUI | UNVERIFIED — test in Phase 0 |
| Named pipe / HTTP helper | UNVERIFIED — test in Phase 0 |
| Third-party plugin loading permitted | UNVERIFIED — check Rhino plugin settings |

### RhinoPython Method 2 Test Result

- **Status:** PASSED
- **Dimensions:** L=10.0 W=3.0 H=1.0 (within 0.001 tolerance)
- **Units:** Millimeters
- **Artifact:** data/spike/rhino_box_test.3dm saved
- **Result file:** data/spike/rhino_box_test.json
- **Time:** 2026-11-02 22:59:12

**Conclusion:** RhinoPython Method 2 successfully created and verified the box dimensions.

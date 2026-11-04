# Rhino 6 CLI Live Test Log

**Date:** 2026-11-04  
**Machine:** Windows 11, Core i3-8145U, 8 GB RAM  
**Rhino:** D:\Rhino 6\System\Rhino.exe v6.18.19266.14201  
**Operator:** Automated (PONYTAIL MODE, per NEI_RHINO_CLI_FIX_PROMPT.md)

## Method

All attempts ran via Python 3 driver (`run_attempts.py` and `diag*.py`) with `subprocess.Popen`,
60 s timeout, only own PID killed (`taskkill /PID <pid> /T /F`). Rhino was closed before
testing (verified via `tasklist`).

## Attempts

| # | Candidate | Command | Result | Evidence |
|---|-----------|---------|--------|----------|
| 1 | C1 | `Rhino.exe /nosplash /notemplate /runscript=_-RunPythonScript (path) _-Exit` | Fail | Result file never written; process killed at 60 s |
| 2 | C2 | `Rhino.exe /nosplash /notemplate /runscript=-_RunPythonScript (path) _-Exit` | Fail | Same |
| 3 | C3 | `Rhino.exe /nosplash /runscript=_-RunPythonScript (path) _-Exit` | Fail | Same |
| 4 | C4 | `Rhino.exe /nosplash /notemplate /runscript=_-RunPythonScript path _-Exit` (no parens) | Fail | Same |
| 5 | C5 | `Rhino.exe /runscript=_-RunPythonScript (path) _-Exit` | Fail | Same |
| 6 | C6 | `Rhino.exe /nosplash /notemplate /runscript=_-RunPythonScript (path)` (no _Exit in cmd) | Fail | Same |
| 7 | diag7 | minimal.py + `/runscript=_-RunPythonScript (path)` (with parens, no _Exit in cmd) | Fail | Result not written; main window "Rhinoceros 6 Commercial" visible at t=15/30/45 s; exit code 1 at 61 s |
| 8 | diag8 | minimal.py + `/runscript=_-RunPythonScript path` (no parens, no _Exit in cmd) | Fail | Identical to diag7 |
| 9 | diag9 | `/runscript=_-Exit` (no Python script at all) | Fail | Rhino stayed open 60 s, killed, exit code 1 |
| 10 | diag10 | `/runscript=_Line 0 0 0 _-Exit` (no Python, trivial command) | Fail | Rhino stayed open 60 s, killed, exit code 1 |

## Findings

- **All 10 live attempts failed** — not a single command executed inside Rhino.
- Even `/runscript=_-Exit` (no Python involved) did not make Rhino exit; Rhino stayed
  open for the full 60 s timeout on every attempt and was force-killed by the driver.
- The main window title "Rhinoceros 6 Commercial" was visible (via `EnumWindows`)
  from t=15 s onward, suggesting Rhino opened but did not process the runscript.
- Likely cause: Rhino 6 on this machine blocks `/runscript` execution at startup —
  possibly a modal license / telemetry / first-run dialog that is not visible to a
  background Popen process, or a Rhino install-level setting (e.g., "Don't run
  startup commands").
- No `.rhp` plugin files were created or loaded during any attempt (verified: only
  our test folder under `%TEMP%\nei_rhino_cli_test\` was written to).

## Unverified Items

- [ ] Whether `/runscript` works on this machine at all (blocked by unknown modal)
- [ ] Whether `_-RunPythonScript <path>` is accepted by the Rhino 6 64-bit Commercial edition
- [ ] Correct exit mechanism after a script completes (`RhinoApp.Exit()` vs. `_-Exit`)
- [ ] Whether Rhino's "Safe Mode" (`/safemode`) would suppress the blocking dialog

## What Would Need to Happen

1. Manually open Rhino, Tools → Options → General → check "Run command line script at
   startup" is enabled, and close all startup dialogs.
2. Re-run a single attempt of candidate C1 manually from a terminal (not Popen) to
   observe whether a dialog appears and blocks execution.
3. If a dialog is observed, document it in this file and close it, then re-run.

## File Artefacts

- `box_test.py` — full box-creation + bounding-box JSON script (RhinoPython 2.7 compatible)
- `minimal.py` — minimal write-only script
- `run_attempts.py` — batch driver (candidates C1–C6)
- `diag7.py` / `diag8.py` / `diag9.py` / `diag10.py` — individual diagnostic drivers
- `attempts.json` — JSON log of all C1–C6 results
- `stdout.txt` / `stderr.txt` — Rhino's stdout/stderr (both empty in all attempts)

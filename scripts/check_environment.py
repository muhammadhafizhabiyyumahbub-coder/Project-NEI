"""Collect local software and hardware facts for Phase 0.

Unknown installation or license details stay UNVERIFIED; this script never
opens CAD documents or starts desktop applications.
"""
from __future__ import annotations

import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
import winreg
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "environment.json"


def registry_value(root: int, key: str, name: str) -> str | None:
    try:
        with winreg.OpenKey(root, key) as handle:
            value, _ = winreg.QueryValueEx(handle, name)
            return str(value)
    except (FileNotFoundError, OSError):
        return None


def find_executable(candidates: list[str]) -> str | None:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return str(path)
        found = shutil.which(candidate)
        if found:
            return found
    return None


def command_output(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT, timeout=5).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def software_record(name: str, candidates: list[str], registry_keys: list[str]) -> dict[str, object]:
    executable = find_executable(candidates)
    registry_hits = []
    for key in registry_keys:
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            if registry_value(root, key, "InstallLocation") or registry_value(root, key, "Path"):
                registry_hits.append(key)
                break
    return {
        "name": name,
        "detected": executable is not None,
        "executable": executable,
        "registry_keys": registry_hits,
        "version": "UNVERIFIED",
        "license_status": "UNVERIFIED",
    }


def physical_memory_bytes() -> int | str:
    value = ctypes.c_ulonglong(0)
    if ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(value)):
        return int(value.value) * 1024
    return "UNVERIFIED"


def gpu_name() -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = [ln.strip() for ln in result.stdout.strip().split("\n") if ln.strip()]
            return lines[0] if lines else "UNVERIFIED"
        return "UNVERIFIED"
    except Exception:
        return "UNVERIFIED"


def probe_solidworks_com() -> str:
    """Check if SOLIDWORKS COM server can be instantiated."""
    try:
        import win32com.client
        try:
            sw = win32com.client.Dispatch("SldWorks.Application")
            if sw:
                return "AVAILABLE"
        except Exception:
            pass
    except ImportError:
        return "PYWIN32_NOT_INSTALLED"
    except Exception:
        pass
    return "NOT_AVAILABLE"


def probe_maxsurf_formats() -> str:
    """Check supported file formats via registry/installed programs."""
    try:
        import winreg
        formats = []
        for reg_key in (r"SOFTWARE\Bentley\Maxsurf", r"SOFTWARE\WOW6432Node\Bentley\Maxsurf"):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key) as key:
                    val, _ = winreg.QueryValueEx(key, "InstallPath")
                    if val:
                        # Maxsurf typically supports .surf, .stl, .iges, .step
                        formats = [".surf", ".stl", ".iges", ".step", ".sat"]
                        break
            except FileNotFoundError:
                continue
        if formats:
            return ",".join(formats)
        return "UNKNOWN"
    except Exception:
        return "UNVERIFIED"


def collect() -> dict[str, object]:
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "python": {"version": platform.python_version(), "executable": sys.executable},
        "os": {"name": platform.system(), "release": platform.release(), "architecture": platform.machine()},
        "hardware": {
            "cpu": platform.processor() or "UNVERIFIED",
            "logical_cpus": os.cpu_count() or "UNVERIFIED",
            "ram_bytes": physical_memory_bytes(),
            "gpu": gpu_name(),
        },
        "software": {
            "rhino6": software_record(
                "Rhino 6",
                [r"D:\Rhino 6\System\Rhino.exe", "Rhino.exe"],
                [r"SOFTWARE\McNeel\Rhinoceros\6.0\Install", r"SOFTWARE\WOW6432Node\McNeel\Rhinoceros\6.0\Install"],
            ),
            "solidworks2022": software_record(
                "SOLIDWORKS 2022",
                [r"D:\SolidWork\SW\SOLIDWORKS\SLDWORKS.exe", r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe", "SLDWORKS.exe"],
                [r"SOFTWARE\SolidWorks\Applications\IM"] ,
            ),
            "maxsurf20_v8i": software_record(
                "Maxsurf 20 V8i",
                ["Maxsurf.exe", "MaxsurfModeler.exe"],
                [r"SOFTWARE\Bentley\Maxsurf"],
            ),
            "ansys": {"detected": False, "status": "DEFERRED"},
        },
        "probes": {
            "solidworks_com": probe_solidworks_com(),
            "maxsurf_formats": probe_maxsurf_formats(),
            "rhino_transport": "RhinoPython manual box test passed; CLI remains UNVERIFIED",
        },
    }


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(collect(), indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""SOLIDWORKS detection script for OQ4 verification.

Checks:
- Registry keys for SOLIDWORKS installations
- Common install paths
- Exe existence and version
- Writes result to data/environment_solidworks.json
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _exe_version(path: str) -> str | None:
    """Read ProductVersion from a Windows exe's version resource."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Item -LiteralPath '{path}').VersionInfo.ProductVersion"],
            capture_output=True, text=True, timeout=15,
        )
        return r.stdout.strip() or None
    except Exception:
        return None


def detect_solidworks():
    """Detect SOLIDWORKS installation on Windows."""
    results = {
        "detected": False,
        "version": None,
        "exe_path": None,
        "install_dir": None,
        "registry_key": None,
        "checked_at": _now(),
        "errors": [],
    }

    # Check custom path requested by user
    custom_paths = [
        r"D:\SolidWork\SW\SOLIDWORKS\SLDWORKS.exe",
        r"D:\SolidWork\SLDWORKS.exe",
    ]
    for path_str in custom_paths:
        path = Path(path_str)
        if path.exists():
            results["detected"] = True
            results["version"] = _exe_version(str(path))
            results["exe_path"] = str(path)
            results["install_dir"] = str(path.parent)
            print(f"[OK] Found SOLIDWORKS at {path}")
            return results

    # Check registry
    try:
        import winreg
        versions = ["2022", "2023", "2021", "2024", "2020"]
        for ver in versions:
            try:
                key_path = rf"SOFTWARE\SolidWorks\SOLIDWORKS {ver}"
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                install_dir = winreg.QueryValueEx(key, "Install Dir")[0]
                winreg.CloseKey(key)
                
                exe_path = Path(install_dir) / "SLDWORKS.exe"
                if exe_path.exists():
                    results["detected"] = True
                    results["version"] = ver
                    results["exe_path"] = str(exe_path)
                    results["install_dir"] = install_dir
                    results["registry_key"] = key_path
                    print(f"[OK] Found SOLIDWORKS {ver} at {exe_path}")
                    return results
                else:
                    results["errors"].append(f"Registry key {key_path} exists but exe not found at {exe_path}")
            except FileNotFoundError:
                continue
            except Exception as e:
                results["errors"].append(f"Registry check {ver}: {e}")
    except ImportError:
        results["errors"].append("winreg module not available (not Windows?)")
    except Exception as e:
        results["errors"].append(f"Registry check failed: {e}")

    # Check common paths
    common_paths = [
        r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
        r"C:\Program Files\SolidWorks Corp\SolidWorks\SLDWORKS.exe",
        r"C:\Program Files (x86)\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
    ]
    
    for path_str in common_paths:
        path = Path(path_str)
        if path.exists():
            results["detected"] = True
            results["exe_path"] = str(path)
            results["install_dir"] = str(path.parent)
            results["version"] = _exe_version(str(path))
            print(f"✓ Found SOLIDWORKS at {path}")
            return results

    if not results["detected"]:
        print("x SOLIDWORKS not detected")
        results["errors"].append("No SOLIDWORKS installation found in registry or common paths")

    return results


def main():
    print("SOLIDWORKS Detection (OQ4 Verification)")
    print("=" * 60)
    
    results = detect_solidworks()
    
    # Write to data/environment_solidworks.json
    output_path = Path("data/environment_solidworks.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n[OK] Results written to {output_path}")
    
    # Summary
    print("\n" + "=" * 60)
    if results["detected"]:
        print(f"RESULT: SOLIDWORKS {results['version']} DETECTED")
        print(f"EXE: {results['exe_path']}")
    else:
        print("RESULT: NOT DETECTED")
        print("\nErrors encountered:")
        for err in results["errors"]:
            print(f"  - {err}")
    
    return 0 if results["detected"] else 1


if __name__ == "__main__":
    sys.exit(main())

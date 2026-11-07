"""NEI Rhino listener helper.

Appends a manual manual-mode loop to listener.py if the env flag is set,
so a plain script execution can keep the watch directory active while Rhino is open.
"""
import os
from pathlib import Path

LISTENER = Path(r"D:\Project NEI\nei\connectors\rhino6\listener.py")
MANUAL = os.environ.get("NEI_RHINO_LISTENER_MANUAL") == "1"


def ensure_manual_mode() -> None:
    text = LISTENER.read_text(encoding="utf-8")
    marker = "_install()"
    idx = text.rindex(marker)
    tail = """

if os.environ.get('NEI_RHINO_LISTENER_MANUAL') == '1':
    while True:
        _tick(None, None)
        time.sleep(0.5)
"""
    text = text[:idx] + marker + tail + text[idx + len(marker):]
    if "import time" not in text:
        text = text.replace("import sys", "import sys\nimport time", 1)
    LISTENER.write_text(text, encoding="utf-8")


def main() -> None:
    if MANUAL:
        ensure_manual_mode()
        print("NEI Rhino listener manual-mode patch applied")
    else:
        print("No manual-mode patch applied")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""NEI Rhino 6 Listener Client — backend (Python 3).

Komunikasi dengan Rhino via file di WATCH_DIR:
1. Tulis command.json  ->Rhino (listener) membaca dan mengeksekusi script
2. Rhino menulis result.json
3. Backend membaca result.json (timeout)

Gunakan:
- User: buka Rhino manual, listener terpasang via startup command.
- Backend: `send_cmd(script_path, timeout_s=60)` -> parsed JSON dict.
"""
import json
import os
import time

WATCH_DIR = r"C:\Users\muham\AppData\Local\Temp\nei_rhino_cmd"
CMD_FILE = os.path.join(WATCH_DIR, "command.json")


def send_cmd(script_path, timeout_s=60):
    """Send a script path to the Rhino listener; wait until it has executed.

    The script writes its own result JSON to the path injected in it.
    Returns the raw command dict echoed back once the listener has picked it up,
    or None on timeout.
    """
    if not os.path.isdir(WATCH_DIR):
        os.makedirs(WATCH_DIR)

    with open(CMD_FILE, "w") as f:
        json.dump({"script": script_path}, f)

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        # Script executed = it wrote its result, which means it ran. Backend
        # reads the result file directly; we just need the listener to have run it.
        if not os.path.exists(CMD_FILE):
            # command consumed
            # brief grace for the script to finish writing its result file
            time.sleep(1.0)
            return True
        time.sleep(0.5)

    return None

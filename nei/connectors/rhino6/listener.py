# -*- coding: utf-8 -*-
"""NEI Rhino 6 Listener (RhinoPython 2.7 / IronPython).

Dipasang sekali via Tools > Options > General >
"Run these commands every time Rhino starts":
    _-RunPythonScript "D:\Project NEI\nei\connectors\rhino6\listener.py"

 NON-BLOCKING: pakai System.Windows.Forms.Timer yang hidup di scriptcontext.sticky
 supaya UI Rhino tetap responsif. Setiap tick:
   1. cek WATCH_DIR\command.json
   2. baca {script, args}; hapus file (ACK)
   3. execfile script di namespace baru
   4. script menulis result ke WATCH_DIR\result.json (opsional)
   5. log semua ke WATCH_DIR\listener.log
"""
import json
import os
import sys
import traceback

import scriptcontext

WATCH_DIR = r"C:\Users\muham\AppData\Local\Temp\nei_rhino_cmd"
LOG_FILE = os.path.join(WATCH_DIR, "listener.log")
CMD_FILE = os.path.join(WATCH_DIR, "command.json")


def _log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _tick(sender, e):
    try:
        if not os.path.exists(CMD_FILE):
            return
        try:
            with open(CMD_FILE, "r") as f:
                cmd = json.load(f)
        except Exception as ex:
            os.unlink(CMD_FILE)
            _log("bad command.json: %s" % ex)
            return

        os.unlink(CMD_FILE)  # ACK immediately; avoid double-run

        script = cmd.get("script")
        if not script or not os.path.isfile(script):
            _log("script not found: %r" % script)
            return

        ns = {"__file__": script, "__name__": "__nei__"}
        _log("run %s" % script)
        try:
            execfile(script, ns)
        except SystemExit:
            pass
        except Exception:
            _log("script error:\n" + traceback.format_exc())
    except Exception:
        pass  # never kill the timer from a tick error


def _install():
    if not os.path.isdir(WATCH_DIR):
        os.makedirs(WATCH_DIR)
    if "nei_timer" in scriptcontext.sticky:
        return  # already installed
    from System.Windows.Forms import Timer
    t = Timer()
    t.Interval = 500  # ms
    t.Tick += _tick
    t.Start()
    scriptcontext.sticky["nei_timer"] = t  # keep reference alive
    _log("listener installed, watching %s" % WATCH_DIR)


_install()

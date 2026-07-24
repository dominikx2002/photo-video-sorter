#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dev_watch.py - auto-restarts main.py every time you save a .py file
in this folder.

This is NOT true hot-reload - Tkinter can't cleanly swap widget code in a
window that's already open. What this does instead: watches the folder,
and on every save it closes the running app and launches a fresh copy.
State (chosen folders, current wizard step) resets each time, but you get
your visual change on screen within about a second of hitting Cmd+S -
no need to switch to the terminal and re-run manually.

Usage:
    pip install watchdog
    python3 dev_watch.py

Press Ctrl+C to stop.
"""
import subprocess
import sys
import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Missing dependency. Install it with:\n    pip install watchdog")
    sys.exit(1)

WATCH_DIR = Path(__file__).parent
APP_FILE = "main.py"


class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self._last_restart = 0.0
        self.start()

    def start(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print(f"\n--- starting {APP_FILE} ---")
        self.process = subprocess.Popen([sys.executable, APP_FILE], cwd=WATCH_DIR)

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        # Debounce: editors sometimes fire multiple modify events per save.
        now = time.time()
        if now - self._last_restart < 0.5:
            return
        self._last_restart = now
        print(f"\n--- change detected in {Path(event.src_path).name}, restarting ---")
        self.start()


if __name__ == "__main__":
    handler = RestartHandler()
    observer = Observer()
    observer.schedule(handler, str(WATCH_DIR), recursive=False)
    observer.start()
    print(f"Watching {WATCH_DIR} for changes. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        if handler.process:
            handler.process.terminate()
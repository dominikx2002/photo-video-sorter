import os
import sys


def resource_path(*parts):
    """
    Resolves a path to a bundled resource (a .ui file, etc.) so it works
    both when running from source and when frozen by PyInstaller.

    In dev mode, resources live next to this file (the project root).
    PyInstaller sets sys._MEIPASS to wherever it unpacked bundled data -
    for both --onefile and --onedir builds - so that takes priority when
    present.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

import os
from .constants import MEDIA_EXT

def scan_source(src, allowed_extensions=None):
    """Quick pre-scan: counts media files and lists which folders/extensions
    they belong to. Used by the wizard's Step 1 to preview what will happen,
    and again at the start of run_sort() to size the progress bar."""
    allowed = allowed_extensions if allowed_extensions is not None else MEDIA_EXT
    total = 0
    folders = set()         # set of unique folder paths containing media files
    by_ext = {}             # dictionary of extension
    for dirpath, _, filenames in os.walk(src):
        for name in filenames:
            if name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in allowed:
                total += 1
                folders.add(dirpath)
                by_ext[ext] = by_ext.get(ext, 0) + 1
    return {"total": total, "folders": len(folders), "by_ext": by_ext}

def count_media_files(src, allowed_extensions=None):
    return scan_source(src, allowed_extensions)["total"]

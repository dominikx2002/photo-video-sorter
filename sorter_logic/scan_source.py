import os
import hashlib
from .constants import MEDIA_EXT

_HEAD_TAIL = 256 * 1024   # bytes hashed from each end for the quick fingerprint


def _quick_fingerprint(path, size):
    """A fast content fingerprint: the file size plus a SHA-256 of its first
    and last 256 KB (or the whole file when small). Two files that share this
    are, for real photos/videos, byte-for-byte identical - so it's enough to
    spot duplicates cheaply, without reading every full file up front."""
    h = hashlib.sha256()
    h.update(str(size).encode())
    with open(path, "rb") as f:
        if size <= 2 * _HEAD_TAIL:
            h.update(f.read())
        else:
            h.update(f.read(_HEAD_TAIL))
            f.seek(-_HEAD_TAIL, os.SEEK_END)
            h.update(f.read(_HEAD_TAIL))
    return h.hexdigest()


def file_fingerprint(path, size=None):
    """Public wrapper: a fast content fingerprint (size + head/tail hash) used
    to spot duplicates during sorting without reading whole files."""
    if size is None:
        size = os.path.getsize(path)
    return _quick_fingerprint(path, size)


def scan_source(src, allowed_extensions=None, detect_duplicates=False):
    """Pre-scan one or more source roots (src may be a path string or a list of
    them). Counts media files, their total size, and which folders/extensions
    they belong to.

    With detect_duplicates=True it also fingerprints every file - across ALL
    roots together - so the wizard can, before any copying starts:
      * report how many are duplicates,
      * size the disk-space check on the UNIQUE bytes only, and
      * hand sorting the exact set of duplicate paths to skip - so redundant
        copies are never written and a nearly-full disk can't overflow.
    """
    roots = src if isinstance(src, (list, tuple)) else [src]
    roots = [r for r in roots if r]
    allowed = allowed_extensions if allowed_extensions is not None else MEDIA_EXT
    total = 0
    total_size = 0
    unique_size = 0
    non_media = 0
    non_media_size = 0
    folders = set()
    by_ext = {}
    found_ext = {}
    seen = {}                   # fingerprint -> first path kept (spans all roots)
    duplicate_paths = set()     # later files with content already kept

    for root in roots:
        for dirpath, _, filenames in os.walk(root):
            for name in filenames:
                if name.startswith("."):
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext not in MEDIA_EXT:
                    non_media += 1
                    try:
                        non_media_size += os.path.getsize(os.path.join(dirpath, name))
                    except OSError:
                        pass
                    continue
                found_ext[ext] = found_ext.get(ext, 0) + 1
                if ext not in allowed:
                    continue
                total += 1
                folders.add(dirpath)
                by_ext[ext] = by_ext.get(ext, 0) + 1
                path = os.path.join(dirpath, name)
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
                total_size += size

                if not detect_duplicates:
                    continue
                try:
                    fp = _quick_fingerprint(path, size)
                except OSError:
                    # Unreadable now - treat as unique; sorting surfaces the error.
                    unique_size += size
                    continue
                if fp in seen:
                    duplicate_paths.add(path)
                else:
                    seen[fp] = path
                    unique_size += size

    result = {"total": total, "folders": len(folders), "by_ext": by_ext,
              "found_ext": found_ext, "total_size": total_size,
              "non_media": non_media, "non_media_size": non_media_size}
    if detect_duplicates:
        result["duplicate_paths"] = duplicate_paths
        result["duplicate_count"] = len(duplicate_paths)
        result["unique_size"] = unique_size
    else:
        result["duplicate_paths"] = set()
        result["duplicate_count"] = 0
        result["unique_size"] = total_size
    return result


def count_media_files(src, allowed_extensions=None):
    return scan_source(src, allowed_extensions)["total"]


def find_duplicate_groups(path, allowed_extensions=None, progress=None, should_cancel=None):
    """Find identical media files under a folder, returned as a list of groups
    (each a sorted list of 2+ paths, largest groups first).

    For speed it's a two-stage sieve: files are grouped by size first (just
    metadata, no reading), and only same-size files are fingerprinted - and the
    fingerprint reads just the first and last 256 KB, not the whole file. For
    real photos and videos, identical size + identical head + identical tail
    means an identical file, so this is both fast and reliable even on a big
    library sitting on an external drive.

    progress(done, total), if given, is called as candidates are fingerprinted
    so the UI can show it isn't frozen."""
    allowed = allowed_extensions if allowed_extensions is not None else MEDIA_EXT
    by_size = {}
    for dirpath, _, filenames in os.walk(path):
        if should_cancel and should_cancel():
            return []
        for name in filenames:
            if name.startswith("."):
                continue
            if os.path.splitext(name)[1].lower() not in allowed:
                continue
            fp = os.path.join(dirpath, name)
            try:
                by_size.setdefault(os.path.getsize(fp), []).append(fp)
            except OSError:
                continue

    # Only files whose size collides can possibly be duplicates.
    candidates = [(size, fp) for size, paths in by_size.items() if len(paths) >= 2
                  for fp in paths]
    total = len(candidates)
    by_fp = {}
    for i, (size, fp) in enumerate(candidates):
        if should_cancel and (i % 25 == 0) and should_cancel():
            return []
        try:
            by_fp.setdefault(_quick_fingerprint(fp, size), []).append(fp)
        except OSError:
            pass
        if progress and (i % 25 == 0):
            progress(i + 1, total)
    if progress:
        progress(total, total)

    groups = [sorted(p) for p in by_fp.values() if len(p) >= 2]
    groups.sort(key=lambda g: -len(g))
    return groups

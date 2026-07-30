import os
import hashlib
import shutil

def unique_path(dest_dir, filename):
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_dir, filename)
    i = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dest_dir, f"{base}_{i}{ext}")
        i += 1
    return candidate


def copy_and_hash(src, dst, chunk_size=1024 * 1024):
    """
    Copies src -> dst (content + metadata, like shutil.copy2) while computing
    the SHA-256 of the content in the same single pass, so duplicate detection
    doesn't cost a second full read of every file. Returns the hex digest.

    Metadata (mtime especially) is preserved via copystat because the sorter
    relies on mtime as a date source elsewhere.
    """
    h = hashlib.sha256()
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        while True:
            chunk = fsrc.read(chunk_size)
            if not chunk:
                break
            fdst.write(chunk)
            h.update(chunk)
    shutil.copystat(src, dst)
    return h.hexdigest()


def human_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
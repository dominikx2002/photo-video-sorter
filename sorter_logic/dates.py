import os
import re
import shutil
import subprocess
import json
from datetime import datetime
from .constants import FOLDER_DATE_RE

# HEIC/HEIF support (iPhone's default photo format) is not built into Pillow.
# Registering this opener once, if the optional pillow-heif package is
# installed, makes Image.open()/getexif() work transparently for .heic/.heif
# files - without it, EXIF reads on those files silently fail and every
# iPhone photo falls straight through to weaker fallbacks.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass


def get_exif_date(path):
    """
    Tries, in order: EXIF DateTimeOriginal/DateTimeDigitized/DateTime, then
    XMP CreateDate/DateTimeOriginal/DateCreated (some editing tools only
    write XMP, especially after re-saving). Works for HEIC too, as long as
    pillow-heif is installed.
    """
    try:
        from PIL import Image
        img = Image.open(path)
        exif = img.getexif()
        if exif:
            for tag in (36867, 36868, 306):  # DateTimeOriginal, DateTimeDigitized, DateTime
                val = exif.get(tag)
                if val:
                    try:
                        return datetime.strptime(str(val)[:19], "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        continue
        return _get_xmp_date(img)
    except Exception:
        return None


def _get_xmp_date(img):
    try:
        getxmp = getattr(img, "getxmp", None)
        if not getxmp:
            return None
        value = _search_xmp(getxmp())
        if not value:
            return None
        value = str(value)[:19].replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y:%m:%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    except Exception:
        return None
    return None


def _search_xmp(node):
    """Recursively hunt a parsed XMP dict for a capture-date-ish field."""
    if isinstance(node, dict):
        for key in ("DateTimeOriginal", "CreateDate", "DateCreated", "DateTimeDigitized"):
            if key in node:
                return node[key]
        for value in node.values():
            found = _search_xmp(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _search_xmp(item)
            if found:
                return found
    return None


def get_video_date(path):
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True, timeout=30)
        tags = json.loads(out.stdout or "{}").get("format", {}).get("tags", {})
        if "creation_time" in tags:
            s = tags["creation_time"].replace("Z", "")[:19]
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    continue
    except Exception:
        return None
    return None


def get_takeout_json_date(path):
    """
    Google Photos Takeout exports sit a '<filename>.json' sidecar next to
    each media file, containing the original capture time under
    photoTakenTime - reliable even when the export process stripped or
    rewrote the media file's own EXIF/mtime.
    """
    json_path = path + ".json"
    if not os.path.exists(json_path):
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data.get("photoTakenTime", {}).get("timestamp")
        if ts:
            return datetime.fromtimestamp(int(ts))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return None


# Matches camera/phone-generated filenames that embed the exact capture
# timestamp, e.g. IMG_20230514_143022.jpg (Android), PXL_20230514_143022.jpg
# (Pixel), VID_20230514_143022.mp4, signal-2023-05-14-143022.jpg. This is
# NOT a guess like the folder-name pattern - it's a timestamp the device
# itself wrote into the name at capture time, so it survives renames-by-copy
# and is generally more trustworthy than the file's mtime.
_FILENAME_DATETIME_PATTERNS = [
    re.compile(r'(?<!\d)(20\d{2})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})(?!\d)'),
    re.compile(r'(?<!\d)(20\d{2})-(\d{2})-(\d{2})[_-](\d{2})(\d{2})(\d{2})(?!\d)'),
]
# WhatsApp-style names only carry a date, no time: IMG-20230514-WA0001.jpg
_FILENAME_DATE_ONLY_PATTERN = re.compile(r'(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)')

_CURRENT_YEAR = datetime.now().year


def get_filename_date(name):
    base = os.path.splitext(name)[0]
    for pattern in _FILENAME_DATETIME_PATTERNS:
        m = pattern.search(base)
        if m:
            y, mo, d, h, mi, s = (int(g) for g in m.groups())
            if 1990 <= y <= _CURRENT_YEAR + 1:
                try:
                    return datetime(y, mo, d, h, mi, s)
                except ValueError:
                    continue

    m = _FILENAME_DATE_ONLY_PATTERN.search(base)
    if m:
        y, mo, d = (int(g) for g in m.groups())
        if 1990 <= y <= _CURRENT_YEAR + 1:
            try:
                return datetime(y, mo, d)
            except ValueError:
                pass
    return None


def get_mtime_date(path):
    """
    Falls back to the file's last-modified timestamp. Deliberately NOT using
    st_birthtime/st_ctime ("date created") - that field resets whenever a
    file is copied to a new location, making it just as unreliable as "date
    copied". mtime is normally set by the camera/phone at capture time and
    is preserved by most copy tools (Finder, Explorer, rsync, MTP transfers).
    """
    try:
        return datetime.fromtimestamp(os.path.getmtime(path))
    except (OSError, OverflowError, ValueError):
        return None


def get_folder_date(path):
    """Checks directory names only - deliberately excludes the filename
    itself (os.path.dirname), so this stays independent from
    get_filename_date() and the "use folder name" toggle does only what
    its label says."""
    for part in reversed(os.path.dirname(path).split(os.sep)):
        m = FOLDER_DATE_RE.search(part)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), 1)
            except ValueError:
                continue
    return None

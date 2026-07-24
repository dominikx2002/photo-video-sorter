import os
import shutil
import subprocess
import json
from datetime import datetime
from .constants import FOLDER_DATE_RE

def get_exif_date(path):
    try:
        from PIL import Image
        exif = Image.open(path).getexif()
        if not exif:
            return None
        for tag in (36867, 306):  # DateTimeOriginal, DateTime
            val = exif.get(tag)
            if val:
                try:
                    return datetime.strptime(str(val)[:19], "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    continue
    except Exception:
        return None
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


def get_folder_date(path):
    for part in reversed(path.split(os.sep)):
        m = FOLDER_DATE_RE.search(part)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), 1)
            except ValueError:
                continue
    return None

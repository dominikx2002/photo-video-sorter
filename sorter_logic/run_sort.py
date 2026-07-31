import os
import shutil
import itertools
from datetime import datetime
import time
from .constants import MEDIA_EXT, PHOTO_EXT, VIDEO_EXT
from .dates import (
    get_exif_date, get_video_date, get_takeout_json_date, get_filename_date,
    get_mtime_date, get_folder_date,
)
from .fsutil import unique_path
from .scan_source import scan_source, file_fingerprint

# Folder layouts the user can pick in the advanced options. Each maps a resolved
# date to the sub-path (under the collection) the file is filed into.
FOLDER_TEMPLATES = ("year_month", "year_slash_month", "year", "year_month_flat")


def template_subpath(template, dt):
    if template == "year":
        return f"{dt.year:04d}"
    if template == "year_slash_month":
        return os.path.join(f"{dt.year:04d}", f"{dt.month:02d}")
    if template == "year_month_flat":
        return f"{dt.year:04d}-{dt.month:02d}"
    return os.path.join(f"{dt.year:04d}", f"{dt.year:04d}-{dt.month:02d}")  # year_month


def run_sort(parent, src, dst_root, use_folder_date, log_path, log, progress,
             should_cancel=None, use_mtime=True, use_filename_date=True,
             allowed_extensions=None, rename_to_date=False, on_file=None,
             move_files=False, folder_template="year_month"):
    """
    Runs the sort. Talks to the caller only through callbacks:
      log(msg)               -> one line of text, for the live log view
      progress(done, total)  -> progress update
      on_file(name)          -> optional, called right before a file starts
                                being processed (metadata reads + copy) - lets
                                the UI show what's happening during a slow
                                single-file copy, rather than looking frozen
      should_cancel()        -> optional, polled between files; return True
                                to stop early (files already copied are kept)

    Date is resolved per file in this priority order (most to least
    authoritative):
      1. EXIF/XMP (photos, including HEIC) or creation_time via ffprobe
         (videos) - metadata embedded by the camera/software itself
      2. Google Photos Takeout sidecar JSON (photoTakenTime), if present -
         Google's own record of the original capture time
      3. Timestamp embedded in the filename itself (e.g. IMG_20230514_120000,
         PXL_..., signal-2023-05-14-...), if use_filename_date - written by
         the device at capture time, so it survives copies/renames
      4. File's last-modified timestamp (mtime), if use_mtime - sturdy but
         more easily disturbed than the above; deliberately not "date
         created" (see dates.py for why)
      5. Folder name YYYY-MM pattern, if use_folder_date - explicit but coarse
      6. Copied to _NoEXIF_review for manual handling

    log_path is decided by the caller (the app knows where it wants logs
    to live - e.g. next to the script while developing, or in
    ~/Library/Logs once packaged as a .app).

    Returns (stats: dict, log_path: str). stats["cancelled"] is True if
    should_cancel() stopped the run before every file was processed.
    """
    start_time = time.time()
    # src may be a single path or a list of source roots.
    roots = src if isinstance(src, (list, tuple)) else [src]
    roots = [r for r in roots if r]
    allowed = allowed_extensions if allowed_extensions is not None else MEDIA_EXT

    have_pillow = True
    try:
        import PIL  # noqa
    except ImportError:
        have_pillow = False
    have_ffprobe = shutil.which("ffprobe") is not None

    out_base = os.path.join(dst_root, parent)
    review_dir = os.path.join(out_base, "_NoEXIF_review")
    os.makedirs(out_base, exist_ok=True)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logfile = open(log_path, "w", encoding="utf-8")

    def logline(msg, also_gui=True):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        if also_gui:
            log(line)
        logfile.write(line + "\n")

    logline("=" * 70)
    logline("Photo & Video Sorter - run started")
    logline("=" * 70)
    if len(roots) == 1:
        logline(f"Source folder:              {roots[0]}")
    else:
        logline(f"Source folders ({len(roots)}):")
        for r in roots:
            logline(f"   - {r}")
    logline(f"Destination folder:         {out_base}")
    logline(f"Pillow (EXIF) available:    {'yes' if have_pillow else 'NO - install with: pip install Pillow'}")
    logline(f"ffprobe (video dates):      {'yes' if have_ffprobe else 'NO - install with: brew install ffmpeg'}")
    logline(f"Filename-timestamp fallback: {'enabled' if use_filename_date else 'disabled'}")
    logline(f"File-modified-date fallback: {'enabled' if use_mtime else 'disabled'}")
    logline(f"Folder-name date fallback:  {'enabled' if use_folder_date else 'disabled'}")
    logline(f"Rename files to their date:  {'enabled' if rename_to_date else 'disabled'}")
    logline(f"Mode:                       {'MOVE (originals removed from source)' if move_files else 'COPY (originals kept)'}")
    logline(f"Folder template:            {folder_template}")
    logline(f"Log file:                   {log_path}")
    logline("-" * 70)

    stats = {"exif": 0, "takeout": 0, "filename": 0, "mtime": 0, "folder": 0,
             "no_date": 0, "errors": 0, "scanned": 0, "skipped": 0, "filtered": 0,
             "cancelled": False, "duplicates_removed": 0}
    no_date_files = []
    # Non-media files we did NOT copy, so the summary can list exactly what
    # stays behind in the source (documents etc.) and would be lost if the user
    # later deletes the source folder thinking everything is sorted.
    skipped_files = []

    # Inline de-duplication: fingerprint each file (size + head/tail hash) as we
    # reach it and skip any whose content we've already copied. Duplicates are
    # therefore never written, so the destination holds one copy of each unique
    # file and a nearly-full disk can't overflow. Originals are never touched.
    #   fingerprint -> source path of the copy we kept
    seen = {}

    verb = "MOVE" if move_files else "COPY"

    def copy_file(src_file, dest_dir, copy_name):
        target = unique_path(dest_dir, copy_name)
        if move_files:
            shutil.move(src_file, target)
        else:
            shutil.copy2(src_file, target)
        return target

    scan = scan_source(src, allowed)
    total = scan["total"]
    logline(f"Pre-scan complete: {total} media file(s) found across {scan['folders']} folder(s).")
    if scan["by_ext"]:
        breakdown = ", ".join(f"{ext} ({n})" for ext, n in sorted(scan["by_ext"].items(), key=lambda kv: -kv[1]))
        logline(f"File types found: {breakdown}")
    logline("-" * 70)
    progress(0, total)
    done = 0

    for dirpath, _, filenames in itertools.chain.from_iterable(os.walk(r) for r in roots):
        if stats["cancelled"]:
            break
        for name in filenames:
            if should_cancel and should_cancel():
                stats["cancelled"] = True
                logline("Sorting cancelled by user - stopping before all files were processed.")
                break
            if name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            src_file = os.path.join(dirpath, name)

            if ext not in allowed:
                if ext in MEDIA_EXT:
                    stats["filtered"] += 1
                    logline(f"[SKIP] Extension excluded by file-type filter: {src_file}")
                else:
                    stats["skipped"] += 1
                    skipped_files.append(src_file)
                    logline(f"[SKIP] Not a photo/video, left in place: {src_file}")
                continue

            stats["scanned"] += 1
            if on_file:
                on_file(name)

            try:
                fp = file_fingerprint(src_file)
            except OSError:
                fp = None
            if fp is not None:
                if fp in seen:
                    stats["duplicates_removed"] += 1
                    logline(f"[DUPLICATE] {name} -> same content as "
                            f"{os.path.basename(seen[fp])}, skipped (not copied)")
                    done += 1
                    progress(done, total)
                    continue
                seen[fp] = src_file

            try:
                dt, source = None, None

                if ext in PHOTO_EXT:
                    dt = get_exif_date(src_file)
                    if dt:
                        logline(f"[EXIF] {name} -> date found: {dt:%Y-%m-%d %H:%M:%S}")
                    else:
                        logline(f"[EXIF] {name} -> no EXIF date tag present")
                elif ext in VIDEO_EXT:
                    dt = get_video_date(src_file)
                    if dt:
                        logline(f"[VIDEO] {name} -> creation_time found via ffprobe: {dt:%Y-%m-%d %H:%M:%S}")
                    else:
                        logline(f"[VIDEO] {name} -> no creation_time metadata found")
                if dt:
                    source = "exif"

                if dt is None:
                    dt = get_takeout_json_date(src_file)
                    if dt:
                        source = "takeout"
                        logline(f"[TAKEOUT] {name} -> no metadata date, using Google Takeout sidecar JSON -> {dt:%Y-%m-%d %H:%M:%S}")

                if dt is None and use_filename_date:
                    dt = get_filename_date(name)
                    if dt:
                        source = "filename"
                        logline(f"[FILENAME] {name} -> no metadata/sidecar date, using timestamp embedded in filename -> {dt:%Y-%m-%d %H:%M:%S}")

                if dt is None and use_mtime:
                    dt = get_mtime_date(src_file)
                    if dt:
                        source = "mtime"
                        logline(f"[MTIME] {name} -> no metadata date, using file's last-modified date -> {dt:%Y-%m-%d %H:%M:%S}")

                if dt is None and use_folder_date:
                    dt = get_folder_date(src_file)
                    if dt:
                        source = "folder"
                        logline(f"[FOLDER-DATE] {name} -> no other date source, using folder name pattern -> {dt:%Y-%m}")

                if dt is None:
                    os.makedirs(review_dir, exist_ok=True)
                    target = copy_file(src_file, review_dir, name)
                    if target:
                        stats["no_date"] += 1
                        no_date_files.append(src_file)
                        logline(f"[NO DATE] {name} -> no date found from any source, copied to _NoEXIF_review")
                else:
                    dest_dir = os.path.join(out_base, template_subpath(folder_template, dt))
                    os.makedirs(dest_dir, exist_ok=True)
                    copy_name = name
                    if rename_to_date:
                        copy_name = f"{dt:%Y-%m-%d %H.%M.%S}{ext}"
                        logline(f"[RENAME] {name} -> {copy_name}")
                    target = copy_file(src_file, dest_dir, copy_name)
                    if target:
                        stats[source] += 1
                        logline(f"[{verb}] {name} -> {target}")

            except Exception as e:
                stats["errors"] += 1
                logline(f"[ERROR] {src_file} -> {e}")

            done += 1
            progress(done, total)

    elapsed = time.time() - start_time
    logline("-" * 70)
    if stats["cancelled"]:
        logline("SORTING CANCELLED - partial results below")
    logline("SUMMARY")
    logline(f"  Media files scanned:             {stats['scanned']}")
    logline(f"  Dated via EXIF/XMP/video metadata: {stats['exif']}")
    logline(f"  Dated via Google Takeout sidecar: {stats['takeout']}")
    logline(f"  Dated via filename timestamp:    {stats['filename']}")
    logline(f"  Dated via file's modified date:  {stats['mtime']}")
    logline(f"  Dated via folder name:           {stats['folder']}")
    logline(f"  No date found (sent to review):  {stats['no_date']}")
    logline(f"  Duplicate copies removed:        {stats['duplicates_removed']}")
    logline(f"  Errors:                          {stats['errors']}")
    logline(f"  Non-media files skipped:         {stats['skipped']}")
    logline(f"  Time elapsed:                    {elapsed:.1f}s")

    total_out = (stats['exif'] + stats['takeout'] + stats['filename']
                 + stats['mtime'] + stats['folder'] + stats['no_date']
                 + stats['duplicates_removed'])
    if total_out == stats['scanned'] - stats['errors']:
        logline("  VERIFICATION OK: file counts match.")
    else:
        logline("  WARNING: file counts do NOT match - please review the log!")

    if no_date_files:
        logline("", also_gui=False)
        logline("Files with no date (please review manually in _NoEXIF_review):", also_gui=False)
        for f in no_date_files:
            logline(f"   - {f}", also_gui=False)

    stats["skipped_files"] = skipped_files
    logfile.close()
    return stats, log_path
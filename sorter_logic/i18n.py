from PySide6.QtCore import QObject, Signal

LANGUAGES = {"en": "English", "pl": "Polski"}

TRANSLATIONS = {
    "en": {
        "sidebar.title": "SETUP STEPS",
        "sidebar.subtitle": "Photo & Video Sorter",
        "sidebar.welcome": "Welcome",
        "sidebar.source": "Source Folder",
        "sidebar.destination": "Destination",
        "sidebar.sorting": "Sorting",
        "sidebar.summary": "Summary",
        "sidebar.settings": "App Settings",

        "common.next": "Next",
        "common.back": "Back",
        "progress.done": "{pct}% — done",

        "welcome.title": "Welcome to Photo & Video Sorter",
        "welcome.intro": (
            "Sort your photos and videos into tidy Year / Year-Month folders - "
            "by the day each one was actually taken."
        ),
        "welcome.steps": (
            "<div style='line-height:150%'>"
            "<span style='color:{accent}'><b>&#10003; Your originals stay safe.</b></span><br>"
            "Files are only ever copied - never changed or deleted."
            "<br><br>"
            "<span style='color:{accent}'><b>&#10003; The real date wins.</b></span><br>"
            "The day a photo was taken, not the day it landed on your drive."
            "<br><br>"
            "<span style='color:{accent}'><b>&#10003; It reads many sources.</b></span><br>"
            "Photo metadata, the filename, Google Takeout, and the file's own date."
            "</div>"
        ),
        "welcome.get_started": "Get Started",

        "source.title": "Select Source Folders",
        "source.subtitle": "Choose one or more folders to scan and sort.",
        "source.choose_folder": "Choose Folder",
        "source.choose_row": "Choose…",
        "source.add_path": "+ Add another folder",
        "source.remove_tooltip": "Remove this folder",
        "source.row_placeholder": "No folder chosen yet",
        "source.no_folder": "No folder selected yet.",
        "source.selected_folder": (
            'Your selected folder is <span style="color: {color}; font-weight: bold;">'
            '"{name}"</span>. Click "Scan Folder" to continue.'
        ),
        "source.scan_folder": "Scan Folder",
        "source.scan_none_found": (
            "Scan completed. No media file(s) found in the selected folder. "
            "Please select a different folder."
        ),
        "source.scan_found": (
            'Scan completed. Found <span style="color: {color}; font-weight: bold;">'
            '{total}</span> media file(s) across '
            '<span style="color: {color}; font-weight: bold;">{folders}</span> folder(s).'
        ),
        "source.scan_selected": "Selected photos &amp; videos to sort: {size}",
        "source.scan_deselected": "Deselected types (won't be copied): {count} · {size}",
        "source.scan_other": ('Other files, no photo/video extension (won\'t be copied): '
                              '<span style="color: {color}; font-weight: bold;">{count}</span> · {size}'),
        "source.scan_grand": "Everything in these folders: {count} files · {size}",
        "source.file_types": "File Types...",
        "source.found_types": "File types found: {breakdown}",
        "source.found_types_hint": "Use \"File Types...\" to exclude any you don't want to move.",
        "source.type_disabled": "{ext} ({n}, off)",
        "source.type_enabled": "{ext} ({n})",

        "destination.title": "Destination and Options",
        "destination.subtitle": "Choose where sorted files will be saved.",
        "destination.collection_name": "Collection name:",
        "destination.choose_folder": "Choose destination folder",
        "destination.advanced": "Advanced settings",
        "destination.use_filename_date": "Use the timestamp embedded in the filename when no metadata date is found",
        "destination.use_filename_date_desc": "When a photo or video has no date in its metadata, the app reads the date written into the file name itself (e.g. IMG_20230514_143022.jpg or VID-2023-05-14). Turn off to ignore dates found in file names.",
        "destination.use_mtime": "Use file's last-modified date when no metadata or filename date is found",
        "destination.use_mtime_desc": "If neither the metadata nor the file name gives a date, fall back to the file's \"last modified\" time from the disk. Less reliable — copying or editing can change it — but better than leaving a file undated.",
        "destination.use_folder_date": "Use folder name as date when no other date source is found",
        "destination.use_folder_date_desc": "As a last resort, look for a date in the name of the folder a file sits in (e.g. \"2019 Holiday\" or \"2020-08\"). Handy for old collections already grouped into year or month folders.",
        "destination.rename_to_date": "Rename files to their detected date (e.g. 2023-05-14 14.30.22.jpg)",
        "destination.rename_to_date_desc": "On top of sorting into Year / Month folders, each file is renamed to its detected date and time (e.g. 2023-05-14 14.30.22.jpg). Off by default, so original file names are kept.",
        "destination.move": "Move files instead of copying them",
        "destination.move_desc": "Files are MOVED out of the source into the destination, so the source folder empties as they're sorted. Off by default — normally files are copied and your originals stay untouched. Duplicates are left in the source.",
        "destination.template": "Folder structure",
        "destination.template_desc": "How dated files are grouped into subfolders inside the collection.",
        "destination.template_year_month": "Year / Year-Month  (2023 / 2023-05)",
        "destination.template_year_slash_month": "Year / Month  (2023 / 05)",
        "destination.template_year": "Year only  (2023)",
        "destination.template_year_month_flat": "Year-Month  (2023-05)",
        "destination.space_ok": "Space check: {required} required, {available} available - plenty of room.",
        "destination.space_low": "Not enough space: {required} required, only {available} available on this drive.",
        "destination.preview_placeholder": "Destination path will appear here.",
        "destination.preview_with_name": "Your files will be organized like this:\n{dest}/{name}/YYYY/YYYY-MM/{file}",
        "destination.preview_no_name": "Your files will be organized like this:\n{dest}/YYYY/YYYY-MM/{file}",

        "filetypes.title": "File Types",
        "filetypes.subtitle": "Choose which file extensions to scan for.",
        "filetypes.photos": "Photos",
        "filetypes.videos": "Videos",
        "filetypes.select_all": "Select All",
        "filetypes.select_none": "Select None",
        "filetypes.confirm": "Confirm",

        "sorting.title": "Sorting Files",
        "sorting.subtitle": "Copying files into year/month folders. Originals are never modified or deleted.",
        "sorting.subtitle_move": "Moving files into year/month folders. Originals are removed from the source as they're sorted.",
        "sorting.summary": "Source: {src}<br>Destination: {dst}<br>Filename-timestamp fallback: {filename_fallback}<br>File-date fallback: {mtime_fallback}<br>Folder-name fallback: {fallback}<br>Rename to date: {rename}",
        "sorting.n_sources": "{n} folders",
        "sorting.fallback_on": "✅",
        "sorting.fallback_off": "<span style=\"color: #8A8D96;\">—</span>",
        "sorting.start": "Start Sorting",
        "sorting.progress": "{done} / {total} files — {pct}%",
        "sorting.current_file": "Copying: {name}",
        "sorting.current_file_move": "Moving: {name}",
        "sorting.complete": "Sorting complete.",
        "sorting.cancelled": "Sorting cancelled.",
        "sorting.cancelling": "Cancelling...",
        "sorting.failed": "Sorting failed - see the log file.",
        "sorting.fact_1": "Reading EXIF metadata for the real capture date…",
        "sorting.fact_2": "Copying only — your originals are never moved or changed…",
        "sorting.fact_2_move": "Moving files out of the source into dated folders…",
        "sorting.fact_3": "Sorting into Year / Year-Month folders…",
        "sorting.fact_4": "Verifying every copy with a checksum…",
        "sorting.fact_5": "No metadata date? Falling back to filename, then folder…",
        "sorting.fact_6": "Skipping duplicates so nothing is copied twice…",
        "sorting.fact_7": "Name clashes get a numeric suffix — never overwritten…",
        "sorting.cancel": "Cancel Sorting",
        "sorting.view_summary": "View Summary",
        "sorting.show_details": "▸ Show details",
        "sorting.hide_details": "▾ Hide details",

        "summary.title": "Sorting Complete",
        "summary.ok": "\u2713 Verification OK - all files accounted for.",
        "summary.warn": "! Warning: file counts do not match - check the log.",
        "summary.scanned": "Files Scanned",
        "summary.exif": "Dated via EXIF/Video",
        "summary.takeout": "Dated via Google Takeout",
        "summary.filename": "Dated via Filename",
        "summary.mtime": "Dated via File Date",
        "summary.folder": "Dated via Folder Name",
        "summary.nodate": "Needs Review (No Date)",
        "summary.errors": "Errors",
        "summary.skipped": "Non-Media Skipped",
        "summary.log_file": "Log file: {path}",
        "summary.duplicates_removed": "Removed {count} duplicate copy/copies (kept one of each).",
        "summary.view_skipped": "View files left behind ({count})",
        "summary.open_dest": "Open Folder",
        "summary.open_log": "Open Log File",
        "summary.start_new": "Start New Sort",
        "summary.review_duplicates": "Review Duplicates ({count})",

        "duplicates.title": "Duplicate Files",
        "duplicates.subtitle": "Found {count} duplicate copy/copies across {sets} set(s). These are byte-for-byte identical files in your sorted result. One copy is kept from each set; the rest can be deleted. Your original files are never touched.",
        "duplicates.set_header": "Set {index} - {count} identical copies",
        "duplicates.keep": "KEEP",
        "duplicates.duplicate": "DUPLICATE",
        "duplicates.delete_all": "Delete All Duplicates",
        "duplicates.done": "Done - deleted {count} duplicate file(s).",

        "settings.title": "App Settings",
        "settings.language": "Language",
        "settings.close": "Close",
        "settings.note": "The live sorting log stays in English regardless of this setting.",

        "skipped.title": "Files Left Behind",
        "skipped.subtitle": ("{count} non-media file(s) ({size}) stayed in your source folders - they "
                             "were not copied. If you need them, move them yourself before deleting the "
                             "originals so nothing is lost."),
        "skipped.reveal": "Open First Folder",

        "compare.title": "Compare Folders",
        "compare.subtitle": "Add any number of folders on each side, then compare what they hold.",
        "compare.group_a": "Side A folders",
        "compare.group_b": "Side B folders",
        "compare.add": "+ Add folder",
        "compare.choose": "Choose…",
        "compare.compare": "Compare",
        "compare.scanning": "Scanning…",
        "compare.pick_both": "Add at least one folder on each side first.",
        "compare.side_a": "Side A",
        "compare.side_b": "Side B",
        "compare.side_media": "Photos &amp; videos: {count} · {size}",
        "compare.side_other": "Other files: {count} · {size}",
        "compare.side_total": "Total: {count} files · {size}",
        "compare.verdict_more": "Side {more} has {n} more photos &amp; videos than side {less}.",
        "compare.verdict_same": "✓ Both sides hold the same number of photos &amp; videos ({count}).",
        "compare.tooltip": "Compare folders",

        "dupfinder.title": "Find Duplicates",
        "dupfinder.subtitle": "Scan a folder for identical photos and videos, then delete the redundant copies (one is kept from each set).",
        "dupfinder.choose": "Choose…",
        "dupfinder.scan": "Scan",
        "dupfinder.scanning": "Scanning…",
        "dupfinder.progress": "Checking {done} / {total} files — {pct}%",
        "dupfinder.generating": "Generating preview… this can take a while, please wait.",
        "dupfinder.log_walk": "Scanning folder: {name}",
        "dupfinder.log_read": "Reading: {name}",
        "dupfinder.log_building": "Building preview thumbnails…",
        "dupfinder.fact_1": "Checking fingerprints…",
        "dupfinder.fact_2": "Reading just the first and last 256 KB of each file…",
        "dupfinder.fact_3": "Grouping files by size first — no reading needed…",
        "dupfinder.fact_4": "Only files with the exact same size can be duplicates…",
        "dupfinder.fact_5": "Same size + same head + same tail = identical file…",
        "dupfinder.fact_6": "Hashing content with SHA-256…",
        "dupfinder.fact_7": "Comparing by content, not by file name…",
        "dupfinder.browse": "Browse sets ({count})",
        "review.title": "Review duplicate sets",
        "review.generating": "Generating preview…",
        "review.gen_count": "{done} / {total} thumbnails",
        "review.deleting": "Moving to Trash… {pct}%",
        "review.subtitle": "Tick the copies you want to remove — at least one file is always kept in each set. Files go to the Trash, so you can restore them.",
        "review.page": "Page {page} / {pages}",
        "review.prev": "‹ Previous",
        "review.next": "Next ›",
        "review.delete_checkbox": "Delete",
        "review.delete_selected": "Delete selected ({count})",
        "review.confirm": "Move {count} selected file(s) to the Trash? You can restore them from the Trash.",
        "review.confirm_delete": "Move to Trash",
        "review.confirm_cancel": "Cancel",
        "review.deleted": "Moved {count} file(s) to the Trash.",
        "review.none_selected": "Nothing is selected for deletion.",
        "review.min_keep": "Keep at least one file in each set.",
        "dupfinder.pick_first": "Pick a folder first.",
        "dupfinder.none": "✓ No duplicates found - every file in this folder is unique.",
        "dupfinder.found": ('Found <span style="color: {color}; font-weight: bold;">{count}</span> '
                            'duplicate file(s) across {sets} set(s).'),
        "dupfinder.showing": "Showing the first {shown} of {total} sets - delete still covers all of them.",
        "dupfinder.set_header": "Set {index} — {count} identical copies",
        "dupfinder.keep": "KEEP",
        "dupfinder.duplicate": "DUPLICATE",
        "dupfinder.delete": "Delete {count} duplicate(s)",
        "dupfinder.confirm_title": "Delete duplicates?",
        "dupfinder.confirm": "Move {count} duplicate file(s) to the Trash? One copy is kept from each set. You can restore them from the Trash.",
        "dupfinder.deleted": "✓ Moved {count} duplicate file(s) to the Trash.",
        "dupfinder.tooltip": "Find duplicate photos",
    },
    "pl": {
        "sidebar.title": "KROKI",
        "sidebar.subtitle": "Photo & Video Sorter",
        "sidebar.welcome": "Powitanie",
        "sidebar.source": "Folder \u017ar\u00f3d\u0142owy",
        "sidebar.destination": "Miejsce docelowe",
        "sidebar.sorting": "Sortowanie",
        "sidebar.summary": "Podsumowanie",
        "sidebar.settings": "Ustawienia aplikacji",

        "common.next": "Dalej",
        "common.back": "Wstecz",
        "progress.done": "{pct}% — ukończono",

        "welcome.title": "Witamy w Photo & Video Sorter",
        "welcome.intro": (
            "Uporz\u0105dkuj swoje zdj\u0119cia i filmy w foldery Rok / Rok-Miesi\u0105c - "
            "wed\u0142ug dnia, w kt\u00f3rym naprawd\u0119 powsta\u0142y."
        ),
        "welcome.steps": (
            "<div style='line-height:150%'>"
            "<span style='color:{accent}'><b>&#10003; Twoje orygina\u0142y s\u0105 bezpieczne.</b></span><br>"
            "Pliki s\u0105 tylko kopiowane - nigdy nie zmieniane ani usuwane."
            "<br><br>"
            "<span style='color:{accent}'><b>&#10003; Liczy si\u0119 prawdziwa data.</b></span><br>"
            "Dzie\u0144 wykonania zdj\u0119cia, a nie moment skopiowania na dysk."
            "<br><br>"
            "<span style='color:{accent}'><b>&#10003; Rozpoznaje r\u00f3\u017cne \u017ar\u00f3d\u0142a.</b></span><br>"
            "Metadane zdj\u0119cia, nazw\u0119 pliku, Google Takeout i dat\u0119 pliku."
            "</div>"
        ),
        "welcome.get_started": "Rozpocznij",

        "source.title": "Wybierz foldery \u017ar\u00f3d\u0142owe",
        "source.subtitle": "Wybierz jeden lub wi\u0119cej folder\u00f3w do przeskanowania i posortowania.",
        "source.choose_folder": "Wybierz folder",
        "source.choose_row": "Wybierz\u2026",
        "source.add_path": "+ Dodaj kolejny folder",
        "source.remove_tooltip": "Usu\u0144 ten folder",
        "source.row_placeholder": "Nie wybrano folderu",
        "source.no_folder": "Nie wybrano jeszcze folderu.",
        "source.selected_folder": (
            'Wybrany folder to <span style="color: {color}; font-weight: bold;">'
            '"{name}"</span>. Kliknij "Skanuj folder", aby kontynuowa\u0107.'
        ),
        "source.scan_folder": "Skanuj folder",
        "source.scan_none_found": (
            "Skanowanie zako\u0144czone. Nie znaleziono plik\u00f3w multimedialnych w "
            "wybranym folderze. Wybierz inny folder."
        ),
        "source.scan_found": (
            'Skanowanie zako\u0144czone. Znaleziono <span style="color: {color}; font-weight: bold;">'
            '{total}</span> plik(\u00f3w) multimedialnych w '
            '<span style="color: {color}; font-weight: bold;">{folders}</span> folderze/folderach.'
        ),
        "source.scan_media": "Zdj\u0119cia i filmy do posortowania: {size}",
        "source.scan_other": ('Inne pliki (nie zostan\u0105 skopiowane): '
                              '<span style="color: {color}; font-weight: bold;">{count}</span> \u00b7 {size}'),
        "source.scan_grand": "Wszystko w tych folderach: {count} plik\u00f3w \u00b7 {size}",
        "source.file_types": "Typy plik\u00f3w...",
        "source.found_types": "Znalezione typy plik\u00f3w: {breakdown}",
        "source.found_types_hint": "U\u017cyj \"Typy plik\u00f3w...\", aby wykluczy\u0107 te, kt\u00f3rych nie chcesz przenosi\u0107.",
        "source.type_disabled": "{ext} ({n}, wy\u0142.)",
        "source.type_enabled": "{ext} ({n})",

        "destination.title": "Miejsce docelowe i opcje",
        "destination.subtitle": "Wybierz, gdzie zostan\u0105 zapisane posortowane pliki.",
        "destination.collection_name": "Nazwa kolekcji:",
        "destination.choose_folder": "Wybierz folder docelowy",
        "destination.advanced": "Ustawienia zaawansowane",
        "destination.use_filename_date": "U\u017cyj znacznika czasu z nazwy pliku, gdy brak daty w metadanych",
        "destination.use_filename_date_desc": "Gdy zdj\u0119cie lub film nie ma daty w metadanych, aplikacja odczytuje dat\u0119 zapisan\u0105 w samej nazwie pliku (np. IMG_20230514_143022.jpg lub VID-2023-05-14). Wy\u0142\u0105cz, aby ignorowa\u0107 daty z nazw plik\u00f3w.",
        "destination.use_mtime": "U\u017cyj daty modyfikacji pliku, gdy brak daty w metadanych lub nazwie pliku",
        "destination.use_mtime_desc": "Je\u015bli ani metadane, ani nazwa pliku nie daj\u0105 daty, u\u017cyj daty \u201eostatniej modyfikacji\u201d pliku z dysku. Mniej pewne \u2014 kopiowanie lub edycja mo\u017ce j\u0105 zmieni\u0107 \u2014 ale lepsze ni\u017c brak daty.",
        "destination.use_folder_date": "U\u017cyj nazwy folderu jako daty, gdy brak innego \u017ar\u00f3d\u0142a daty",
        "destination.use_folder_date_desc": "W ostateczno\u015bci szukaj daty w nazwie folderu, w kt\u00f3rym le\u017cy plik (np. \u201e2019 Wakacje\u201d lub \u201e2020-08\u201d). Przydatne dla starych zbior\u00f3w ju\u017c pogrupowanych w foldery lat lub miesi\u0119cy.",
        "destination.rename_to_date": "Zmie\u0144 nazwy plik\u00f3w na wykryt\u0105 dat\u0119 (np. 2023-05-14 14.30.22.jpg)",
        "destination.rename_to_date_desc": "Opr\u00f3cz sortowania do folder\u00f3w Rok / Miesi\u0105c, ka\u017cdy plik jest przemianowany na wykryt\u0105 dat\u0119 i godzin\u0119 (np. 2023-05-14 14.30.22.jpg). Domy\u015blnie wy\u0142\u0105czone, wi\u0119c oryginalne nazwy plik\u00f3w s\u0105 zachowane.",
        "destination.move": "Przenie\u015b pliki zamiast je kopiowa\u0107",
        "destination.move_desc": "Pliki s\u0105 PRZENOSZONE ze \u017ar\u00f3d\u0142a do miejsca docelowego, wi\u0119c folder \u017ar\u00f3d\u0142owy pustoszeje w trakcie sortowania. Domy\u015blnie wy\u0142\u0105czone \u2014 zwykle pliki s\u0105 kopiowane, a orygina\u0142y pozostaj\u0105 nietkni\u0119te. Duplikaty zostaj\u0105 w \u017ar\u00f3dle.",
        "destination.template": "Struktura folder\u00f3w",
        "destination.template_desc": "Jak datowane pliki s\u0105 grupowane w podfoldery wewn\u0105trz kolekcji.",
        "destination.template_year_month": "Rok / Rok-Miesi\u0105c  (2023 / 2023-05)",
        "destination.template_year_slash_month": "Rok / Miesi\u0105c  (2023 / 05)",
        "destination.template_year": "Tylko Rok  (2023)",
        "destination.template_year_month_flat": "Rok-Miesi\u0105c  (2023-05)",
        "destination.space_ok": "Miejsce na dysku: potrzeba {required}, dost\u0119pne {available} - wystarczaj\u0105co.",
        "destination.space_low": "Za ma\u0142o miejsca: potrzeba {required}, dost\u0119pne tylko {available} na tym dysku.",
        "destination.preview_placeholder": "Tutaj pojawi si\u0119 \u015bcie\u017cka docelowa.",
        "destination.preview_with_name": "Twoje pliki zostan\u0105 zorganizowane w ten spos\u00f3b:\n{dest}/{name}/RRRR/RRRR-MM/{file}",
        "destination.preview_no_name": "Twoje pliki zostan\u0105 zorganizowane w ten spos\u00f3b:\n{dest}/RRRR/RRRR-MM/{file}",

        "filetypes.title": "Typy plik\u00f3w",
        "filetypes.subtitle": "Wybierz, kt\u00f3rych rozszerze\u0144 plik\u00f3w szuka\u0107 podczas skanowania.",
        "filetypes.photos": "Zdj\u0119cia",
        "filetypes.videos": "Filmy",
        "filetypes.select_all": "Zaznacz wszystko",
        "filetypes.select_none": "Odznacz wszystko",
        "filetypes.confirm": "Zatwierd\u017a",

        "sorting.title": "Sortowanie plik\u00f3w",
        "sorting.subtitle": "Kopiowanie plik\u00f3w do folder\u00f3w rok/miesi\u0105c. Orygina\u0142y nigdy nie s\u0105 modyfikowane ani usuwane.",
        "sorting.subtitle_move": "Przenoszenie plik\u00f3w do folder\u00f3w rok/miesi\u0105c. Orygina\u0142y s\u0105 usuwane ze \u017ar\u00f3d\u0142a w trakcie sortowania.",
        "sorting.summary": "\u0179r\u00f3d\u0142o: {src}<br>Cel: {dst}<br>Data z nazwy pliku: {filename_fallback}<br>Data modyfikacji pliku: {mtime_fallback}<br>Daty z nazwy folderu: {fallback}<br>Zmiana nazwy na dat\u0119: {rename}",
        "sorting.n_sources": "{n} folder\u00f3w",
        "sorting.fallback_on": "\u2705",
        "sorting.fallback_off": "<span style=\"color: #8A8D96;\">\u2014</span>",
        "sorting.start": "Rozpocznij sortowanie",
        "sorting.progress": "{done} / {total} plik\u00f3w \u2014 {pct}%",
        "sorting.current_file": "Kopiowanie: {name}",
        "sorting.current_file_move": "Przenoszenie: {name}",
        "sorting.complete": "Sortowanie zako\u0144czone.",
        "sorting.cancelled": "Sortowanie anulowane.",
        "sorting.cancelling": "Anulowanie...",
        "sorting.failed": "Sortowanie nie powiod\u0142o si\u0119 - zobacz plik logu.",
        "sorting.fact_1": "Odczytuj\u0119 metadane EXIF, aby pozna\u0107 prawdziw\u0105 dat\u0119 zdj\u0119cia\u2026",
        "sorting.fact_2": "Tylko kopiuj\u0119 \u2014 orygina\u0142y nie s\u0105 przenoszone ani zmieniane\u2026",
        "sorting.fact_2_move": "Przenosz\u0119 pliki ze \u017ar\u00f3d\u0142a do datowanych folder\u00f3w\u2026",
        "sorting.fact_3": "Sortuj\u0119 do folder\u00f3w Rok / Rok-Miesi\u0105c\u2026",
        "sorting.fact_4": "Weryfikuj\u0119 ka\u017cd\u0105 kopi\u0119 sum\u0105 kontroln\u0105\u2026",
        "sorting.fact_5": "Brak daty w metadanych? Si\u0119gam do nazwy pliku, potem folderu\u2026",
        "sorting.fact_6": "Pomijam duplikaty, aby nic nie skopiowa\u0107 dwa razy\u2026",
        "sorting.fact_7": "Konflikty nazw dostaj\u0105 numer \u2014 nic nie jest nadpisywane\u2026",
        "sorting.cancel": "Anuluj sortowanie",
        "sorting.view_summary": "Zobacz podsumowanie",
        "sorting.show_details": "▸ Pokaż szczegóły",
        "sorting.hide_details": "▾ Ukryj szczegóły",

        "summary.title": "Sortowanie zako\u0144czone",
        "summary.ok": "\u2713 Weryfikacja OK - wszystkie pliki uwzgl\u0119dnione.",
        "summary.warn": "! Uwaga: liczby plik\u00f3w si\u0119 nie zgadzaj\u0105 - sprawd\u017a log.",
        "summary.scanned": "Przeskanowane pliki",
        "summary.exif": "Data z EXIF/wideo",
        "summary.takeout": "Data z Google Takeout",
        "summary.filename": "Data z nazwy pliku",
        "summary.mtime": "Data z pliku",
        "summary.folder": "Data z nazwy folderu",
        "summary.nodate": "Do przejrzenia (brak daty)",
        "summary.errors": "B\u0142\u0119dy",
        "summary.skipped": "Pomini\u0119te pliki",
        "summary.log_file": "Plik logu: {path}",
        "summary.duplicates_removed": "Usuni\u0119to {count} zduplikowanych kopii (zostawiono po jednej).",
        "summary.view_skipped": "Zobacz pozostawione pliki ({count})",
        "summary.open_dest": "Otw\u00f3rz folder",
        "summary.open_log": "Otw\u00f3rz log",
        "summary.start_new": "Nowe sortowanie",
        "summary.review_duplicates": "Przejrzyj duplikaty ({count})",

        "duplicates.title": "Zduplikowane pliki",
        "duplicates.subtitle": "Znaleziono {count} zduplikowan\u0105 kopi\u0119/kopii w {sets} zestawie/zestawach. To pliki identyczne co do bajta w posortowanym wyniku. Z ka\u017cdego zestawu jedna kopia zostaje zachowana; reszt\u0119 mo\u017cna usun\u0105\u0107. Twoje oryginalne pliki nigdy nie s\u0105 ruszane.",
        "duplicates.set_header": "Zestaw {index} - {count} identycznych kopii",
        "duplicates.keep": "ZOSTAJE",
        "duplicates.duplicate": "DUPLIKAT",
        "duplicates.delete_all": "Usu\u0144 wszystkie duplikaty",
        "duplicates.done": "Gotowe - usuni\u0119to {count} zduplikowanych plik\u00f3w.",

        "settings.title": "Ustawienia aplikacji",
        "settings.language": "J\u0119zyk",
        "settings.close": "Zamknij",
        "settings.note": "Log sortowania na \u017cywo zawsze pozostaje w j\u0119zyku angielskim.",

        "skipped.title": "Pozostawione pliki",
        "skipped.subtitle": ("{count} plik(\u00f3w) nie-multimedialnych ({size}) zosta\u0142o w folderach \u017ar\u00f3d\u0142owych - "
                             "nie zosta\u0142y skopiowane. Je\u015bli ich potrzebujesz, przenie\u015b je samodzielnie przed "
                             "usuni\u0119ciem orygina\u0142\u00f3w, \u017ceby nic nie zgin\u0119\u0142o."),
        "skipped.reveal": "Otw\u00f3rz pierwszy folder",

        "compare.title": "Por\u00f3wnaj foldery",
        "compare.subtitle": "Dodaj dowoln\u0105 liczb\u0119 folder\u00f3w po ka\u017cdej stronie i por\u00f3wnaj ich zawarto\u015b\u0107.",
        "compare.group_a": "Foldery \u2014 strona A",
        "compare.group_b": "Foldery \u2014 strona B",
        "compare.add": "+ Dodaj folder",
        "compare.choose": "Wybierz\u2026",
        "compare.compare": "Por\u00f3wnaj",
        "compare.scanning": "Skanowanie\u2026",
        "compare.pick_both": "Najpierw dodaj po jednym folderze z ka\u017cdej strony.",
        "compare.side_a": "Strona A",
        "compare.side_b": "Strona B",
        "compare.side_media": "Zdj\u0119cia i filmy: {count} \u00b7 {size}",
        "compare.side_other": "Inne pliki: {count} \u00b7 {size}",
        "compare.side_total": "Razem: {count} plik\u00f3w \u00b7 {size}",
        "compare.verdict_more": "Strona {more} ma o {n} zdj\u0119\u0107 i film\u00f3w wi\u0119cej ni\u017c strona {less}.",
        "compare.verdict_same": "\u2713 Obie strony maj\u0105 tyle samo zdj\u0119\u0107 i film\u00f3w ({count}).",
        "compare.tooltip": "Por\u00f3wnaj foldery",

        "dupfinder.title": "Znajd\u017a duplikaty",
        "dupfinder.subtitle": "Przeskanuj folder w poszukiwaniu identycznych zdj\u0119\u0107 i film\u00f3w, a potem usu\u0144 zb\u0119dne kopie (z ka\u017cdego zestawu jedna zostaje).",
        "dupfinder.choose": "Wybierz\u2026",
        "dupfinder.scan": "Skanuj",
        "dupfinder.scanning": "Skanowanie\u2026",
        "dupfinder.progress": "Sprawdzanie {done} / {total} plik\u00f3w \u2014 {pct}%",
        "dupfinder.generating": "Generowanie podgl\u0105du\u2026 to mo\u017ce chwil\u0119 potrwa\u0107, poczekaj.",
        "dupfinder.log_walk": "Skanowanie folderu: {name}",
        "dupfinder.log_read": "Odczyt: {name}",
        "dupfinder.log_building": "Tworzenie miniatur podgl\u0105du\u2026",
        "dupfinder.fact_1": "Sprawdzanie fingerprinta\u2026",
        "dupfinder.fact_2": "Odczytuj\u0119 tylko pierwsze i ostatnie 256 KB ka\u017cdego pliku\u2026",
        "dupfinder.fact_3": "Najpierw grupuj\u0119 pliki po rozmiarze \u2014 bez odczytu\u2026",
        "dupfinder.fact_4": "Tylko pliki o identycznym rozmiarze mog\u0105 by\u0107 duplikatami\u2026",
        "dupfinder.fact_5": "Ten sam rozmiar + pocz\u0105tek + koniec = identyczny plik\u2026",
        "dupfinder.fact_6": "Licz\u0119 skr\u00f3t tre\u015bci SHA-256\u2026",
        "dupfinder.fact_7": "Por\u00f3wnuj\u0119 po tre\u015bci, nie po nazwie pliku\u2026",
        "dupfinder.browse": "Przegl\u0105daj zestawy ({count})",
        "review.title": "Przegl\u0105d zestaw\u00f3w duplikat\u00f3w",
        "review.generating": "Generowanie podgl\u0105du\u2026",
        "review.gen_count": "{done} / {total} miniatur",
        "review.deleting": "Przenoszenie do Kosza\u2026 {pct}%",
        "review.subtitle": "Zaznacz kopie, kt\u00f3re chcesz usun\u0105\u0107 \u2014 w ka\u017cdym zestawie zawsze zostaje co najmniej jeden plik. Pliki trafiaj\u0105 do Kosza, wi\u0119c mo\u017cesz je przywr\u00f3ci\u0107.",
        "review.page": "Strona {page} / {pages}",
        "review.prev": "\u2039 Poprzednia",
        "review.next": "Nast\u0119pna \u203a",
        "review.delete_checkbox": "Usu\u0144",
        "review.delete_selected": "Usu\u0144 zaznaczone ({count})",
        "review.confirm": "Przenie\u015b\u0107 {count} zaznaczonych plik\u00f3w do Kosza? Mo\u017cesz je przywr\u00f3ci\u0107 z Kosza.",
        "review.confirm_delete": "Przenie\u015b do Kosza",
        "review.confirm_cancel": "Anuluj",
        "review.deleted": "Przeniesiono {count} plik(\u00f3w) do Kosza.",
        "review.none_selected": "Nie zaznaczono nic do usuni\u0119cia.",
        "review.min_keep": "W ka\u017cdym zestawie musi zosta\u0107 co najmniej jeden plik.",
        "dupfinder.pick_first": "Najpierw wybierz folder.",
        "dupfinder.none": "\u2713 Nie znaleziono duplikat\u00f3w - ka\u017cdy plik w tym folderze jest unikalny.",
        "dupfinder.found": ('Znaleziono <span style="color: {color}; font-weight: bold;">{count}</span> '
                            'zduplikowanych plik\u00f3w w {sets} zestawie/zestawach.'),
        "dupfinder.showing": "Pokazuj\u0119 pierwsze {shown} z {total} zestaw\u00f3w - usuwanie i tak obejmuje wszystkie.",
        "dupfinder.set_header": "Zestaw {index} \u2014 {count} identycznych kopii",
        "dupfinder.keep": "ZOSTAJE",
        "dupfinder.duplicate": "DUPLIKAT",
        "dupfinder.delete": "Usu\u0144 {count} duplikat(\u00f3w)",
        "dupfinder.confirm_title": "Usun\u0105\u0107 duplikaty?",
        "dupfinder.confirm": "Przenie\u015b\u0107 {count} zduplikowanych plik\u00f3w do Kosza? Z ka\u017cdego zestawu jedna kopia zostaje. Mo\u017cesz je przywr\u00f3ci\u0107 z Kosza.",
        "dupfinder.deleted": "\u2713 Przeniesiono {count} zduplikowanych plik\u00f3w do Kosza.",
        "dupfinder.tooltip": "Znajd\u017a duplikaty zdj\u0119\u0107",
    },
}


class Translator(QObject):
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._lang = "en"

    def set_language(self, code, _emit=True):
        if code not in TRANSLATIONS or code == self._lang:
            return
        self._lang = code
        if _emit:
            self.language_changed.emit(code)

    def language(self):
        return self._lang

    def t(self, key, **kwargs):
        text = TRANSLATIONS.get(self._lang, {}).get(key)
        if text is None:
            text = TRANSLATIONS["en"].get(key, key)
        return text.format(**kwargs) if kwargs else text


translator = Translator()

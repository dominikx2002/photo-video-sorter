from PySide6.QtCore import QObject, Signal

LANGUAGES = {"en": "English", "pl": "Polski"}

TRANSLATIONS = {
    "en": {
        "sidebar.title": "SETUP STEPS",
        "sidebar.subtitle": "Photo & Video Sorter",
        "sidebar.welcome": "Welcome",
        "sidebar.source": "Scan Source Folder",
        "sidebar.destination": "Destination",
        "sidebar.sorting": "Sorting",
        "sidebar.summary": "Summary",
        "sidebar.settings": "App Settings",

        "common.next": "Next",
        "common.back": "Back",

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
        "source.scan_duplicates": (
            '<span style="color: {color}; font-weight: bold;">{count}</span> '
            'of them are duplicates and will be skipped (only unique files are copied).'
        ),
        "source.file_types": "File Types...",
        "source.found_types": "File types found: {breakdown}",
        "source.found_types_hint": "Use \"File Types...\" to exclude any you don't want to move.",
        "source.type_disabled": "{ext} ({n}, off)",
        "source.type_enabled": "{ext} ({n})",

        "destination.title": "Destination and Options",
        "destination.subtitle": "Choose where sorted files will be saved.",
        "destination.collection_name": "Collection name:",
        "destination.choose_folder": "Choose destination folder",
        "destination.use_filename_date": "Use the timestamp embedded in the filename when no metadata date is found",
        "destination.use_mtime": "Use file's last-modified date when no metadata or filename date is found",
        "destination.use_folder_date": "Use folder name as date when no other date source is found",
        "destination.rename_to_date": "Rename files to their detected date (e.g. 2023-05-14 14.30.22.jpg)",
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

        "sorting.title": "Sorting Files",
        "sorting.subtitle": "Copying files into year/month folders. Originals are never modified or deleted.",
        "sorting.summary": "Source: {src}\nDestination: {dst}\nFilename-timestamp fallback: {filename_fallback}\nFile-date fallback: {mtime_fallback}\nFolder-name fallback: {fallback}\nRename to date: {rename}",
        "sorting.n_sources": "{n} folders",
        "sorting.fallback_on": "on",
        "sorting.fallback_off": "off",
        "sorting.start": "Start Sorting",
        "sorting.progress": "{done} / {total} files processed ({pct}%)",
        "sorting.current_file": "Copying: {name}",
        "sorting.complete": "Sorting complete.",
        "sorting.cancelled": "Sorting cancelled.",
        "sorting.cancelling": "Cancelling...",
        "sorting.failed": "Sorting failed - see log above.",
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

        "compare.title": "Compare Folders",
        "compare.subtitle": "Pick two folders and see how many photos and videos each one holds.",
        "compare.folder_a": "Folder A:",
        "compare.folder_b": "Folder B:",
        "compare.choose": "Choose…",
        "compare.compare": "Compare",
        "compare.scanning": "Scanning…",
        "compare.pick_both": "Pick both folders first.",
        "compare.count": "<b>{name}</b>: {count} media file(s)",
        "compare.same": "✓ Both folders hold the same number of media files.",
        "compare.diff": "{more} has {n} more media file(s) than {less}.",
        "compare.tooltip": "Compare two folders",

        "dupfinder.title": "Find Duplicates",
        "dupfinder.subtitle": "Scan a folder for identical photos and videos, then delete the redundant copies (one is kept from each set).",
        "dupfinder.choose": "Choose…",
        "dupfinder.scan": "Scan",
        "dupfinder.scanning": "Scanning…",
        "dupfinder.progress": "Checking {done} / {total} files…",
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
        "dupfinder.confirm": "Permanently delete {count} duplicate file(s)? One copy is kept from each set. This cannot be undone.",
        "dupfinder.deleted": "✓ Deleted {count} duplicate file(s).",
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
        "source.scan_duplicates": (
            'w tym <span style="color: {color}; font-weight: bold;">{count}</span> '
            'duplikat\u00f3w \u2013 zostan\u0105 pomini\u0119te (kopiowane s\u0105 tylko unikalne pliki).'
        ),
        "source.file_types": "Typy plik\u00f3w...",
        "source.found_types": "Znalezione typy plik\u00f3w: {breakdown}",
        "source.found_types_hint": "U\u017cyj \"Typy plik\u00f3w...\", aby wykluczy\u0107 te, kt\u00f3rych nie chcesz przenosi\u0107.",
        "source.type_disabled": "{ext} ({n}, wy\u0142.)",
        "source.type_enabled": "{ext} ({n})",

        "destination.title": "Miejsce docelowe i opcje",
        "destination.subtitle": "Wybierz, gdzie zostan\u0105 zapisane posortowane pliki.",
        "destination.collection_name": "Nazwa kolekcji:",
        "destination.choose_folder": "Wybierz folder docelowy",
        "destination.use_filename_date": "U\u017cyj znacznika czasu z nazwy pliku, gdy brak daty w metadanych",
        "destination.use_mtime": "U\u017cyj daty modyfikacji pliku, gdy brak daty w metadanych lub nazwie pliku",
        "destination.use_folder_date": "U\u017cyj nazwy folderu jako daty, gdy brak innego \u017ar\u00f3d\u0142a daty",
        "destination.rename_to_date": "Zmie\u0144 nazwy plik\u00f3w na wykryt\u0105 dat\u0119 (np. 2023-05-14 14.30.22.jpg)",
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

        "sorting.title": "Sortowanie plik\u00f3w",
        "sorting.subtitle": "Kopiowanie plik\u00f3w do folder\u00f3w rok/miesi\u0105c. Orygina\u0142y nigdy nie s\u0105 modyfikowane ani usuwane.",
        "sorting.summary": "\u0179r\u00f3d\u0142o: {src}\nCel: {dst}\nData z nazwy pliku: {filename_fallback}\nData modyfikacji pliku: {mtime_fallback}\nDaty z nazwy folderu: {fallback}\nZmiana nazwy na dat\u0119: {rename}",
        "sorting.n_sources": "{n} folder\u00f3w",
        "sorting.fallback_on": "w\u0142\u0105czone",
        "sorting.fallback_off": "wy\u0142\u0105czone",
        "sorting.start": "Rozpocznij sortowanie",
        "sorting.progress": "{done} / {total} plik\u00f3w przetworzonych ({pct}%)",
        "sorting.current_file": "Kopiowanie: {name}",
        "sorting.complete": "Sortowanie zako\u0144czone.",
        "sorting.cancelled": "Sortowanie anulowane.",
        "sorting.cancelling": "Anulowanie...",
        "sorting.failed": "Sortowanie nie powiod\u0142o si\u0119 - zobacz log powy\u017cej.",
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

        "compare.title": "Por\u00f3wnaj foldery",
        "compare.subtitle": "Wybierz dwa foldery i sprawd\u017a, ile zdj\u0119\u0107 i film\u00f3w zawiera ka\u017cdy z nich.",
        "compare.folder_a": "Folder A:",
        "compare.folder_b": "Folder B:",
        "compare.choose": "Wybierz\u2026",
        "compare.compare": "Por\u00f3wnaj",
        "compare.scanning": "Skanowanie\u2026",
        "compare.pick_both": "Najpierw wybierz oba foldery.",
        "compare.count": "<b>{name}</b>: {count} plik(\u00f3w) multimedialnych",
        "compare.same": "\u2713 Oba foldery maj\u0105 tyle samo plik\u00f3w multimedialnych.",
        "compare.diff": "{more} ma o {n} plik(\u00f3w) multimedialnych wi\u0119cej ni\u017c {less}.",
        "compare.tooltip": "Por\u00f3wnaj dwa foldery",

        "dupfinder.title": "Znajd\u017a duplikaty",
        "dupfinder.subtitle": "Przeskanuj folder w poszukiwaniu identycznych zdj\u0119\u0107 i film\u00f3w, a potem usu\u0144 zb\u0119dne kopie (z ka\u017cdego zestawu jedna zostaje).",
        "dupfinder.choose": "Wybierz\u2026",
        "dupfinder.scan": "Skanuj",
        "dupfinder.scanning": "Skanowanie\u2026",
        "dupfinder.progress": "Sprawdzanie {done} / {total} plik\u00f3w\u2026",
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
        "dupfinder.confirm": "Trwale usun\u0105\u0107 {count} zduplikowanych plik\u00f3w? Z ka\u017cdego zestawu jedna kopia zostaje. Tego nie mo\u017cna cofn\u0105\u0107.",
        "dupfinder.deleted": "\u2713 Usuni\u0119to {count} zduplikowanych plik\u00f3w.",
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

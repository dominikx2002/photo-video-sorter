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
            "This wizard organizes your photos and videos into a clean Year / "
            "Year-Month folder structure, using the date each file was actually "
            "taken - not the date it happened to be copied."
        ),
        "welcome.steps": (
            "Here's what happens next:\n\n"
            "1. Scan Source Folder - point the app at a folder and it finds every "
            "photo and video inside it, including subfolders.\n"
            "2. Destination and Options - choose where the sorted copies go, and "
            "give this collection a name.\n"
            "3. Sorting - the app copies every file into dated folders. Your "
            "originals are never modified or deleted.\n"
            "4. Summary - see exactly what happened, and open the results."
        ),
        "welcome.get_started": "Get Started",

        "source.title": "Select Source Folder",
        "source.subtitle": "Choose the folder to scan...",
        "source.choose_folder": "Choose Folder",
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
        "source.file_types": "File Types...",

        "destination.title": "Destination and Options",
        "destination.subtitle": "Choose where sorted files will be saved.",
        "destination.collection_name": "Collection name:",
        "destination.choose_folder": "Choose destination folder",
        "destination.use_filename_date": "Use the timestamp embedded in the filename when no metadata date is found",
        "destination.use_mtime": "Use file's last-modified date when no metadata or filename date is found",
        "destination.use_folder_date": "Use folder name as date when no other date source is found",
        "destination.rename_to_date": "Rename files to their detected date (e.g. 2023-05-14 14.30.22.jpg)",
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
        "sorting.fallback_on": "on",
        "sorting.fallback_off": "off",
        "sorting.start": "Start Sorting",
        "sorting.progress": "{done} / {total} files processed ({pct}%)",
        "sorting.complete": "Sorting complete.",
        "sorting.cancelled": "Sorting cancelled.",
        "sorting.cancelling": "Cancelling...",
        "sorting.failed": "Sorting failed - see log above.",
        "sorting.cancel": "Cancel Sorting",
        "sorting.view_summary": "View Summary",

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
        "summary.open_dest": "Open Destination Folder",
        "summary.open_log": "Open Log File",
        "summary.start_new": "Start New Sort",

        "settings.title": "App Settings",
        "settings.language": "Language",
        "settings.close": "Close",
        "settings.note": "The live sorting log stays in English regardless of this setting.",
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
            "Ten kreator porz\u0105dkuje Twoje zdj\u0119cia i filmy w przejrzyst\u0105 "
            "struktur\u0119 folder\u00f3w Rok / Rok-Miesi\u0105c, wykorzystuj\u0105c dat\u0119 "
            "faktycznego wykonania pliku - a nie dat\u0119 jego skopiowania."
        ),
        "welcome.steps": (
            "Oto co si\u0119 teraz wydarzy:\n\n"
            "1. Skanowanie folderu \u017ar\u00f3d\u0142owego - wska\u017c folder, a aplikacja "
            "znajdzie w nim wszystkie zdj\u0119cia i filmy, tak\u017ce w podfolderach.\n"
            "2. Miejsce docelowe i opcje - wybierz, gdzie maj\u0105 trafi\u0107 posortowane "
            "kopie, i nadaj tej kolekcji nazw\u0119.\n"
            "3. Sortowanie - aplikacja kopiuje ka\u017cdy plik do folderu z dat\u0105. "
            "Orygina\u0142y nigdy nie s\u0105 modyfikowane ani usuwane.\n"
            "4. Podsumowanie - zobacz dok\u0142adnie co si\u0119 sta\u0142o i otw\u00f3rz wyniki."
        ),
        "welcome.get_started": "Rozpocznij",

        "source.title": "Wybierz folder \u017ar\u00f3d\u0142owy",
        "source.subtitle": "Wybierz folder do przeskanowania...",
        "source.choose_folder": "Wybierz folder",
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
        "source.file_types": "Typy plik\u00f3w...",

        "destination.title": "Miejsce docelowe i opcje",
        "destination.subtitle": "Wybierz, gdzie zostan\u0105 zapisane posortowane pliki.",
        "destination.collection_name": "Nazwa kolekcji:",
        "destination.choose_folder": "Wybierz folder docelowy",
        "destination.use_filename_date": "U\u017cyj znacznika czasu z nazwy pliku, gdy brak daty w metadanych",
        "destination.use_mtime": "U\u017cyj daty modyfikacji pliku, gdy brak daty w metadanych lub nazwie pliku",
        "destination.use_folder_date": "U\u017cyj nazwy folderu jako daty, gdy brak innego \u017ar\u00f3d\u0142a daty",
        "destination.rename_to_date": "Zmie\u0144 nazwy plik\u00f3w na wykryt\u0105 dat\u0119 (np. 2023-05-14 14.30.22.jpg)",
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
        "sorting.fallback_on": "w\u0142\u0105czone",
        "sorting.fallback_off": "wy\u0142\u0105czone",
        "sorting.start": "Rozpocznij sortowanie",
        "sorting.progress": "{done} / {total} plik\u00f3w przetworzonych ({pct}%)",
        "sorting.complete": "Sortowanie zako\u0144czone.",
        "sorting.cancelled": "Sortowanie anulowane.",
        "sorting.cancelling": "Anulowanie...",
        "sorting.failed": "Sortowanie nie powiod\u0142o si\u0119 - zobacz log powy\u017cej.",
        "sorting.cancel": "Anuluj sortowanie",
        "sorting.view_summary": "Zobacz podsumowanie",

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
        "summary.open_dest": "Otw\u00f3rz folder",
        "summary.open_log": "Otw\u00f3rz log",
        "summary.start_new": "Nowe sortowanie",

        "settings.title": "Ustawienia aplikacji",
        "settings.language": "J\u0119zyk",
        "settings.close": "Zamknij",
        "settings.note": "Log sortowania na \u017cywo zawsze pozostaje w j\u0119zyku angielskim.",
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

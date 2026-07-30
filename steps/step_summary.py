import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QFrame
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QObject, Signal
from sorter_logic.theme import mark_primary, mark_secondary, apply_card_shadow, COLOR_GREEN, COLOR_ORANGE
from sorter_logic.i18n import translator as tr
from paths import resource_path

STAT_CARDS = ("scanned", "exif", "takeout", "filename", "mtime", "folder", "nodate", "errors", "skipped")
STAT_KEYS = {"scanned": "scanned", "exif": "exif", "takeout": "takeout", "filename": "filename",
             "mtime": "mtime", "folder": "folder", "nodate": "no_date", "errors": "errors", "skipped": "skipped"}
STAT_CAPTION_KEYS = {"scanned": "summary.scanned", "exif": "summary.exif", "takeout": "summary.takeout",
                      "filename": "summary.filename", "mtime": "summary.mtime", "folder": "summary.folder",
                      "nodate": "summary.nodate", "errors": "summary.errors", "skipped": "summary.skipped"}


class SummaryStep(QObject):
    start_new_requested = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/step4_summary.ui"))
        ui_file.open(QFile.ReadOnly)

        self.window = loader.load(ui_file)
        self.title_label = self.window.findChild(QLabel, "titleLabel")
        self.verify_label = self.window.findChild(QLabel, "verifyLabel")
        self.log_path_label = self.window.findChild(QLabel, "logPathLabel")
        self.open_dest_btn = self.window.findChild(QPushButton, "openDestButton")
        self.open_log_btn = self.window.findChild(QPushButton, "openLogButton")
        self.review_dupes_btn = self.window.findChild(QPushButton, "reviewDuplicatesButton")
        self.start_new_btn = self.window.findChild(QPushButton, "startNewButton")

        self.number_labels = {}
        self.caption_labels = {}
        for card in STAT_CARDS:
            frame = self.window.findChild(QFrame, f"{card}Card")
            frame.setProperty("card", "true")
            apply_card_shadow(frame)
            number_label = self.window.findChild(QLabel, f"{card}NumberLabel")
            caption_label = self.window.findChild(QLabel, f"{card}CaptionLabel")
            number_label.setProperty("cardNumber", "true")
            caption_label.setProperty("muted", "true")
            self.number_labels[card] = number_label
            self.caption_labels[card] = caption_label

        self.title_label.setProperty("heading", "true")
        self.log_path_label.setProperty("muted", "true")
        mark_secondary(self.open_dest_btn)
        mark_secondary(self.open_log_btn)
        mark_secondary(self.review_dupes_btn)
        mark_primary(self.start_new_btn)

        self.dest_path = None
        self.log_path = None
        self._ok = None
        self.duplicates_removed = 0
        self.skipped_files = []

        self.open_dest_btn.clicked.connect(self.open_destination_folder)
        self.open_log_btn.clicked.connect(self.open_log_file)
        self.start_new_btn.clicked.connect(self.start_new_requested.emit)
        # Repurpose the (now unused) review-duplicates button as the viewer for
        # non-media files that were left behind.
        self.review_dupes_btn.clicked.connect(self.open_skipped)
        self.review_dupes_btn.setVisible(False)
        self.retranslate()

    def retranslate(self):
        self.title_label.setText(tr.t("summary.title"))
        for card in STAT_CARDS:
            self.caption_labels[card].setText(tr.t(STAT_CAPTION_KEYS[card]))
        self.open_dest_btn.setText(tr.t("summary.open_dest"))
        self.open_log_btn.setText(tr.t("summary.open_log"))
        self.start_new_btn.setText(tr.t("summary.start_new"))
        self.review_dupes_btn.setText(tr.t("summary.view_skipped", count=len(self.skipped_files)))
        self._render_verify_label()
        self._render_log_path_label()

    def open_skipped(self):
        if not self.skipped_files:
            return
        from steps.skipped_files_dialog import SkippedFilesDialog
        SkippedFilesDialog(self.skipped_files, self.window).exec()

    def _render_verify_label(self):
        if self._ok is None:
            self.verify_label.setText("")
        elif self._ok:
            self.verify_label.setText(
                f'<span style="color:{COLOR_GREEN}; font-weight:bold;">{tr.t("summary.ok")}</span>'
            )
        else:
            self.verify_label.setText(
                f'<span style="color:{COLOR_ORANGE}; font-weight:bold;">{tr.t("summary.warn")}</span>'
            )

    def _render_log_path_label(self):
        lines = []
        if self.duplicates_removed:
            lines.append(tr.t("summary.duplicates_removed", count=self.duplicates_removed))
        if self.log_path:
            lines.append(tr.t("summary.log_file", path=self.log_path))
        self.log_path_label.setText("\n".join(lines))

    def set_data(self, result):
        stats = result.get("stats") or {}
        self.log_path = result.get("log_path")
        dest = result.get("dest_path") or ""
        name = result.get("collection_name") or ""
        self.dest_path = os.path.join(dest, name) if name else dest
        self.duplicates_removed = stats.get("duplicates_removed", 0)
        self.skipped_files = stats.get("skipped_files", [])
        self.review_dupes_btn.setText(tr.t("summary.view_skipped", count=len(self.skipped_files)))
        self.review_dupes_btn.setVisible(bool(self.skipped_files))

        for card in STAT_CARDS:
            self.number_labels[card].setText(str(stats.get(STAT_KEYS[card], 0)))

        total_out = (stats.get("exif", 0) + stats.get("takeout", 0) + stats.get("filename", 0)
                     + stats.get("mtime", 0) + stats.get("folder", 0) + stats.get("no_date", 0)
                     + stats.get("duplicates_removed", 0))
        self._ok = total_out == stats.get("scanned", 0) - stats.get("errors", 0)
        self._render_verify_label()
        self._render_log_path_label()

    def _reveal(self, path):
        if sys.platform == "darwin":
            subprocess.run(["open", path])
        elif sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path])

    def open_destination_folder(self):
        if self.dest_path and os.path.isdir(self.dest_path):
            self._reveal(self.dest_path)

    def open_log_file(self):
        if self.log_path and os.path.exists(self.log_path):
            self._reveal(self.log_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    step = SummaryStep()
    step.set_data({"stats": {"scanned": 10, "exif": 4, "takeout": 1, "filename": 1, "mtime": 2, "folder": 1,
                              "no_date": 1, "errors": 0, "skipped": 2},
                   "log_path": "/tmp/log.txt", "dest_path": os.path.expanduser("~/Desktop"), "collection_name": "Test"})
    step.window.show()
    app.exec()

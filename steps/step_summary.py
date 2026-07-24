import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QFrame
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QObject, Signal
from sorter_logic.theme import mark_primary, mark_secondary, COLOR_GREEN, COLOR_ORANGE
from paths import resource_path

STAT_CARDS = ("scanned", "exif", "folder", "nodate", "errors", "skipped")
STAT_KEYS = {"scanned": "scanned", "exif": "exif", "folder": "folder", "nodate": "no_date",
             "errors": "errors", "skipped": "skipped"}


class SummaryStep(QObject):
    start_new_requested = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("step4_summary.ui"))
        ui_file.open(QFile.ReadOnly)

        self.window = loader.load(ui_file)
        self.title_label = self.window.findChild(QLabel, "titleLabel")
        self.verify_label = self.window.findChild(QLabel, "verifyLabel")
        self.log_path_label = self.window.findChild(QLabel, "logPathLabel")
        self.open_dest_btn = self.window.findChild(QPushButton, "openDestButton")
        self.open_log_btn = self.window.findChild(QPushButton, "openLogButton")
        self.start_new_btn = self.window.findChild(QPushButton, "startNewButton")

        self.number_labels = {}
        for card in STAT_CARDS:
            frame = self.window.findChild(QFrame, f"{card}Card")
            frame.setProperty("card", "true")
            number_label = self.window.findChild(QLabel, f"{card}NumberLabel")
            caption_label = self.window.findChild(QLabel, f"{card}CaptionLabel")
            number_label.setProperty("cardNumber", "true")
            caption_label.setProperty("muted", "true")
            self.number_labels[card] = number_label

        self.title_label.setProperty("heading", "true")
        self.log_path_label.setProperty("muted", "true")
        mark_secondary(self.open_dest_btn)
        mark_secondary(self.open_log_btn)
        mark_primary(self.start_new_btn)

        self.dest_path = None
        self.log_path = None

        self.open_dest_btn.clicked.connect(self.open_destination_folder)
        self.open_log_btn.clicked.connect(self.open_log_file)
        self.start_new_btn.clicked.connect(self.start_new_requested.emit)

    def set_data(self, result):
        stats = result.get("stats") or {}
        self.log_path = result.get("log_path")
        dest = result.get("dest_path") or ""
        name = result.get("collection_name") or ""
        self.dest_path = os.path.join(dest, name) if name else dest

        for card in STAT_CARDS:
            self.number_labels[card].setText(str(stats.get(STAT_KEYS[card], 0)))

        total_out = stats.get("exif", 0) + stats.get("folder", 0) + stats.get("no_date", 0)
        ok = total_out == stats.get("scanned", 0) - stats.get("errors", 0)
        if ok:
            self.verify_label.setText(f"<span style=\"color:{COLOR_GREEN}; font-weight:bold;\">"
                                        f"✓ Verification OK - all files accounted for.</span>")
        else:
            self.verify_label.setText(f"<span style=\"color:{COLOR_ORANGE}; font-weight:bold;\">"
                                        f"! Warning: file counts do not match - check the log.</span>")

        self.log_path_label.setText(f"Log file: {self.log_path}")

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
    step.set_data({"stats": {"scanned": 10, "exif": 8, "folder": 1, "no_date": 1, "errors": 0, "skipped": 2},
                   "log_path": "/tmp/log.txt", "dest_path": os.path.expanduser("~/Desktop"), "collection_name": "Test"})
    step.window.show()
    app.exec()

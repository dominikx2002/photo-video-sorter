import sys
import os
import html
from datetime import datetime
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QProgressBar, QPlainTextEdit, QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal, QObject
from sorter_logic import run_sort
from sorter_logic.theme import mark_primary, mark_secondary, COLOR_GREEN, COLOR_ORANGE, COLOR_PRIMARY, COLOR_TEXT
from paths import resource_path

LOG_COLORS = {
    "[COPY]": COLOR_GREEN,
    "[EXIF]": "#2A6FB0",
    "[VIDEO]": "#2A6FB0",
    "[FOLDER-DATE]": COLOR_ORANGE,
    "[NO DATE]": COLOR_ORANGE,
    "[ERROR]": COLOR_PRIMARY,
    "[SKIP]": "#A9ACB1",
}


def get_log_dir():
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Logs/PhotoSorterApp")
        elif sys.platform == "win32":
            base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "PhotoSorterApp", "Logs")
        else:
            base = os.path.expanduser("~/.local/share/PhotoSorterApp/logs")
    else:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(base, exist_ok=True)
    return base


def get_log_path(parent_name):
    safe_name = "".join(c for c in parent_name.strip() if c.isalnum() or c in " _-") or "sort"
    return os.path.join(get_log_dir(), f"sort_log_{safe_name}_{datetime.now():%Y%m%d_%H%M%S}.txt")


class SortWorker(QObject):
    log_line = Signal(str)
    progress = Signal(int, int)
    finished = Signal(dict, str)
    error = Signal(str)

    def __init__(self, parent_name, src, dst, use_folder_date, log_path, should_cancel=None):
        super().__init__()
        self.parent_name = parent_name
        self.src = src
        self.dst = dst
        self.use_folder_date = use_folder_date
        self.log_path = log_path
        self.should_cancel = should_cancel

    def run(self):
        try:
            stats, log_path = run_sort(
                self.parent_name, self.src, self.dst, self.use_folder_date,
                self.log_path, self.log_line.emit, self.progress.emit,
                should_cancel=self.should_cancel,
            )
            self.finished.emit(stats, log_path)
        except Exception as e:
            self.error.emit(str(e))


class SortingStep(QObject):
    continue_requested = Signal()
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("step3_sorting.ui"))
        ui_file.open(QFile.ReadOnly)

        self.window = loader.load(ui_file)
        self.title_label = self.window.findChild(QLabel, "titleLabel")
        self.subtitle_label = self.window.findChild(QLabel, "subtitleLabel")
        self.summary_label = self.window.findChild(QLabel, "summaryLabel")
        self.start_btn = self.window.findChild(QPushButton, "startButton")
        self.progress_bar = self.window.findChild(QProgressBar, "sortProgressBar")
        self.progress_label = self.window.findChild(QLabel, "progressLabel")
        self.log_view = self.window.findChild(QPlainTextEdit, "logView")
        self.log_view.setObjectName("logView")
        self.pre_start_spacer = self.window.findChild(QWidget, "preStartSpacer")
        self.back_btn = self.window.findChild(QPushButton, "backButton")
        self.cancel_btn = self.window.findChild(QPushButton, "cancelButton")
        self.continue_btn = self.window.findChild(QPushButton, "continueButton")

        self.title_label.setProperty("heading", "true")
        self.subtitle_label.setProperty("subheading", "true")
        self.summary_label.setProperty("muted", "true")
        self.progress_label.setProperty("muted", "true")
        mark_primary(self.start_btn)
        mark_primary(self.continue_btn)
        mark_secondary(self.back_btn)
        mark_secondary(self.cancel_btn)

        self.start_btn.clicked.connect(self.start_sorting)
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.cancel_btn.clicked.connect(self.cancel_sorting)

        self.thread = None
        self.worker = None
        self.stats = None
        self.log_path = None
        self.context = None

        self._reset_ui()

    def set_context(self, src_path, dest_path, collection_name, use_folder_date):
        self.context = {
            "src_path": src_path,
            "dest_path": dest_path,
            "collection_name": collection_name,
            "use_folder_date": use_folder_date,
        }
        fallback = "on" if use_folder_date else "off"
        self.summary_label.setText(
            f"Source: {src_path}\n"
            f"Destination: {os.path.join(dest_path, collection_name) if collection_name else dest_path}\n"
            f"Folder-name fallback: {fallback}"
        )
        self._reset_ui()

    def get_result(self):
        return {"stats": self.stats, "log_path": self.log_path, **(self.context or {})}

    def reset(self):
        self.context = None
        self.summary_label.setText("")
        self._reset_ui()

    def _reset_ui(self):
        self.stats = None
        self.log_path = None
        self.start_btn.show()
        self.start_btn.setEnabled(True)
        self.pre_start_spacer.show()
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.progress_label.hide()
        self.progress_label.setText("")
        self.log_view.hide()
        self.log_view.clear()
        self.continue_btn.setEnabled(False)
        self.back_btn.setEnabled(True)
        self.cancel_btn.hide()
        self.cancel_btn.setEnabled(True)

    def start_sorting(self):
        if not self.context:
            return

        self.start_btn.hide()
        self.pre_start_spacer.hide()
        self.progress_bar.show()
        self.progress_label.show()
        self.log_view.show()
        self.back_btn.setEnabled(False)
        self.cancel_btn.show()
        self.cancel_btn.setEnabled(True)

        log_path = get_log_path(self.context["collection_name"])

        self.thread = QThread()
        self.worker = SortWorker(
            self.context["collection_name"], self.context["src_path"],
            self.context["dest_path"], self.context["use_folder_date"], log_path,
            should_cancel=self.thread.isInterruptionRequested,
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log_line.connect(self.append_log)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)

        self.thread.start()

    def on_progress(self, done, total):
        self.progress_bar.setMaximum(max(total, 1))
        self.progress_bar.setValue(done)
        pct = int(done / total * 100) if total else 100
        self.progress_label.setText(f"{done} / {total} files processed ({pct}%)")

    def cancel_sorting(self):
        if self.thread:
            self.thread.requestInterruption()
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Cancelling...")

    def on_finished(self, stats, log_path):
        self.stats = stats
        self.log_path = log_path
        self.progress_label.setText("Sorting cancelled." if stats.get("cancelled") else "Sorting complete.")
        self.cancel_btn.hide()
        self.continue_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def on_error(self, message):
        self.append_log(f"[ERROR] {message}")
        self.progress_label.setText("Sorting failed - see log above.")
        self.cancel_btn.hide()
        self.back_btn.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def append_log(self, msg):
        color = None
        for tag, tag_color in LOG_COLORS.items():
            if tag in msg:
                color = tag_color
                break
        if color is None and (msg.isupper() or msg.strip().startswith("=") or msg.strip().startswith("-")):
            color = COLOR_TEXT
        escaped = html.escape(msg)
        if color:
            self.log_view.appendHtml(f'<span style="color:{color};">{escaped}</span>')
        else:
            self.log_view.appendPlainText(msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    step = SortingStep()
    step.set_context(os.path.expanduser("~/Pictures"), os.path.expanduser("~/Desktop"), "Test", True)
    step.window.show()
    app.exec()

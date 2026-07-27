import sys
import os
import html
from datetime import datetime
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QProgressBar, QPlainTextEdit, QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal, QObject, QPropertyAnimation, QEasingCurve
from sorter_logic import run_sort
from sorter_logic.theme import mark_primary, mark_secondary, COLOR_GREEN, COLOR_ORANGE, COLOR_PRIMARY, COLOR_TEXT
from sorter_logic.i18n import translator as tr
from paths import resource_path

LOG_COLORS = {
    "[COPY]": COLOR_GREEN,
    "[EXIF]": "#2A6FB0",
    "[VIDEO]": "#2A6FB0",
    "[TAKEOUT]": "#2A6FB0",
    "[FILENAME]": "#6C5CE7",
    "[MTIME]": "#2FA39B",
    "[RENAME]": "#6C5CE7",
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

    def __init__(self, parent_name, src, dst, use_folder_date, log_path, should_cancel=None,
                 use_mtime=True, use_filename_date=True, allowed_extensions=None, rename_to_date=False):
        super().__init__()
        self.parent_name = parent_name
        self.src = src
        self.dst = dst
        self.use_folder_date = use_folder_date
        self.use_mtime = use_mtime
        self.use_filename_date = use_filename_date
        self.allowed_extensions = allowed_extensions
        self.rename_to_date = rename_to_date
        self.log_path = log_path
        self.should_cancel = should_cancel

    def run(self):
        try:
            stats, log_path = run_sort(
                self.parent_name, self.src, self.dst, self.use_folder_date,
                self.log_path, self.log_line.emit, self.progress.emit,
                should_cancel=self.should_cancel, use_mtime=self.use_mtime,
                use_filename_date=self.use_filename_date,
                allowed_extensions=self.allowed_extensions,
                rename_to_date=self.rename_to_date,
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
        ui_file = QFile(resource_path("ui/step3_sorting.ui"))
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

        self.progress_bar.setTextVisible(False)
        self.progress_anim = QPropertyAnimation(self.progress_bar, b"value", self)
        self.progress_anim.setDuration(250)
        self.progress_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.start_btn.clicked.connect(self.start_sorting)
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.cancel_btn.clicked.connect(self.cancel_sorting)

        self.thread = None
        self.worker = None
        self.stats = None
        self.log_path = None
        self.context = None
        self._progress_state = None

        self._reset_ui()
        self.retranslate()

    def retranslate(self):
        self.title_label.setText(tr.t("sorting.title"))
        self.subtitle_label.setText(tr.t("sorting.subtitle"))
        self.start_btn.setText(tr.t("sorting.start"))
        self.cancel_btn.setText(tr.t("sorting.cancel"))
        self.continue_btn.setText(tr.t("sorting.view_summary"))
        self.back_btn.setText(tr.t("common.back"))
        self._render_summary_label()
        self._render_progress_label()

    def _render_summary_label(self):
        if not self.context:
            self.summary_label.setText("")
            return
        src_path = self.context["src_path"]
        dest_path = self.context["dest_path"]
        collection_name = self.context["collection_name"]
        dst = os.path.join(dest_path, collection_name) if collection_name else dest_path
        filename_fallback = tr.t("sorting.fallback_on") if self.context["use_filename_date"] else tr.t("sorting.fallback_off")
        mtime_fallback = tr.t("sorting.fallback_on") if self.context["use_mtime"] else tr.t("sorting.fallback_off")
        fallback = tr.t("sorting.fallback_on") if self.context["use_folder_date"] else tr.t("sorting.fallback_off")
        rename = tr.t("sorting.fallback_on") if self.context["rename_to_date"] else tr.t("sorting.fallback_off")
        self.summary_label.setText(tr.t(
            "sorting.summary", src=src_path, dst=dst, filename_fallback=filename_fallback,
            mtime_fallback=mtime_fallback, fallback=fallback, rename=rename,
        ))

    def _render_progress_label(self):
        state = self._progress_state
        if state is None:
            self.progress_label.setText("")
        elif state[0] == "progress":
            _, done, total = state
            pct = int(done / total * 100) if total else 100
            self.progress_label.setText(tr.t("sorting.progress", done=done, total=total, pct=pct))
        else:
            self.progress_label.setText(tr.t(f"sorting.{state[0]}"))

    def set_context(self, src_path, dest_path, collection_name, use_folder_date,
                     use_mtime=True, use_filename_date=True, allowed_extensions=None,
                     rename_to_date=False):
        self.context = {
            "src_path": src_path,
            "dest_path": dest_path,
            "collection_name": collection_name,
            "use_folder_date": use_folder_date,
            "use_mtime": use_mtime,
            "use_filename_date": use_filename_date,
            "allowed_extensions": allowed_extensions,
            "rename_to_date": rename_to_date,
        }
        self._render_summary_label()
        self._reset_ui()

    def get_result(self):
        return {"stats": self.stats, "log_path": self.log_path, **(self.context or {})}

    def reset(self):
        self.context = None
        self._render_summary_label()
        self._reset_ui()

    def _reset_ui(self):
        self.stats = None
        self.log_path = None
        self._progress_state = None
        self.start_btn.show()
        self.start_btn.setEnabled(True)
        self.pre_start_spacer.show()
        self.progress_anim.stop()
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.progress_label.hide()
        self._render_progress_label()
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
            use_mtime=self.context["use_mtime"],
            use_filename_date=self.context["use_filename_date"],
            allowed_extensions=self.context["allowed_extensions"],
            rename_to_date=self.context["rename_to_date"],
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
        self.progress_anim.stop()
        self.progress_anim.setStartValue(self.progress_bar.value())
        self.progress_anim.setEndValue(done)
        self.progress_anim.start()
        self._progress_state = ("progress", done, total)
        self._render_progress_label()

    def cancel_sorting(self):
        if self.thread:
            self.thread.requestInterruption()
        self.cancel_btn.setEnabled(False)
        self._progress_state = ("cancelling",)
        self._render_progress_label()

    def on_finished(self, stats, log_path):
        self.stats = stats
        self.log_path = log_path
        self._progress_state = ("cancelled",) if stats.get("cancelled") else ("complete",)
        self._render_progress_label()
        self.cancel_btn.hide()
        self.continue_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def on_error(self, message):
        self.append_log(f"[ERROR] {message}")
        self._progress_state = ("failed",)
        self._render_progress_label()
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

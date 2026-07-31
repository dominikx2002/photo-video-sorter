import sys
import os
import html
from datetime import datetime
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QProgressBar, QPlainTextEdit, QWidget, QGraphicsOpacityEffect, QVBoxLayout
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal, QObject, QPropertyAnimation, QEasingCurve, Qt
from sorter_logic import run_sort
from sorter_logic.theme import mark_primary, mark_secondary, accent
from sorter_logic.i18n import translator as tr
from shimmer_progress import replace_progressbar
from activity_loader import SpinnerTrivia
from svg_icon import colored_svg_datauri
from paths import resource_path

# Bright, terminal-style palette - the log renders white-on-dark, so these are
# tuned to read against #1E1E24 (roughly the VS Code / iTerm defaults).
LOG_COLORS = {
    "[COPY]": "#4EC98A",
    "[EXIF]": "#4FA6FF",
    "[VIDEO]": "#4FA6FF",
    "[TAKEOUT]": "#4FA6FF",
    "[FILENAME]": "#C58AF0",
    "[MTIME]": "#4EC9C9",
    "[RENAME]": "#C58AF0",
    "[FOLDER-DATE]": "#E5B045",
    "[NO DATE]": "#E5B045",
    "[DUPLICATE]": "#E5B045",
    "[ERROR]": "#F16A6A",
    "[SKIP]": "#8A8D94",
}
LOG_DEFAULT_COLOR = "#D4D4DC"


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
    current_file = Signal(str)
    finished = Signal(dict, str)
    error = Signal(str)

    def __init__(self, parent_name, src, dst, use_folder_date, log_path, should_cancel=None,
                 use_mtime=True, use_filename_date=True, allowed_extensions=None, rename_to_date=False,
                 move_files=False, folder_template="year_month"):
        super().__init__()
        self.parent_name = parent_name
        self.src = src
        self.dst = dst
        self.use_folder_date = use_folder_date
        self.use_mtime = use_mtime
        self.use_filename_date = use_filename_date
        self.allowed_extensions = allowed_extensions
        self.rename_to_date = rename_to_date
        self.move_files = move_files
        self.folder_template = folder_template
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
                on_file=self.current_file.emit,
                move_files=self.move_files,
                folder_template=self.folder_template,
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
        self.progress_bar = replace_progressbar(self.window, "sortProgressBar")
        self.progress_label = self.window.findChild(QLabel, "progressLabel")
        self.current_file_label = self.window.findChild(QLabel, "currentFileLabel")
        self.log_view = self.window.findChild(QPlainTextEdit, "logView")
        self.log_view.setObjectName("logView")
        self.details_toggle_btn = self.window.findChild(QPushButton, "detailsToggleButton")
        self.details_toggle_btn.setObjectName("detailsToggle")
        self.details_spacer = self.window.findChild(QWidget, "detailsSpacer")
        self.pre_start_spacer = self.window.findChild(QWidget, "preStartSpacer")
        self.back_btn = self.window.findChild(QPushButton, "backButton")
        self.cancel_btn = self.window.findChild(QPushButton, "cancelButton")
        self.continue_btn = self.window.findChild(QPushButton, "continueButton")

        self.title_label.setProperty("heading", "true")
        self.subtitle_label.setProperty("subheading", "true")
        self.summary_label.setProperty("muted", "true")
        self.summary_label.setTextFormat(Qt.RichText)
        self.progress_label.setProperty("muted", "true")
        self.current_file_label.setProperty("muted", "true")
        mark_primary(self.start_btn)
        mark_primary(self.continue_btn)
        mark_secondary(self.back_btn)
        mark_secondary(self.cancel_btn)

        self.progress_bar.setTextVisible(False)
        self.progress_anim = QPropertyAnimation(self.progress_bar, b"animValue", self)
        self.progress_anim.setDuration(250)
        self.progress_anim.setEasingCurve(QEasingCurve.OutCubic)

        # A slow, continuous opacity pulse on the "currently copying" label -
        # so even when the same large file is copying for a long stretch
        # (no new progress/log events firing), something is visibly still
        # moving and the app doesn't look frozen. Using keyframes for a
        # smooth 1.0 -> 0.4 -> 1.0 "breathing" triangle wave, rather than
        # start/end values, so consecutive loops connect without a snap.
        self._current_file_opacity = QGraphicsOpacityEffect(self.current_file_label)
        self.current_file_label.setGraphicsEffect(self._current_file_opacity)
        self.pulse_anim = QPropertyAnimation(self._current_file_opacity, b"opacity", self)
        self.pulse_anim.setDuration(1400)
        self.pulse_anim.setKeyValueAt(0.0, 1.0)
        self.pulse_anim.setKeyValueAt(0.5, 0.4)
        self.pulse_anim.setKeyValueAt(1.0, 1.0)
        self.pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.pulse_anim.setLoopCount(-1)

        # A spinner with rotating "what sorting does" trivia - the same alive
        # indicator as the duplicate scanner - in place of the old show-details
        # disclosure and log terminal (the full log is still written to file).
        self.trivia = SpinnerTrivia()
        self.trivia.hide()
        layout = self.window.findChild(QVBoxLayout, "verticalLayout")
        layout.insertWidget(layout.indexOf(self.current_file_label) + 1, self.trivia)
        self.details_toggle_btn.hide()
        self.log_view.hide()

        self.start_btn.clicked.connect(self.start_sorting)
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.cancel_btn.clicked.connect(self.cancel_sorting)
        self.details_toggle_btn.clicked.connect(self.toggle_details)

        self.thread = None
        self.worker = None
        self.stats = None
        self.log_path = None
        self.context = None
        self._progress_state = None
        self._current_file_name = None
        self._details_open = False

        self._reset_ui()
        self.retranslate()

    def retranslate(self):
        self.title_label.setText(tr.t("sorting.title"))
        moving = bool(self.context and self.context.get("move_files"))
        self.subtitle_label.setText(tr.t("sorting.subtitle_move" if moving else "sorting.subtitle"))
        self.start_btn.setText(tr.t("sorting.start"))
        self.cancel_btn.setText(tr.t("sorting.cancel"))
        self.continue_btn.setText(tr.t("sorting.view_summary"))
        self.back_btn.setText(tr.t("common.back"))
        self._render_summary_label()
        self._render_progress_label()
        self._render_current_file_label()
        self._render_details_toggle()

    def _render_details_toggle(self):
        key = "sorting.hide_details" if self._details_open else "sorting.show_details"
        self.details_toggle_btn.setText(tr.t(key))

    def toggle_details(self):
        # Ubuntu-installer style: the log stays hidden behind this disclosure,
        # so the default view is just the progress. Expanding reveals the
        # terminal; the expanding spacer that keeps the nav pinned to the
        # bottom yields its space to the log.
        self._details_open = not self._details_open
        self.log_view.setVisible(self._details_open)
        self.details_spacer.setVisible(not self._details_open)
        self._render_details_toggle()

    def _render_summary_label(self):
        if not self.context:
            self.summary_label.setText("")
            return
        src = self.context["src_path"]
        if isinstance(src, (list, tuple)):
            src_path = src[0] if len(src) == 1 else tr.t("sorting.n_sources", n=len(src))
        else:
            src_path = src
        dest_path = self.context["dest_path"]
        collection_name = self.context["collection_name"]
        dst = os.path.join(dest_path, collection_name) if collection_name else dest_path
        on, off = self._mark(True), self._mark(False)
        filename_fallback = on if self.context["use_filename_date"] else off
        mtime_fallback = on if self.context["use_mtime"] else off
        fallback = on if self.context["use_folder_date"] else off
        rename = on if self.context["rename_to_date"] else off
        self.summary_label.setText(tr.t(
            "sorting.summary", src=src_path, dst=dst, filename_fallback=filename_fallback,
            mtime_fallback=mtime_fallback, fallback=fallback, rename=rename,
        ))

    def _mark(self, on):
        # A round check (accent colour) when on, a round x (white) when off -
        # rendered from the SVG icons, tinted to the live theme. Falls back to a
        # text glyph if an icon file is missing.
        if on:
            icon = colored_svg_datauri(resource_path("packaging/icons/check-round.svg"), accent())
            return icon or f'<span style="color:{accent()};">&#x2714;</span>'
        icon = colored_svg_datauri(resource_path("packaging/icons/uncheck-round.svg"), "#FFFFFF")
        return icon or '<span style="color:#FFFFFF;">&#x2715;</span>'

    def _facts(self):
        facts = [tr.t(f"sorting.fact_{i}") for i in range(1, 8)]
        if self.context and self.context.get("move_files"):
            facts[1] = tr.t("sorting.fact_2_move")   # the "copying only" fact
        return facts

    def _render_progress_label(self):
        state = self._progress_state
        if state is None:
            self.progress_label.setText("")
        elif state[0] == "progress":
            _, done, total = state
            pct = int(done / total * 100) if total else 100
            self.progress_label.setText(tr.t("sorting.progress", done=done, total=total, pct=pct))
        elif state[0] == "complete":
            # Same "100% — done" wording as the duplicate finder at 100%.
            self.progress_label.setText(tr.t("progress.done", pct=100))
        else:
            self.progress_label.setText(tr.t(f"sorting.{state[0]}"))

    def _render_current_file_label(self):
        if self._current_file_name:
            moving = bool(self.context and self.context.get("move_files"))
            key = "sorting.current_file_move" if moving else "sorting.current_file"
            self.current_file_label.setText(tr.t(key, name=self._current_file_name))
        else:
            self.current_file_label.setText("")

    def set_context(self, src_path, dest_path, collection_name, use_folder_date,
                     use_mtime=True, use_filename_date=True, allowed_extensions=None,
                     rename_to_date=False, move_files=False, folder_template="year_month"):
        self.context = {
            "src_path": src_path,
            "dest_path": dest_path,
            "collection_name": collection_name,
            "use_folder_date": use_folder_date,
            "use_mtime": use_mtime,
            "use_filename_date": use_filename_date,
            "allowed_extensions": allowed_extensions,
            "rename_to_date": rename_to_date,
            "move_files": move_files,
            "folder_template": folder_template,
        }
        self.subtitle_label.setText(
            tr.t("sorting.subtitle_move" if move_files else "sorting.subtitle"))
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
        self._current_file_name = None
        self.start_btn.show()
        self.start_btn.setEnabled(True)
        self.pre_start_spacer.show()
        self.progress_anim.stop()
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.progress_label.hide()
        self._render_progress_label()
        self.trivia.stop()
        self.trivia.hide()
        self.current_file_label.hide()
        self._render_current_file_label()
        self.details_spacer.hide()
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
        self.current_file_label.show()
        # Spinner + sorting trivia keeps the view alive; the spacer holds the nav
        # at the bottom. The log is written to file, not shown in the UI.
        self.trivia.start(self._facts())
        self.trivia.show()
        self.details_spacer.show()
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
            move_files=self.context["move_files"],
            folder_template=self.context["folder_template"],
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log_line.connect(self.append_log)
        self.worker.progress.connect(self.on_progress)
        self.worker.current_file.connect(self.on_current_file)
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

    def on_current_file(self, name):
        self._current_file_name = name
        self._render_current_file_label()

    def cancel_sorting(self):
        if self.thread:
            self.thread.requestInterruption()
        self.cancel_btn.setEnabled(False)
        self._progress_state = ("cancelling",)
        self._render_progress_label()

    def on_finished(self, stats, log_path):
        self.stats = stats
        self.log_path = log_path
        if not stats.get("cancelled"):
            self.progress_anim.stop()
            self.progress_bar.setValue(self.progress_bar.maximum())     # snap to full
        self._progress_state = ("cancelled",) if stats.get("cancelled") else ("complete",)
        self._render_progress_label()
        self.trivia.stop()
        self.trivia.hide()
        self._current_file_name = None
        self._render_current_file_label()
        self.current_file_label.hide()
        self.cancel_btn.hide()
        self.continue_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def on_error(self, message):
        self.append_log(f"[ERROR] {message}")
        self._progress_state = ("failed",)
        self._render_progress_label()
        self.trivia.stop()
        self.trivia.hide()
        self._current_file_name = None
        self._render_current_file_label()
        self.current_file_label.hide()
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
            color = LOG_DEFAULT_COLOR
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

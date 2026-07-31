import os
import threading
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, QTimer
from sorter_logic.scan_source import find_duplicate_groups
from sorter_logic.constants import PHOTO_EXT
from sorter_logic.theme import mark_primary, mark_secondary, accent, COLOR_GREEN
from sorter_logic.fsutil import trash_or_remove
from sorter_logic.i18n import translator as tr
from sorter_logic.mac_chrome import begin_activity, end_activity
from shimmer_progress import ShimmerProgressBar
from activity_loader import SpinnerTrivia
from steps.duplicate_review_dialog import (
    DuplicateReviewDialog, PreviewLoadingDialog, decode_thumb, _PER_PAGE,
)


class _DupWorker(QObject):
    finished = Signal(list)
    progress = Signal(int, int)
    activity = Signal(str, str)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self._cancel = threading.Event()

    def cancel(self):
        self._cancel.set()

    def run(self):
        groups = find_duplicate_groups(
            self.path, progress=self.progress.emit, should_cancel=self._cancel.is_set,
            activity=self.activity.emit)
        self.finished.emit(groups)


class DuplicateFinderDialog(QDialog):
    """Standalone tool: scan a folder for byte-identical photos/videos, review
    the duplicates as thumbnails, and delete the redundant copies (one kept per
    set) in place."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(False)
        self.setMinimumSize(620, 560)
        self.path = ""
        self.groups = []
        self.thread = None
        self.worker = None
        self._closing = False
        self._activity_token = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setProperty("heading", "true")
        layout.addWidget(self.title_label)
        self.subtitle_label = QLabel()
        self.subtitle_label.setProperty("subheading", "true")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        self.choose_btn = QPushButton()
        mark_secondary(self.choose_btn)
        self.choose_btn.clicked.connect(self._choose)
        self.scan_btn = QPushButton()
        mark_primary(self.scan_btn)
        self.scan_btn.clicked.connect(self._scan)
        row.addWidget(self.folder_edit, 1)
        row.addWidget(self.choose_btn)
        row.addWidget(self.scan_btn)
        layout.addLayout(row)

        self.status_label = QLabel()
        self.status_label.setTextFormat(Qt.RichText)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress = ShimmerProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        # A subtle, greyed live "log" line under the bar - the file/folder the
        # scan is touching right now, so you can watch it work.
        self.activity_label = QLabel()
        self.activity_label.setObjectName("activityLog")
        self.activity_label.hide()
        layout.addWidget(self.activity_label)

        # Spinner + rotating "how duplicates are found" trivia, gently pulsing.
        self.trivia = SpinnerTrivia()
        self.trivia.hide()
        layout.addWidget(self.trivia)

        layout.addStretch(1)

        nav = QHBoxLayout()
        self.close_btn = QPushButton()
        mark_secondary(self.close_btn)
        self.close_btn.clicked.connect(self.close)
        self.review_btn = QPushButton()
        mark_primary(self.review_btn)
        self.review_btn.clicked.connect(self._open_review)
        self.review_btn.setVisible(False)
        self.delete_btn = QPushButton()
        mark_secondary(self.delete_btn)
        self.delete_btn.clicked.connect(self._delete)
        self.delete_btn.setVisible(False)
        nav.addWidget(self.close_btn)
        nav.addStretch(1)
        nav.addWidget(self.delete_btn)
        nav.addWidget(self.review_btn)
        layout.addLayout(nav)

        self.retranslate()
        tr.language_changed.connect(self.retranslate)

    def retranslate(self, *_):
        self.setWindowTitle(tr.t("dupfinder.title"))
        self.title_label.setText(tr.t("dupfinder.title"))
        self.subtitle_label.setText(tr.t("dupfinder.subtitle"))
        self.choose_btn.setText(tr.t("dupfinder.choose"))
        self.scan_btn.setText(tr.t("dupfinder.scan"))
        self.close_btn.setText(tr.t("settings.close"))
        self._render_delete_btn()
        self._render_review_btn()

    def _choose(self):
        folder = QFileDialog.getExistingDirectory(self, tr.t("dupfinder.title"))
        if folder:
            self.path = folder
            self.folder_edit.setText(folder)

    def _scan(self):
        if not self.path:
            self.status_label.setText(
                f'<span style="color:{accent()};">{tr.t("dupfinder.pick_first")}</span>')
            return
        self.scan_btn.setEnabled(False)
        self.delete_btn.setVisible(False)
        self.review_btn.setVisible(False)
        self.status_label.setText(tr.t("dupfinder.scanning"))
        self.progress.setRange(0, 0)          # busy while walking the folder
        self.progress.show()
        self.activity_label.setText("")
        self.activity_label.show()
        self.trivia.start(self._facts())
        self.trivia.show()
        # Keep macOS App Nap from suspending us (and the worker) when the app
        # loses focus mid-scan.
        self._activity_token = begin_activity("Scanning for duplicate files")

        self.thread = QThread()
        self.worker = _DupWorker(self.path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.activity.connect(self._on_activity)
        self.worker.finished.connect(self._on_found)
        self.thread.start()

    def _facts(self):
        return [tr.t(f"dupfinder.fact_{i}") for i in range(1, 8)]

    def _stop_activity_ui(self):
        self.progress.hide()
        self.activity_label.hide()
        self.trivia.stop()
        self.trivia.hide()

    def _on_activity(self, phase, name):
        if self._closing:
            return
        key = "dupfinder.log_walk" if phase == "walk" else "dupfinder.log_read"
        text = tr.t(key, name=name)
        fm = self.activity_label.fontMetrics()
        self.activity_label.setText(
            fm.elidedText(text, Qt.ElideRight, max(self.width() - 90, 120)))

    def _on_progress(self, done, total):
        if self._closing or not total:
            return
        self.progress.setRange(0, total)
        self.progress.setValue(done)
        pct = int(done * 100 / total)
        if done >= total:
            self.status_label.setText(tr.t("progress.done", pct=100))
        else:
            self.status_label.setText(
                tr.t("dupfinder.progress", done=done, total=total, pct=pct))

    def _on_found(self, groups):
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        if self._closing:
            return
        self.scan_btn.setEnabled(True)
        self._end_activity()
        self._stop_activity_ui()
        self.groups = groups
        # No inline preview here - just the summary and buttons. Thumbnails live
        # in the separate "Browse sets" window, which pages 10 sets at a time.
        self._render_groups()

    def _end_activity(self):
        if self._activity_token is not None:
            end_activity(self._activity_token)
            self._activity_token = None

    def _stop_thread(self):
        if self.thread and self.thread.isRunning():
            if self.worker:
                self.worker.cancel()
            self.thread.quit()
            self.thread.wait()
        self.trivia.stop()
        self._end_activity()

    def closeEvent(self, event):
        # Never let a running scan thread outlive the dialog - that aborts Qt.
        self._closing = True
        self._stop_thread()
        super().closeEvent(event)

    def _render_groups(self):
        dup_count = sum(len(g) - 1 for g in self.groups)
        if not self.groups:
            self.status_label.setText(
                f'<span style="color:{COLOR_GREEN};">{tr.t("dupfinder.none")}</span>')
            self.delete_btn.setVisible(False)
            self.review_btn.setVisible(False)
            return
        self.status_label.setText(
            tr.t("dupfinder.found", color=accent(), count=dup_count, sets=len(self.groups)))
        self.delete_btn.setVisible(True)
        self.review_btn.setVisible(True)
        self._render_delete_btn()
        self._render_review_btn()

    def _render_review_btn(self):
        self.review_btn.setText(tr.t("dupfinder.browse", count=len(self.groups)))

    def _open_review(self):
        if not self.groups:
            return
        # Generate the first page's thumbnails up front, in a small progress
        # window; only once they're all ready does that window close and the
        # review dialog open - fully rendered, no half-built preview.
        first = self.groups[:_PER_PAGE]
        paths = [p for g in first for p in g
                 if os.path.splitext(p)[1].lower() in PHOTO_EXT]
        cache = {}
        if paths:
            loader = PreviewLoadingDialog(self)
            loader.set_progress(0, len(paths))
            token = begin_activity("Generating duplicate preview")
            state = {"i": 0}
            timer = QTimer(loader)
            timer.setInterval(0)

            def step():
                budget = 4
                while budget and state["i"] < len(paths):
                    p = paths[state["i"]]
                    cache[p] = decode_thumb(p)
                    state["i"] += 1
                    budget -= 1
                loader.set_progress(state["i"], len(paths))
                if state["i"] >= len(paths):
                    timer.stop()
                    end_activity(token)
                    loader.accept()

            timer.timeout.connect(step)
            timer.start()
            loader.exec()

        DuplicateReviewDialog(self.groups, parent=self,
                              on_deleted=self._on_review_deleted,
                              thumb_cache=cache).exec()

    def _on_review_deleted(self, deleted):
        if not deleted:
            return
        dset = set(deleted)
        self.groups = [[p for p in g if p not in dset] for g in self.groups]
        self.groups = [g for g in self.groups if len(g) >= 2]
        self._render_groups()

    def _render_delete_btn(self):
        dup_count = sum(len(g) - 1 for g in self.groups)
        self.delete_btn.setText(tr.t("dupfinder.delete", count=dup_count))

    def _delete(self):
        dup_count = sum(len(g) - 1 for g in self.groups)
        if not dup_count:
            return
        # Check the clicked button by identity - QMessageBox.question can report
        # the wrong standard button on macOS, which let "No" delete anyway.
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(tr.t("dupfinder.confirm_title"))
        box.setText(tr.t("dupfinder.confirm", count=dup_count))
        delete_button = box.addButton(tr.t("review.confirm_delete"), QMessageBox.DestructiveRole)
        cancel_button = box.addButton(tr.t("review.confirm_cancel"), QMessageBox.RejectRole)
        box.setDefaultButton(cancel_button)
        box.exec()
        if box.clickedButton() is not delete_button:
            return
        deleted = 0
        for group in self.groups:
            for path in group[1:]:              # keep the first, delete the rest
                try:
                    trash_or_remove(path)
                    deleted += 1
                except OSError:
                    pass
        self.groups = []
        self.delete_btn.setVisible(False)
        self.review_btn.setVisible(False)
        self.status_label.setText(
            f'<span style="color:{COLOR_GREEN};">{tr.t("dupfinder.deleted", count=deleted)}</span>')

import os
import threading
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QScrollArea, QWidget, QFrame, QMessageBox, QProgressBar,
)
from PySide6.QtCore import Qt, QObject, QThread, Signal, QSize
from PySide6.QtGui import QPixmap
from sorter_logic.scan_source import find_duplicate_groups
from sorter_logic.constants import PHOTO_EXT
from sorter_logic.fsutil import human_size
from sorter_logic.theme import mark_primary, mark_secondary, accent, COLOR_GREEN, COLOR_ORANGE
from sorter_logic.i18n import translator as tr

_THUMB = 48


_MAX_GROUPS_SHOWN = 120     # cap on how many sets get thumbnail cards


class _DupWorker(QObject):
    finished = Signal(list)
    progress = Signal(int, int)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self._cancel = threading.Event()

    def cancel(self):
        self._cancel.set()

    def run(self):
        groups = find_duplicate_groups(
            self.path, progress=self.progress.emit, should_cancel=self._cancel.is_set)
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

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.groups_layout = QVBoxLayout(self.container)
        self.groups_layout.setContentsMargins(0, 0, 0, 0)
        self.groups_layout.setSpacing(10)
        self.groups_layout.addStretch(1)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        nav = QHBoxLayout()
        self.delete_btn = QPushButton()
        mark_primary(self.delete_btn)
        self.delete_btn.clicked.connect(self._delete)
        self.delete_btn.setVisible(False)
        self.close_btn = QPushButton()
        mark_secondary(self.close_btn)
        self.close_btn.clicked.connect(self.close)
        nav.addWidget(self.close_btn)
        nav.addStretch(1)
        nav.addWidget(self.delete_btn)
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
        self._clear_groups()
        self.status_label.setText(tr.t("dupfinder.scanning"))
        self.progress.setRange(0, 0)          # busy while walking the folder
        self.progress.show()

        self.thread = QThread()
        self.worker = _DupWorker(self.path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_found)
        self.thread.start()

    def _on_progress(self, done, total):
        if self._closing or not total:
            return
        self.progress.setRange(0, total)
        self.progress.setValue(done)
        self.status_label.setText(tr.t("dupfinder.progress", done=done, total=total))

    def _on_found(self, groups):
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        if self._closing:
            return
        self.scan_btn.setEnabled(True)
        self.progress.hide()
        self.groups = groups
        self._render_groups()

    def _stop_thread(self):
        if self.thread and self.thread.isRunning():
            if self.worker:
                self.worker.cancel()
            self.thread.quit()
            self.thread.wait()

    def closeEvent(self, event):
        # Never let a running scan thread outlive the dialog - that aborts Qt.
        self._closing = True
        self._stop_thread()
        super().closeEvent(event)

    def _clear_groups(self):
        while self.groups_layout.count() > 1:      # keep the trailing stretch
            item = self.groups_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _render_groups(self):
        self._clear_groups()
        dup_count = sum(len(g) - 1 for g in self.groups)
        if not self.groups:
            self.status_label.setText(
                f'<span style="color:{COLOR_GREEN};">{tr.t("dupfinder.none")}</span>')
            self.delete_btn.setVisible(False)
            return
        status = tr.t("dupfinder.found", color=accent(), count=dup_count, sets=len(self.groups))
        # Only build cards for the first N sets - thousands of thumbnail widgets
        # would freeze the UI. Deletion still covers every set.
        shown = self.groups[:_MAX_GROUPS_SHOWN]
        if len(self.groups) > _MAX_GROUPS_SHOWN:
            status += "<br>" + tr.t("dupfinder.showing", shown=len(shown), total=len(self.groups))
        self.status_label.setText(status)
        for idx, group in enumerate(shown, 1):
            self.groups_layout.insertWidget(self.groups_layout.count() - 1,
                                            self._build_group(idx, group))
        self.delete_btn.setVisible(True)
        self._render_delete_btn()

    def _build_group(self, idx, group):
        card = QFrame()
        card.setProperty("card", "true")
        v = QVBoxLayout(card)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(8)
        header = QLabel(tr.t("dupfinder.set_header", index=idx, count=len(group)))
        header.setProperty("muted", "true")
        v.addWidget(header)
        for i, path in enumerate(group):
            v.addLayout(self._build_row(path, keep=(i == 0)))
        return card

    def _build_row(self, path, keep):
        row = QHBoxLayout()
        row.setSpacing(10)
        thumb = QLabel()
        thumb.setFixedSize(_THUMB, _THUMB)
        thumb.setAlignment(Qt.AlignCenter)
        pix = self._thumb(path)
        if pix:
            thumb.setPixmap(pix)
        else:
            thumb.setText("🎞")
        row.addWidget(thumb)

        info = QVBoxLayout()
        info.setSpacing(2)
        name = QLabel(os.path.basename(path))
        try:
            size = human_size(os.path.getsize(path))
        except OSError:
            size = ""
        tag_color = COLOR_GREEN if keep else COLOR_ORANGE
        tag = tr.t("dupfinder.keep") if keep else tr.t("dupfinder.duplicate")
        meta = QLabel(f'<span style="color:{tag_color}; font-weight:bold;">{tag}</span>'
                      f'&nbsp;&nbsp;<span style="color:#8A8D96;">{size}</span>')
        meta.setTextFormat(Qt.RichText)
        info.addWidget(name)
        info.addWidget(meta)
        row.addLayout(info, 1)
        return row

    def _thumb(self, path):
        if os.path.splitext(path)[1].lower() not in PHOTO_EXT:
            return None
        pix = QPixmap(path)
        if pix.isNull():
            return None
        return pix.scaled(QSize(_THUMB, _THUMB), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _render_delete_btn(self):
        dup_count = sum(len(g) - 1 for g in self.groups)
        self.delete_btn.setText(tr.t("dupfinder.delete", count=dup_count))

    def _delete(self):
        dup_count = sum(len(g) - 1 for g in self.groups)
        if not dup_count:
            return
        confirm = QMessageBox.question(
            self, tr.t("dupfinder.confirm_title"),
            tr.t("dupfinder.confirm", count=dup_count),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        deleted = 0
        for group in self.groups:
            for path in group[1:]:              # keep the first, delete the rest
                try:
                    os.remove(path)
                    deleted += 1
                except OSError:
                    pass
        self.groups = []
        self._clear_groups()
        self.delete_btn.setVisible(False)
        self.status_label.setText(
            f'<span style="color:{COLOR_GREEN};">{tr.t("dupfinder.deleted", count=deleted)}</span>')

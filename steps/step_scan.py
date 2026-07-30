import sys
import os
from PySide6.QtWidgets import (
    QApplication, QPushButton, QLineEdit, QFileDialog, QLabel, QProgressBar,
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal, QObject, Qt
from sorter_logic import scan_source
from sorter_logic.fsutil import human_size
from sorter_logic.theme import mark_primary, mark_secondary, accent
from sorter_logic.i18n import translator as tr
from sorter_logic.settings_store import load_enabled_extensions
from steps.file_types_dialog import FileTypesDialog
from paths import resource_path


class ScanWorker(QObject):
    finished = Signal(dict)

    def __init__(self, paths, allowed_extensions):
        super().__init__()
        self.paths = paths
        self.allowed_extensions = allowed_extensions

    def run(self):
        # Fast count only (no per-file reading) so scanning is instant even on
        # a huge library. Duplicates are handled during sorting instead.
        result = scan_source(self.paths, self.allowed_extensions)
        self.finished.emit(result)


class SourceStep(QObject):
    continue_requested = Signal()
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/step1_source.ui"))
        ui_file.open(QFile.ReadOnly)

        self.window = loader.load(ui_file)
        self.title_label = self.window.findChild(QLabel, "label")
        self.subtitle_label = self.window.findChild(QLabel, "label_2")
        self.paths_scroll = self.window.findChild(QScrollArea, "pathsScroll")
        self.paths_layout = self.window.findChild(QVBoxLayout, "pathsLayout")
        self.add_path_btn = self.window.findChild(QPushButton, "addPathButton")
        self.choose_folder_label = self.window.findChild(QLabel, "chooseFolderLabel")
        self.scan_btn = self.window.findChild(QPushButton, "scanFolderButton")
        self.progress_bar = self.window.findChild(QProgressBar, "scanProgressBar")
        self.status_label = self.window.findChild(QLabel, "statusLabel")
        self.found_types_label = self.window.findChild(QLabel, "foundTypesLabel")
        self.continue_btn = self.window.findChild(QPushButton, "continueButton")
        self.back_btn = self.window.findChild(QPushButton, "backButton")
        self.file_types_btn = self.window.findChild(QPushButton, "fileTypesButton")

        self.title_label.setProperty("heading", "true")
        self.subtitle_label.setProperty("subheading", "true")
        self.choose_folder_label.setProperty("muted", "true")
        self.status_label.setProperty("muted", "true")
        self.found_types_label.setProperty("muted", "true")
        mark_primary(self.continue_btn)
        mark_secondary(self.scan_btn)
        mark_secondary(self.back_btn)
        mark_secondary(self.file_types_btn)
        mark_secondary(self.add_path_btn)

        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()

        self.scan_result = None
        self.last_found_ext = None
        self.path_rows = []          # list of {widget, edit, choose, remove}
        # Leave room on the right so rows don't slide under the overlay
        # scrollbar. The scroll area's height tracks the row count (see
        # _update_scroll_height) up to a few rows, then it scrolls. Keep the
        # scroll area and its viewport fully transparent so the rounded rows sit
        # cleanly on the content pane - no ugly sharp-cornered box behind them.
        self.paths_layout.setContentsMargins(0, 0, 10, 0)
        self.paths_scroll.setFrameShape(QFrame.NoFrame)
        self.paths_scroll.viewport().setStyleSheet("background: transparent;")

        self.add_path_btn.clicked.connect(lambda: self._add_row(browse=True))
        self.scan_btn.clicked.connect(self.scan_folder)
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.file_types_btn.clicked.connect(self.open_file_types)

        self.thread = None
        self.worker = None

        self._add_row()             # start with one empty row
        self.retranslate()

    # --- dynamic path rows ---------------------------------------------------
    def _add_row(self, path="", browse=False):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        edit = QLineEdit()
        edit.setReadOnly(True)
        edit.setText(path)
        edit.setPlaceholderText(tr.t("source.row_placeholder"))
        choose = QPushButton()
        mark_secondary(choose)
        remove = QPushButton("✕")
        remove.setObjectName("rowRemove")
        remove.setFixedSize(30, 36)
        remove.setCursor(Qt.PointingHandCursor)
        h.addWidget(edit, 1)
        h.addWidget(choose)
        h.addWidget(remove)

        entry = {"widget": row, "edit": edit, "choose": choose, "remove": remove}
        choose.clicked.connect(lambda: self._browse_row(entry))
        remove.clicked.connect(lambda: self._remove_row(entry))
        self.path_rows.append(entry)
        self.paths_layout.addWidget(row)
        self._retranslate_rows()
        self._update_rows_state()
        if browse:
            self._browse_row(entry)

    def _browse_row(self, entry):
        folder = QFileDialog.getExistingDirectory(self.window, tr.t("source.title"))
        if folder:
            entry["edit"].setText(folder)
            self._invalidate_scan()
            self._update_rows_state()

    def _remove_row(self, entry):
        if len(self.path_rows) <= 1:
            entry["edit"].setText("")          # keep one row, just clear it
        else:
            self.path_rows.remove(entry)
            self.paths_layout.removeWidget(entry["widget"])
            entry["widget"].deleteLater()
        self._invalidate_scan()
        self._update_rows_state()

    def _selected_paths(self):
        seen, out = set(), []
        for e in self.path_rows:
            p = e["edit"].text().strip()
            if p and p not in seen:
                seen.add(p)
                out.append(p)
        return out

    def _update_rows_state(self):
        only_one = len(self.path_rows) <= 1
        for e in self.path_rows:
            e["remove"].setEnabled(not only_one)
        self.scan_btn.setEnabled(bool(self._selected_paths()))
        self._update_scroll_height()

    def _update_scroll_height(self):
        # Fit the visible rows exactly (up to 3), then let the rest scroll.
        visible = min(max(len(self.path_rows), 1), 3)
        self.paths_scroll.setFixedHeight(visible * 44 + 8)

    def _invalidate_scan(self):
        self.scan_result = None
        self.last_found_ext = None
        self.continue_btn.setEnabled(False)
        self._render_status_label()
        self._render_found_types_label()

    # --- rendering -----------------------------------------------------------
    def retranslate(self):
        self.title_label.setText(tr.t("source.title"))
        self.subtitle_label.setText(tr.t("source.subtitle"))
        self.add_path_btn.setText(tr.t("source.add_path"))
        self.scan_btn.setText(tr.t("source.scan_folder"))
        self.continue_btn.setText(tr.t("common.next"))
        self.back_btn.setText(tr.t("common.back"))
        self.file_types_btn.setText(tr.t("source.file_types"))
        self._retranslate_rows()
        self.choose_folder_label.setText("")
        self._render_status_label()
        self._render_found_types_label()

    def _retranslate_rows(self):
        for e in self.path_rows:
            e["choose"].setText(tr.t("source.choose_row"))
            e["remove"].setToolTip(tr.t("source.remove_tooltip"))

    def _render_status_label(self):
        r = self.scan_result
        if r is None:
            self.status_label.setText("")
            return
        if r["total"] == 0 and r.get("non_media", 0) == 0:
            self.status_label.setText(tr.t("source.scan_none_found"))
            return
        media_size = r.get("total_size", 0)
        non_media = r.get("non_media", 0)
        non_media_size = r.get("non_media_size", 0)
        lines = [
            tr.t("source.scan_found", color=accent(), total=r["total"], folders=r["folders"]),
            tr.t("source.scan_media", size=human_size(media_size)),
            tr.t("source.scan_other", color=accent(), count=non_media, size=human_size(non_media_size)),
            tr.t("source.scan_grand", count=r["total"] + non_media,
                 size=human_size(media_size + non_media_size)),
        ]
        self.status_label.setText("<br>".join(lines))

    def _render_found_types_label(self):
        found = self.last_found_ext
        if not found:
            self.found_types_label.setText("")
            return
        enabled = load_enabled_extensions()
        parts = []
        for ext, n in sorted(found.items(), key=lambda kv: -kv[1]):
            key = "source.type_enabled" if ext in enabled else "source.type_disabled"
            parts.append(tr.t(key, ext=ext, n=n))
        breakdown = tr.t("source.found_types", breakdown=", ".join(parts))
        self.found_types_label.setText(f"{breakdown}\n{tr.t('source.found_types_hint')}")

    # --- data / flow ---------------------------------------------------------
    def get_data(self):
        return {
            "src_paths": self._selected_paths(),
            "scan_result": self.scan_result,
            "allowed_extensions": load_enabled_extensions(),
        }

    def open_file_types(self):
        had_scan = self.scan_result is not None
        if FileTypesDialog(self.window).exec() and had_scan:
            # File-type selection changed after a scan already ran - the counts
            # no longer reflect what would be sorted, so force a re-scan.
            self.scan_result = None
            self.continue_btn.setEnabled(False)
            self._render_status_label()
            self._render_found_types_label()

    def reset(self):
        for e in self.path_rows:
            self.paths_layout.removeWidget(e["widget"])
            e["widget"].deleteLater()
        self.path_rows = []
        self.scan_result = None
        self.last_found_ext = None
        self._add_row()
        self.continue_btn.setEnabled(False)
        self.choose_folder_label.setText("")
        self._render_status_label()
        self._render_found_types_label()

    def on_scan_finished(self, result):
        self.progress_bar.hide()
        self.scan_result = result
        self.last_found_ext = result.get("found_ext")
        self._render_status_label()
        self._render_found_types_label()
        self.continue_btn.setEnabled(result["total"] != 0)
        self.scan_btn.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def scan_folder(self):
        paths = self._selected_paths()
        if not paths:
            return

        self.scan_btn.setEnabled(False)
        # Indeterminate "busy" bar - fingerprinting for duplicates takes a
        # moment and we don't track per-file progress here.
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()

        self.thread = QThread()
        self.worker = ScanWorker(paths, load_enabled_extensions())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_scan_finished)
        self.thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    step = SourceStep()
    step.window.show()
    app.exec()

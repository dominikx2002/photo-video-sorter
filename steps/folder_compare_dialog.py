import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
)
from PySide6.QtCore import Qt, QObject, QThread, Signal
from sorter_logic import scan_source
from sorter_logic.theme import mark_primary, mark_secondary, COLOR_GREEN, accent
from sorter_logic.i18n import translator as tr


class _CompareWorker(QObject):
    finished = Signal(dict)

    def __init__(self, path_a, path_b):
        super().__init__()
        self.path_a = path_a
        self.path_b = path_b

    def run(self):
        self.finished.emit({
            "a": scan_source(self.path_a),
            "b": scan_source(self.path_b),
        })


class FolderCompareDialog(QDialog):
    """Standalone tool: pick two folders, scan both, and see how many photos
    and videos each holds - a quick way to check whether two locations match."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(False)
        self.setMinimumSize(580, 380)
        self.path_a = ""
        self.path_b = ""
        self.thread = None
        self.worker = None

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

        layout.addSpacing(6)
        self.a_label, self.a_edit, self.a_btn = self._make_row(layout, self._choose_a)
        self.b_label, self.b_edit, self.b_btn = self._make_row(layout, self._choose_b)

        self.compare_btn = QPushButton()
        mark_primary(self.compare_btn)
        self.compare_btn.clicked.connect(self._compare)
        layout.addSpacing(4)
        layout.addWidget(self.compare_btn)

        self.result_label = QLabel()
        self.result_label.setTextFormat(Qt.RichText)
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        layout.addStretch(1)

        self.close_btn = QPushButton()
        mark_secondary(self.close_btn)
        self.close_btn.clicked.connect(self.close)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.close_btn)
        layout.addLayout(row)

        self.retranslate()
        tr.language_changed.connect(self.retranslate)

    def _make_row(self, layout, on_choose):
        row = QHBoxLayout()
        label = QLabel()
        label.setMinimumWidth(70)
        edit = QLineEdit()
        edit.setReadOnly(True)
        btn = QPushButton()
        mark_secondary(btn)
        btn.clicked.connect(on_choose)
        row.addWidget(label)
        row.addWidget(edit, 1)
        row.addWidget(btn)
        layout.addLayout(row)
        return label, edit, btn

    def retranslate(self, *_):
        self.setWindowTitle(tr.t("compare.title"))
        self.title_label.setText(tr.t("compare.title"))
        self.subtitle_label.setText(tr.t("compare.subtitle"))
        self.a_label.setText(tr.t("compare.folder_a"))
        self.b_label.setText(tr.t("compare.folder_b"))
        self.a_btn.setText(tr.t("compare.choose"))
        self.b_btn.setText(tr.t("compare.choose"))
        self.compare_btn.setText(tr.t("compare.compare"))
        self.close_btn.setText(tr.t("settings.close"))

    def closeEvent(self, event):
        # Don't leave a scan thread running when the window closes.
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        super().closeEvent(event)

    def _choose_a(self):
        folder = QFileDialog.getExistingDirectory(self, tr.t("compare.folder_a"))
        if folder:
            self.path_a = folder
            self.a_edit.setText(folder)

    def _choose_b(self):
        folder = QFileDialog.getExistingDirectory(self, tr.t("compare.folder_b"))
        if folder:
            self.path_b = folder
            self.b_edit.setText(folder)

    def _compare(self):
        if not (self.path_a and self.path_b):
            self.result_label.setText(
                f'<span style="color:{accent()};">{tr.t("compare.pick_both")}</span>'
            )
            return
        self.compare_btn.setEnabled(False)
        self.result_label.setText(tr.t("compare.scanning"))

        self.thread = QThread()
        self.worker = _CompareWorker(self.path_a, self.path_b)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_finished)
        self.thread.start()

    def _on_finished(self, result):
        self.compare_btn.setEnabled(True)
        if self.thread:
            self.thread.quit()
            self.thread.wait()

        name_a = os.path.basename(os.path.normpath(self.path_a)) or self.path_a
        name_b = os.path.basename(os.path.normpath(self.path_b)) or self.path_b
        count_a = result["a"]["total"]
        count_b = result["b"]["total"]

        lines = [
            tr.t("compare.count", name=name_a, count=count_a),
            tr.t("compare.count", name=name_b, count=count_b),
            "",
        ]
        if count_a == count_b:
            verdict = f'<span style="color:{COLOR_GREEN};">{tr.t("compare.same")}</span>'
        else:
            more, less, n = ((name_a, name_b, count_a - count_b) if count_a > count_b
                             else (name_b, name_a, count_b - count_a))
            verdict = f'<b>{tr.t("compare.diff", more=more, less=less, n=n)}</b>'
        lines.append(verdict)
        self.result_label.setText("<br>".join(lines))

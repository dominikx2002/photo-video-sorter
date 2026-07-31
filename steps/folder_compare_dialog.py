import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QWidget, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, QObject, QThread, Signal
from sorter_logic import scan_source
from sorter_logic.fsutil import human_size
from sorter_logic.theme import mark_primary, mark_secondary, accent, COLOR_GREEN
from sorter_logic.i18n import translator as tr


class _FolderList(QWidget):
    """A little add/remove list of folder rows: [path | Choose | x] plus a
    '+ Add folder' button. paths() returns the chosen folders."""

    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog
        self.rows = []
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)
        # Rows live in a transparent scroll area that grows to fit up to a few
        # rows, then scrolls - the same behaviour as step 2.
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.viewport().setStyleSheet("background: transparent;")
        container = QWidget()
        self.rows_layout = QVBoxLayout(container)
        self.rows_layout.setContentsMargins(0, 0, 10, 0)
        self.rows_layout.setSpacing(6)
        self.scroll.setWidget(container)
        outer.addWidget(self.scroll)
        self.add_btn = QPushButton()
        mark_secondary(self.add_btn)
        self.add_btn.clicked.connect(lambda: self.add_row())
        outer.addWidget(self.add_btn)
        self.add_row()

    def add_row(self, path="", browse=False):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        edit = QLineEdit()
        edit.setReadOnly(True)
        edit.setText(path)
        edit.setPlaceholderText(tr.t("source.row_placeholder"))
        choose = QPushButton(tr.t("compare.choose"))
        mark_secondary(choose)
        remove = QPushButton("✕")
        remove.setObjectName("rowRemove")
        remove.setFixedSize(30, 36)
        remove.setCursor(Qt.PointingHandCursor)
        h.addWidget(edit, 1)
        h.addWidget(choose)
        h.addWidget(remove)
        entry = {"widget": row, "edit": edit, "choose": choose, "remove": remove}
        choose.clicked.connect(lambda: self._browse(entry))
        remove.clicked.connect(lambda: self._remove(entry))
        self.rows.append(entry)
        self.rows_layout.addWidget(row)
        self._update_state()
        if browse:
            self._browse(entry)

    def _browse(self, entry):
        folder = QFileDialog.getExistingDirectory(self.dialog, tr.t("compare.choose"))
        if folder:
            entry["edit"].setText(folder)

    def _remove(self, entry):
        if len(self.rows) <= 1:
            entry["edit"].setText("")
        else:
            self.rows.remove(entry)
            self.rows_layout.removeWidget(entry["widget"])
            entry["widget"].deleteLater()
        self._update_state()

    def _update_state(self):
        multiple = len(self.rows) > 1
        for e in self.rows:
            e["remove"].setVisible(multiple)
        visible = min(max(len(self.rows), 1), 3)
        self.scroll.setFixedHeight(visible * 44 + 8)

    def paths(self):
        seen, out = set(), []
        for e in self.rows:
            p = e["edit"].text().strip()
            if p and p not in seen:
                seen.add(p)
                out.append(p)
        return out

    def retranslate(self):
        self.add_btn.setText(tr.t("compare.add"))
        for e in self.rows:
            e["choose"].setText(tr.t("compare.choose"))


class _CompareWorker(QObject):
    finished = Signal(dict)

    def __init__(self, paths_a, paths_b):
        super().__init__()
        self.paths_a = paths_a
        self.paths_b = paths_b

    def run(self):
        self.finished.emit({
            "a": scan_source(self.paths_a),
            "b": scan_source(self.paths_b),
        })


class FolderCompareDialog(QDialog):
    """Pick any number of folders on each side, scan them all, and see a full
    breakdown - photos/videos, other files, and sizes - for each side."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(False)
        self.setMinimumSize(600, 620)
        self.thread = None
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(10)

        self.title_label = QLabel()
        self.title_label.setProperty("heading", "true")
        layout.addWidget(self.title_label)
        self.subtitle_label = QLabel()
        self.subtitle_label.setProperty("subheading", "true")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.a_label = QLabel()
        self.a_label.setProperty("muted", "true")
        layout.addWidget(self.a_label)
        self.list_a = _FolderList(self)
        layout.addWidget(self.list_a)

        self.b_label = QLabel()
        self.b_label.setProperty("muted", "true")
        layout.addWidget(self.b_label)
        self.list_b = _FolderList(self)
        layout.addWidget(self.list_b)

        self.compare_btn = QPushButton()
        mark_primary(self.compare_btn)
        self.compare_btn.clicked.connect(self._compare)
        layout.addSpacing(2)
        layout.addWidget(self.compare_btn)

        self.result_label = QLabel()
        self.result_label.setTextFormat(Qt.RichText)
        self.result_label.setWordWrap(True)
        self.result_label.setAlignment(Qt.AlignTop)
        layout.addWidget(self.result_label, 1)

        row = QHBoxLayout()
        row.addStretch(1)
        self.close_btn = QPushButton()
        mark_secondary(self.close_btn)
        self.close_btn.clicked.connect(self.close)
        row.addWidget(self.close_btn)
        layout.addLayout(row)

        self.retranslate()
        tr.language_changed.connect(self.retranslate)

    def retranslate(self, *_):
        self.setWindowTitle(tr.t("compare.title"))
        self.title_label.setText(tr.t("compare.title"))
        self.subtitle_label.setText(tr.t("compare.subtitle"))
        self.a_label.setText(tr.t("compare.group_a"))
        self.b_label.setText(tr.t("compare.group_b"))
        self.compare_btn.setText(tr.t("compare.compare"))
        self.close_btn.setText(tr.t("settings.close"))
        self.list_a.retranslate()
        self.list_b.retranslate()

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        super().closeEvent(event)

    def _compare(self):
        pa, pb = self.list_a.paths(), self.list_b.paths()
        if not (pa and pb):
            self.result_label.setText(
                f'<span style="color:{accent()};">{tr.t("compare.pick_both")}</span>')
            return
        self.compare_btn.setEnabled(False)
        self.result_label.setText(tr.t("compare.scanning"))
        self.thread = QThread()
        self.worker = _CompareWorker(pa, pb)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_finished)
        self.thread.start()

    def _side_html(self, label, r):
        media, media_sz = r["total"], r["total_size"]
        other, other_sz = r["non_media"], r["non_media_size"]
        return (f'<b>{label}</b><br>'
                f'{tr.t("compare.side_media", count=media, size=human_size(media_sz))}<br>'
                f'{tr.t("compare.side_other", count=other, size=human_size(other_sz))}<br>'
                f'{tr.t("compare.side_total", count=media + other, size=human_size(media_sz + other_sz))}')

    def _on_finished(self, result):
        self.compare_btn.setEnabled(True)
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        ra, rb = result["a"], result["b"]
        parts = [self._side_html(tr.t("compare.side_a"), ra), "",
                 self._side_html(tr.t("compare.side_b"), rb), ""]
        ca, cb = ra["total"], rb["total"]
        if ca == cb:
            verdict = f'<span style="color:{COLOR_GREEN};">{tr.t("compare.verdict_same", count=ca)}</span>'
        else:
            more, less, n = (("A", "B", ca - cb) if ca > cb else ("B", "A", cb - ca))
            verdict = f'<b>{tr.t("compare.verdict_more", more=more, less=less, n=n)}</b>'
        parts.append(verdict)
        self.result_label.setText("<br>".join(parts))

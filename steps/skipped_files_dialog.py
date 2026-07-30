import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
)
from PySide6.QtCore import Qt
from sorter_logic.fsutil import human_size
from sorter_logic.theme import mark_primary, mark_secondary
from sorter_logic.i18n import translator as tr


class SkippedFilesDialog(QDialog):
    """Lists the non-media files that were left in the source folders (not
    copied), so the user knows exactly what still needs handling before they
    delete or move the originals."""

    def __init__(self, files, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(640, 480)
        self.files = list(files)

        total_size = 0
        for f in self.files:
            try:
                total_size += os.path.getsize(f)
            except OSError:
                pass

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(10)

        title = QLabel(tr.t("skipped.title"))
        title.setProperty("heading", "true")
        layout.addWidget(title)
        subtitle = QLabel(tr.t("skipped.subtitle", count=len(self.files), size=human_size(total_size)))
        subtitle.setProperty("subheading", "true")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setObjectName("logView")            # reuse the monospace terminal look
        self.view.setPlainText("\n".join(self.files))
        layout.addWidget(self.view, 1)

        nav = QHBoxLayout()
        self.reveal_btn = QPushButton(tr.t("skipped.reveal"))
        mark_secondary(self.reveal_btn)
        self.reveal_btn.clicked.connect(self._reveal_first)
        close_btn = QPushButton(tr.t("settings.close"))
        mark_primary(close_btn)
        close_btn.clicked.connect(self.accept)
        nav.addWidget(self.reveal_btn)
        nav.addStretch(1)
        nav.addWidget(close_btn)
        layout.addLayout(nav)

    def _reveal_first(self):
        if not self.files:
            return
        folder = os.path.dirname(self.files[0])
        if not os.path.isdir(folder):
            return
        if sys.platform == "darwin":
            subprocess.run(["open", folder])
        elif sys.platform == "win32":
            os.startfile(folder)
        else:
            subprocess.run(["xdg-open", folder])

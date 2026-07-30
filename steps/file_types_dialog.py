from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QCheckBox, QPushButton,
    QFrame, QScrollArea, QWidget
)
from sorter_logic.constants import PHOTO_EXT, VIDEO_EXT
from sorter_logic.settings_store import load_enabled_extensions, save_enabled_extensions
from sorter_logic.i18n import translator as tr
from sorter_logic.theme import mark_primary, mark_secondary

COLUMNS = 4


class FileTypesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setFixedSize(460, 560)

        enabled = load_enabled_extensions()
        self.checkboxes = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 18)

        self.title_label = QLabel()
        self.title_label.setProperty("heading", "true")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setProperty("subheading", "true")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        # There are many extensions now, so the checkbox grids live in a
        # scroll area between the header and the buttons.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.viewport().setStyleSheet("background: transparent;")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 4, 8, 0)

        self.photos_label = QLabel()
        self.photos_label.setProperty("muted", "true")
        content_layout.addWidget(self.photos_label)
        content_layout.addLayout(self._build_grid(sorted(PHOTO_EXT), enabled))

        self.videos_label = QLabel()
        self.videos_label.setProperty("muted", "true")
        content_layout.addWidget(self.videos_label)
        content_layout.addLayout(self._build_grid(sorted(VIDEO_EXT), enabled))
        content_layout.addStretch(1)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        select_row = QHBoxLayout()
        self.select_all_btn = QPushButton()
        self.select_none_btn = QPushButton()
        mark_secondary(self.select_all_btn)
        mark_secondary(self.select_none_btn)
        self.select_all_btn.clicked.connect(lambda: self._set_all(True))
        self.select_none_btn.clicked.connect(lambda: self._set_all(False))
        select_row.addWidget(self.select_all_btn)
        select_row.addWidget(self.select_none_btn)
        select_row.addStretch(1)
        layout.addLayout(select_row)

        self.close_btn = QPushButton()
        mark_primary(self.close_btn)
        self.close_btn.clicked.connect(self._save_and_close)
        layout.addWidget(self.close_btn)

        self.retranslate()
        tr.language_changed.connect(self.retranslate)

    def _build_grid(self, extensions, enabled):
        grid = QGridLayout()
        grid.setContentsMargins(0, 4, 0, 12)
        for i, ext in enumerate(extensions):
            cb = QCheckBox(ext)
            cb.setChecked(ext in enabled)
            self.checkboxes[ext] = cb
            grid.addWidget(cb, i // COLUMNS, i % COLUMNS)
        return grid

    def _set_all(self, checked):
        for cb in self.checkboxes.values():
            cb.setChecked(checked)

    def _save_and_close(self):
        chosen = {ext for ext, cb in self.checkboxes.items() if cb.isChecked()}
        save_enabled_extensions(chosen)
        self.accept()

    def retranslate(self):
        self.setWindowTitle(tr.t("filetypes.title"))
        self.title_label.setText(tr.t("filetypes.title"))
        self.subtitle_label.setText(tr.t("filetypes.subtitle"))
        self.photos_label.setText(tr.t("filetypes.photos"))
        self.videos_label.setText(tr.t("filetypes.videos"))
        self.select_all_btn.setText(tr.t("filetypes.select_all"))
        self.select_none_btn.setText(tr.t("filetypes.select_none"))
        self.close_btn.setText(tr.t("settings.close"))

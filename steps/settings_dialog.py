from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from sorter_logic.i18n import translator as tr, LANGUAGES
from sorter_logic.settings_store import save_language
from sorter_logic.theme import mark_primary


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setFixedSize(360, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 18)

        self.title_label = QLabel()
        self.title_label.setProperty("heading", "true")
        layout.addWidget(self.title_label)

        row = QHBoxLayout()
        self.language_label = QLabel()
        row.addWidget(self.language_label)
        self.language_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.setCurrentIndex(self.language_combo.findData(tr.language()))
        row.addWidget(self.language_combo, 1)
        layout.addLayout(row)

        self.note_label = QLabel()
        self.note_label.setProperty("muted", "true")
        self.note_label.setWordWrap(True)
        layout.addWidget(self.note_label)

        layout.addStretch(1)

        self.close_btn = QPushButton()
        mark_primary(self.close_btn)
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn, 0)

        self.language_combo.currentIndexChanged.connect(self._on_language_changed)

        self.retranslate()
        tr.language_changed.connect(self.retranslate)

    def _on_language_changed(self, index):
        code = self.language_combo.itemData(index)
        if code:
            save_language(code)
            tr.set_language(code)

    def retranslate(self):
        self.setWindowTitle(tr.t("settings.title"))
        self.title_label.setText(tr.t("settings.title"))
        self.language_label.setText(tr.t("settings.language") + ":")
        self.note_label.setText(tr.t("settings.note"))
        self.close_btn.setText(tr.t("settings.close"))

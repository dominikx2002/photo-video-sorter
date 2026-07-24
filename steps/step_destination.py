import sys
import time
import os
from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit, QFileDialog, QLabel, QCheckBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QObject, QEvent, Signal
from sorter_logic.constants import THEME_COLOR
from sorter_logic.theme import mark_primary, mark_secondary
from paths import resource_path

class DestinationStep(QObject):
    continue_requested = Signal()
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("step2_destination.ui"))
        ui_file.open(QFile.ReadOnly)

        self.window = loader.load(ui_file)
        self.title_label = self.window.findChild(QLabel, "label")
        self.subtitle_label = self.window.findChild(QLabel, "label_2")
        self.collection_name_edit = self.window.findChild(QLineEdit, "collectionNameEdit")
        self.dest_path_edit = self.window.findChild(QLineEdit, "destPathEdit")
        self.choose_dest_btn = self.window.findChild(QPushButton, "chooseDestButton")
        self.use_folder_date_checkbox = self.window.findChild(QCheckBox, "useFolderDateCheckbox")
        self.path_preview_label = self.window.findChild(QLabel, "pathPreviewLabel")
        self.continue_btn = self.window.findChild(QPushButton, "continueButton")
        self.back_btn = self.window.findChild(QPushButton, "backButton")

        self.title_label.setProperty("heading", "true")
        self.subtitle_label.setProperty("subheading", "true")
        self.path_preview_label.setProperty("muted", "true")
        mark_primary(self.continue_btn)
        mark_secondary(self.choose_dest_btn)
        mark_secondary(self.back_btn)

        self.choose_dest_btn.clicked.connect(self.choose_destination_folder)
        self.collection_name_edit.textChanged.connect(self.update_preview)
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)

        self.window.installEventFilter(self)
        self.window.setFocus()
        self.update_preview()

    def get_data(self):
        return {
            "collection_name": self.collection_name_edit.text().strip(),
            "dest_path": self.dest_path_edit.text().strip(),
            "use_folder_date": self.use_folder_date_checkbox.isChecked(),
        }

    def reset(self):
        self.collection_name_edit.setText("")
        self.dest_path_edit.setText("")
        self.use_folder_date_checkbox.setChecked(True)
        self.update_preview()

    def eventFilter(self, obj, event):
        if obj is self.window and event.type() == QEvent.MouseButtonPress:
            focused = QApplication.focusWidget()
            if focused in (self.collection_name_edit, self.dest_path_edit):
                focused.clearFocus()
        return super().eventFilter(obj, event)

    def choose_destination_folder(self):
        self.collection_name_edit.clearFocus()
        folder = QFileDialog.getExistingDirectory(self.window, "Select the destination folder")
        if folder:
            self.dest_path_edit.setText(folder)
            self.update_preview()

    def update_preview(self):
        name = self.collection_name_edit.text()
        dest = os.path.normpath(self.dest_path_edit.text()) if self.dest_path_edit.text() else ""

        if dest:
            if name:
                self.path_preview_label.setText(f"Your files will be organized like this:\n"
                    f"{dest}/{name}/YYYY/YYYY-MM/")
            else:
                self.path_preview_label.setText(f"Your files will be organized like this:\n"
                    f"{dest}/YYYY/YYYY-MM/")
            self.continue_btn.setEnabled(True)
        else:
            self.path_preview_label.setText("Destination path will appear here.")
            self.continue_btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    step = DestinationStep()
    step.window.show()
    app.exec()

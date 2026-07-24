import sys
import time
import os
from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit, QFileDialog, QLabel, QCheckBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QObject, QEvent, Signal
from sorter_logic.constants import THEME_COLOR
from sorter_logic.theme import mark_primary, mark_secondary
from sorter_logic.i18n import translator as tr
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
        self.collection_name_label = self.window.findChild(QLabel, "label_3")
        self.collection_name_edit = self.window.findChild(QLineEdit, "collectionNameEdit")
        self.dest_path_edit = self.window.findChild(QLineEdit, "destPathEdit")
        self.choose_dest_btn = self.window.findChild(QPushButton, "chooseDestButton")
        self.use_filename_date_checkbox = self.window.findChild(QCheckBox, "useFilenameDateCheckbox")
        self.use_mtime_checkbox = self.window.findChild(QCheckBox, "useMtimeCheckbox")
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

        self.retranslate()

    def retranslate(self):
        self.title_label.setText(tr.t("destination.title"))
        self.subtitle_label.setText(tr.t("destination.subtitle"))
        self.collection_name_label.setText(tr.t("destination.collection_name"))
        self.choose_dest_btn.setText(tr.t("destination.choose_folder"))
        self.use_filename_date_checkbox.setText(tr.t("destination.use_filename_date"))
        self.use_mtime_checkbox.setText(tr.t("destination.use_mtime"))
        self.use_folder_date_checkbox.setText(tr.t("destination.use_folder_date"))
        self.continue_btn.setText(tr.t("common.next"))
        self.back_btn.setText(tr.t("common.back"))
        self.update_preview()

    def get_data(self):
        return {
            "collection_name": self.collection_name_edit.text().strip(),
            "dest_path": self.dest_path_edit.text().strip(),
            "use_filename_date": self.use_filename_date_checkbox.isChecked(),
            "use_mtime": self.use_mtime_checkbox.isChecked(),
            "use_folder_date": self.use_folder_date_checkbox.isChecked(),
        }

    def reset(self):
        self.collection_name_edit.setText("")
        self.dest_path_edit.setText("")
        self.use_filename_date_checkbox.setChecked(True)
        self.use_mtime_checkbox.setChecked(True)
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
        folder = QFileDialog.getExistingDirectory(self.window, tr.t("destination.choose_folder"))
        if folder:
            self.dest_path_edit.setText(folder)
            self.update_preview()

    def update_preview(self):
        name = self.collection_name_edit.text()
        dest = os.path.normpath(self.dest_path_edit.text()) if self.dest_path_edit.text() else ""

        if dest:
            if name:
                self.path_preview_label.setText(tr.t("destination.preview_with_name", dest=dest, name=name))
            else:
                self.path_preview_label.setText(tr.t("destination.preview_no_name", dest=dest))
            self.continue_btn.setEnabled(True)
        else:
            self.path_preview_label.setText(tr.t("destination.preview_placeholder"))
            self.continue_btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    step = DestinationStep()
    step.window.show()
    app.exec()

import sys
import time
import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QPushButton, QLineEdit, QFileDialog, QLabel, QCheckBox,
    QWidget, QVBoxLayout, QToolButton, QScrollArea, QFrame, QSizePolicy, QComboBox,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QObject, QEvent, Signal, Qt
from sorter_logic.theme import mark_primary, mark_secondary, COLOR_GREEN, COLOR_ORANGE
from sorter_logic.i18n import translator as tr
from sorter_logic.fsutil import human_size
from sorter_logic.run_sort import FOLDER_TEMPLATES
from toggle_switch import ToggleSwitch
from paths import resource_path

class DestinationStep(QObject):
    continue_requested = Signal()
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/step2_destination.ui"))
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
        self.rename_to_date_checkbox = self.window.findChild(QCheckBox, "renameToDateCheckbox")
        self.path_preview_label = self.window.findChild(QLabel, "pathPreviewLabel")
        self.space_label = self.window.findChild(QLabel, "spaceLabel")
        self.continue_btn = self.window.findChild(QPushButton, "continueButton")
        self.back_btn = self.window.findChild(QPushButton, "backButton")

        self.title_label.setProperty("heading", "true")
        self.subtitle_label.setProperty("subheading", "true")
        self.path_preview_label.setProperty("muted", "true")
        self.space_label.setProperty("muted", "true")
        self.required_size_bytes = 0
        mark_primary(self.continue_btn)
        mark_secondary(self.choose_dest_btn)
        mark_secondary(self.back_btn)

        self.choose_dest_btn.clicked.connect(self.choose_destination_folder)
        self.collection_name_edit.textChanged.connect(self.update_preview)
        # rename toggle -> update_preview is wired in _build_advanced_section,
        # after the .ui checkbox is swapped for a toggle switch.
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)

        self._build_advanced_section()

        self.window.installEventFilter(self)
        self.window.setFocus()

        self.retranslate()

    def _build_advanced_section(self):
        """Tuck the four date-source options behind a collapsible "Advanced
        settings" header, each with a greyed, small-print explanation of exactly
        what it does. Collapsed by default; the defaults still apply while hidden."""
        layout = self.window.findChild(QVBoxLayout, "verticalLayout")

        # Drop the plain .ui checkboxes and replace them with Apple-style toggle
        # switches (built in code), keeping the same attribute names so the rest
        # of the class - get_data, reset - is unchanged. The 3 date fallbacks
        # default on, the rest off.
        insert_at = layout.indexOf(self.use_filename_date_checkbox)
        for cb in (self.use_filename_date_checkbox, self.use_mtime_checkbox,
                   self.use_folder_date_checkbox, self.rename_to_date_checkbox):
            layout.removeWidget(cb)
            cb.deleteLater()

        self.use_filename_date_checkbox = ToggleSwitch()
        self.use_mtime_checkbox = ToggleSwitch()
        self.use_folder_date_checkbox = ToggleSwitch()
        self.rename_to_date_checkbox = ToggleSwitch()
        self.move_checkbox = ToggleSwitch()
        for tog in (self.use_filename_date_checkbox, self.use_mtime_checkbox,
                    self.use_folder_date_checkbox):
            tog.setChecked(True)
        self.rename_to_date_checkbox.toggled.connect(self.update_preview)

        options = [
            (self.use_filename_date_checkbox, "destination.use_filename_date_desc"),
            (self.use_mtime_checkbox, "destination.use_mtime_desc"),
            (self.use_folder_date_checkbox, "destination.use_folder_date_desc"),
            (self.rename_to_date_checkbox, "destination.rename_to_date_desc"),
            (self.move_checkbox, "destination.move_desc"),
        ]

        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setObjectName("advancedToggle")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setCursor(Qt.PointingHandCursor)
        self.advanced_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.advanced_toggle.setArrowType(Qt.RightArrow)
        self.advanced_toggle.toggled.connect(self._on_advanced_toggled)

        self.advanced_container = QWidget()
        box = QVBoxLayout(self.advanced_container)
        box.setContentsMargins(0, 2, 0, 2)
        box.setSpacing(2)
        self.option_descs = []
        for cb, desc_key in options:
            box.addWidget(cb)
            desc = QLabel()
            desc.setObjectName("optionDesc")
            desc.setWordWrap(True)
            box.addWidget(desc)
            self.option_descs.append((desc, desc_key))

        # Folder-structure template picker.
        self.template_label = QLabel()
        self.template_label.setObjectName("optionHeading")
        box.addWidget(self.template_label)
        self.template_combo = QComboBox()
        for key in FOLDER_TEMPLATES:
            self.template_combo.addItem("", key)
        box.addWidget(self.template_combo)
        self.template_desc = QLabel()
        self.template_desc.setObjectName("optionDesc")
        self.template_desc.setWordWrap(True)
        box.addWidget(self.template_desc)

        # Give the expanded options a transparent scroll region that soaks up
        # whatever vertical room the (resizable) window offers, capped at the
        # content's own height - so it grows as you enlarge the window and the
        # scrollbar simply disappears once everything fits.
        self.advanced_scroll = QScrollArea()
        self.advanced_scroll.setWidgetResizable(True)
        self.advanced_scroll.setFrameShape(QFrame.NoFrame)
        self.advanced_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.advanced_scroll.viewport().setStyleSheet("background: transparent;")
        self.advanced_scroll.setWidget(self.advanced_container)
        self.advanced_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.advanced_scroll.setVisible(False)

        layout.insertWidget(insert_at, self.advanced_toggle)
        layout.insertWidget(insert_at + 1, self.advanced_scroll)
        layout.setStretchFactor(self.advanced_scroll, 1)   # grab space before the spacer

    def _on_advanced_toggled(self, checked):
        self.advanced_scroll.setVisible(checked)
        self.advanced_toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self._sync_advanced_height()

    def _sync_advanced_height(self):
        # Cap the scroll at the content's natural height so it never shows empty
        # space; below that the layout gives it less and it scrolls.
        if self.advanced_scroll.isVisible():
            self.advanced_scroll.setMaximumHeight(self.advanced_container.sizeHint().height())

    def retranslate(self):
        self.title_label.setText(tr.t("destination.title"))
        self.subtitle_label.setText(tr.t("destination.subtitle"))
        self.collection_name_label.setText(tr.t("destination.collection_name"))
        self.choose_dest_btn.setText(tr.t("destination.choose_folder"))
        self.advanced_toggle.setText(tr.t("destination.advanced"))
        self.use_filename_date_checkbox.setText(tr.t("destination.use_filename_date"))
        self.use_mtime_checkbox.setText(tr.t("destination.use_mtime"))
        self.use_folder_date_checkbox.setText(tr.t("destination.use_folder_date"))
        self.rename_to_date_checkbox.setText(tr.t("destination.rename_to_date"))
        self.move_checkbox.setText(tr.t("destination.move"))
        for desc, key in self.option_descs:
            desc.setText(tr.t(key))
        self.template_label.setText(tr.t("destination.template"))
        self.template_desc.setText(tr.t("destination.template_desc"))
        for i, key in enumerate(FOLDER_TEMPLATES):
            self.template_combo.setItemText(i, tr.t(f"destination.template_{key}"))
        self.continue_btn.setText(tr.t("common.next"))
        self.back_btn.setText(tr.t("common.back"))
        self.update_preview()

    def set_required_size(self, size_bytes):
        self.required_size_bytes = size_bytes or 0
        self.update_preview()

    def get_data(self):
        return {
            "collection_name": self.collection_name_edit.text().strip(),
            "dest_path": self.dest_path_edit.text().strip(),
            "use_filename_date": self.use_filename_date_checkbox.isChecked(),
            "use_mtime": self.use_mtime_checkbox.isChecked(),
            "use_folder_date": self.use_folder_date_checkbox.isChecked(),
            "rename_to_date": self.rename_to_date_checkbox.isChecked(),
            "move_files": self.move_checkbox.isChecked(),
            "folder_template": self.template_combo.currentData(),
        }

    def reset(self):
        self.collection_name_edit.setText("")
        self.dest_path_edit.setText("")
        self.use_filename_date_checkbox.setChecked(True)
        self.use_mtime_checkbox.setChecked(True)
        self.use_folder_date_checkbox.setChecked(True)
        self.rename_to_date_checkbox.setChecked(False)
        self.move_checkbox.setChecked(False)
        self.template_combo.setCurrentIndex(0)
        self.required_size_bytes = 0
        self.update_preview()

    def eventFilter(self, obj, event):
        if obj is self.window and event.type() == QEvent.MouseButtonPress:
            focused = QApplication.focusWidget()
            if focused in (self.collection_name_edit, self.dest_path_edit):
                focused.clearFocus()
        elif obj is self.window and event.type() == QEvent.Resize:
            self._sync_advanced_height()
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
        example_file = "2023-05-14 14.30.22.jpg" if self.rename_to_date_checkbox.isChecked() else "photo.jpg"

        if dest:
            if name:
                self.path_preview_label.setText(
                    tr.t("destination.preview_with_name", dest=dest, name=name, file=example_file)
                )
            else:
                self.path_preview_label.setText(
                    tr.t("destination.preview_no_name", dest=dest, file=example_file)
                )
            space_ok = self._render_space_label(dest)
            self.continue_btn.setEnabled(space_ok)
        else:
            self.path_preview_label.setText(tr.t("destination.preview_placeholder"))
            self.space_label.setText("")
            self.continue_btn.setEnabled(False)

    def _render_space_label(self, dest):
        if not self.required_size_bytes:
            self.space_label.setText("")
            return True
        try:
            free_bytes = shutil.disk_usage(dest).free
        except OSError:
            self.space_label.setText("")
            return True

        required = human_size(self.required_size_bytes)
        available = human_size(free_bytes)
        if free_bytes >= self.required_size_bytes:
            self.space_label.setText(
                f'<span style="color:{COLOR_GREEN};">{tr.t("destination.space_ok", required=required, available=available)}</span>'
            )
            return True
        else:
            self.space_label.setText(
                f'<span style="color:{COLOR_ORANGE}; font-weight:bold;">'
                f'{tr.t("destination.space_low", required=required, available=available)}</span>'
            )
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    step = DestinationStep()
    step.window.show()
    app.exec()

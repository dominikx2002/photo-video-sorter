import sys
import time
import os
from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit, QFileDialog, QLabel, QProgressBar
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal, QObject
from sorter_logic import scan_source
from sorter_logic.constants import THEME_COLOR
from sorter_logic.theme import mark_primary, mark_secondary
from sorter_logic.i18n import translator as tr
from paths import resource_path


class ScanWorker(QObject):
    finished = Signal(dict)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        time.sleep(1)
        result = scan_source(self.path)
        self.finished.emit(result)


class SourceStep(QObject):
    continue_requested = Signal()
    back_requested = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("step1_source.ui"))
        ui_file.open(QFile.ReadOnly)

        self.window = loader.load(ui_file)
        self.title_label = self.window.findChild(QLabel, "label")
        self.subtitle_label = self.window.findChild(QLabel, "label_2")
        self.choose_btn = self.window.findChild(QPushButton, "chooseFolderButton")
        self.src_path_edit = self.window.findChild(QLineEdit, "srcPathEdit")
        self.choose_folder_label = self.window.findChild(QLabel, "chooseFolderLabel")
        self.scan_btn = self.window.findChild(QPushButton, "scanFolderButton")
        self.progress_bar = self.window.findChild(QProgressBar, "scanProgressBar")
        self.status_label = self.window.findChild(QLabel, "statusLabel")
        self.continue_btn = self.window.findChild(QPushButton, "continueButton")
        self.back_btn = self.window.findChild(QPushButton, "backButton")

        self.title_label.setProperty("heading", "true")
        self.subtitle_label.setProperty("subheading", "true")
        self.status_label.setProperty("muted", "true")
        mark_primary(self.continue_btn)
        mark_secondary(self.choose_btn)
        mark_secondary(self.scan_btn)
        mark_secondary(self.back_btn)

        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()

        self.scan_result = None
        self.folder_name = None

        self.choose_btn.clicked.connect(self.choose_folder)
        self.scan_btn.clicked.connect(self.scan_folder)
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)

        self.thread = None
        self.worker = None

        self.retranslate()

    def retranslate(self):
        self.title_label.setText(tr.t("source.title"))
        self.subtitle_label.setText(tr.t("source.subtitle"))
        self.choose_btn.setText(tr.t("source.choose_folder"))
        self.scan_btn.setText(tr.t("source.scan_folder"))
        self.continue_btn.setText(tr.t("common.next"))
        self.back_btn.setText(tr.t("common.back"))
        self._render_folder_label()
        self._render_status_label()

    def _render_folder_label(self):
        if self.folder_name is None:
            self.choose_folder_label.setText(tr.t("source.no_folder"))
        else:
            self.choose_folder_label.setText(
                tr.t("source.selected_folder", color=THEME_COLOR, name=self.folder_name)
            )

    def _render_status_label(self):
        if self.scan_result is None:
            self.status_label.setText("")
        elif self.scan_result["total"] == 0:
            self.status_label.setText(tr.t("source.scan_none_found"))
        else:
            self.status_label.setText(tr.t(
                "source.scan_found", color=THEME_COLOR,
                total=self.scan_result["total"], folders=self.scan_result["folders"],
            ))

    def get_data(self):
        return {"src_path": self.src_path_edit.text(), "scan_result": self.scan_result}

    def reset(self):
        self.scan_result = None
        self.folder_name = None
        self.src_path_edit.setText("")
        self.scan_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)
        self._render_folder_label()
        self._render_status_label()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self.window, tr.t("source.title"))
        if folder:
            self.scan_result = None
            self.src_path_edit.setText(folder)
            self.folder_name = os.path.basename(os.path.normpath(folder))
            self._render_folder_label()
            self._render_status_label()
            self.scan_btn.setEnabled(True)
            self.continue_btn.setEnabled(False)

    def on_scan_finished(self, result):
        self.progress_bar.hide()
        self.scan_result = result
        self._render_status_label()
        self.continue_btn.setEnabled(result["total"] != 0)
        self.scan_btn.setEnabled(True)
        self.thread.quit()
        self.thread.wait()

    def scan_folder(self):
        path = self.src_path_edit.text()
        if not path:
            return

        self.scan_btn.setEnabled(False)
        self.progress_bar.show()

        self.thread = QThread()
        self.worker = ScanWorker(path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_scan_finished)

        self.thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    step = SourceStep()
    step.window.show()
    app.exec()

import sys
import time
import os
from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit, QFileDialog, QLabel, QProgressBar
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal, QObject
from sorter_logic import scan_source
from sorter_logic.constants import THEME_COLOR
from sorter_logic.theme import mark_primary, mark_secondary
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

        self.progress_bar.hide()

        self.scan_result = None

        self.choose_btn.clicked.connect(self.choose_folder)
        self.scan_btn.clicked.connect(self.scan_folder)
        self.continue_btn.clicked.connect(self.continue_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)

        self.thread = None
        self.worker = None

    def get_data(self):
        return {"src_path": self.src_path_edit.text(), "scan_result": self.scan_result}

    def reset(self):
        self.scan_result = None
        self.src_path_edit.setText("")
        self.choose_folder_label.setText("No folder selected yet.")
        self.status_label.setText("")
        self.scan_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self.window, "Select the folder to scan")
        if folder:
            self.status_label.setText("")
            self.src_path_edit.setText(folder)
            folder_name = os.path.basename(os.path.normpath(folder))
            self.choose_folder_label.setText(
                f"Your selected folder is <span style=\"color: {THEME_COLOR}; font-weight: bold;\">"
                f"\"{folder_name}\"</span>. Click \"Scan Folder\" to continue."
            )
            self.scan_btn.setEnabled(True)
            self.continue_btn.setEnabled(False)
            self.scan_result = None

    def on_scan_finished(self, result):
        self.progress_bar.hide()
        self.scan_result = result
        if result['total'] == 0:
            self.status_label.setText(
                "Scan completed. No media file(s) found in the selected folder. "
                "Please select a different folder."
            )
            self.continue_btn.setEnabled(False)
        else:
            self.status_label.setText(
                f"Scan completed. Found <span style=\"color: {THEME_COLOR}; font-weight: bold;\">"
                f"{result['total']}</span> media file(s) across "
                f"<span style=\"color: {THEME_COLOR}; font-weight: bold;\">{result['folders']}</span> folder(s)."
            )
            self.continue_btn.setEnabled(True)
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

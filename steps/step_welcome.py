import sys
from PySide6.QtWidgets import QApplication, QPushButton, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QObject, Signal
from sorter_logic.theme import mark_primary
from sorter_logic.i18n import translator as tr
from paths import resource_path


class WelcomeStep(QObject):
    continue_requested = Signal()

    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile(resource_path("ui/step0_welcome.ui"))
        ui_file.open(QFile.ReadOnly)

        self.window = loader.load(ui_file)
        self.title_label = self.window.findChild(QLabel, "titleLabel")
        self.intro_label = self.window.findChild(QLabel, "introLabel")
        self.steps_label = self.window.findChild(QLabel, "stepsLabel")
        self.get_started_btn = self.window.findChild(QPushButton, "getStartedButton")

        self.title_label.setProperty("heading", "true")
        mark_primary(self.get_started_btn)

        self.get_started_btn.clicked.connect(self.continue_requested.emit)

        self.retranslate()

    def retranslate(self):
        self.title_label.setText(tr.t("welcome.title"))
        self.intro_label.setText(tr.t("welcome.intro"))
        self.steps_label.setText(tr.t("welcome.steps"))
        self.get_started_btn.setText(tr.t("welcome.get_started"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    step = WelcomeStep()
    step.window.show()
    app.exec()

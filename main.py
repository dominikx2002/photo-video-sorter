import sys
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QStackedWidget, QPushButton
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt
from steps.step_welcome import WelcomeStep
from steps.step_scan import SourceStep
from steps.step_destination import DestinationStep
from steps.step_sorting import SortingStep
from steps.step_summary import SummaryStep
from sorter_logic.theme import apply_theme
from paths import resource_path


def load_ui(path):
    loader = QUiLoader()
    ui_file = QFile(resource_path(path))
    if not ui_file.open(QFile.ReadOnly):
        raise FileNotFoundError(f"Could not open UI file: {path}")
    return loader.load(ui_file)


class WizardApp:
    def __init__(self):
        self.main_window = QWidget()
        self.main_window.setObjectName("mainWindow")
        self.main_window.setWindowTitle("Photo & Video Sorter")
        # Fixed, compact size - mirrors the real Raspberry Pi Imager's small,
        # non-resizable setup dialog rather than a freely resizable window.
        self.main_window.setFixedSize(700, 480)
        main_layout = QHBoxLayout(self.main_window)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = load_ui("sidebar.ui")
        main_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.welcome_step = WelcomeStep()
        self.source_step = SourceStep()
        self.destination_step = DestinationStep()
        self.sorting_step = SortingStep()
        self.summary_step = SummaryStep()

        for step in (self.welcome_step, self.source_step, self.destination_step,
                     self.sorting_step, self.summary_step):
            self.stack.addWidget(step.window)

        self.sidebar_buttons = [
            self.sidebar.findChild(QPushButton, "welcomeButton"),
            self.sidebar.findChild(QPushButton, "sourceFolderButton"),
            self.sidebar.findChild(QPushButton, "destinationButton"),
            self.sidebar.findChild(QPushButton, "sortingButton"),
            self.sidebar.findChild(QPushButton, "summaryButton"),
        ]
        # The sidebar is preview-only: it reflects progress but does not
        # accept clicks, so users can't jump ahead of (or back behind) the
        # step they're actually on.
        for button in self.sidebar_buttons:
            button.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            button.setFocusPolicy(Qt.NoFocus)

        self.completed_steps = set()
        self.current_step = 0

        self.welcome_step.continue_requested.connect(self.on_welcome_continue)
        self.source_step.continue_requested.connect(self.on_source_continue)
        self.source_step.back_requested.connect(lambda: self.goto(0))
        self.destination_step.continue_requested.connect(self.on_destination_continue)
        self.destination_step.back_requested.connect(lambda: self.goto(1))
        self.sorting_step.continue_requested.connect(self.on_sorting_continue)
        self.sorting_step.back_requested.connect(lambda: self.goto(2))
        self.summary_step.start_new_requested.connect(self.on_start_new)

        self.goto(0)

    def on_welcome_continue(self):
        self.completed_steps.add(0)
        self.goto(1)

    def on_source_continue(self):
        self.completed_steps.add(1)
        self.goto(2)

    def on_destination_continue(self):
        source_data = self.source_step.get_data()
        dest_data = self.destination_step.get_data()
        self.sorting_step.set_context(
            source_data["src_path"], dest_data["dest_path"],
            dest_data["collection_name"], dest_data["use_folder_date"],
        )
        self.completed_steps.add(2)
        self.goto(3)

    def on_sorting_continue(self):
        self.summary_step.set_data(self.sorting_step.get_result())
        self.completed_steps.add(3)
        self.goto(4)

    def on_start_new(self):
        self.source_step.reset()
        self.destination_step.reset()
        self.sorting_step.reset()
        self.completed_steps = set()
        self.goto(0)

    def goto(self, idx):
        self.current_step = idx
        self.stack.setCurrentIndex(idx)
        self.update_sidebar()

    def update_sidebar(self):
        for idx, button in enumerate(self.sidebar_buttons):
            button.setChecked(idx == self.current_step)
            visited = idx in self.completed_steps and idx != self.current_step
            button.setProperty("visited", "true" if visited else "false")
            button.style().unpolish(button)
            button.style().polish(button)

    def show(self):
        self.main_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)

    wizard = WizardApp()
    wizard.show()

    app.exec()

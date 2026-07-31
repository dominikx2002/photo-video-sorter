import sys
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QPushButton, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QSize
from PySide6.QtGui import QIcon
from steps.step_welcome import WelcomeStep
from steps.step_scan import SourceStep
from steps.step_destination import DestinationStep
from steps.step_sorting import SortingStep
from steps.step_summary import SummaryStep
from steps.settings_dialog import SettingsDialog
from steps.folder_compare_dialog import FolderCompareDialog
from steps.duplicate_finder_dialog import DuplicateFinderDialog
from sorter_logic.theme import apply_theme, theme_events, VIBRANCY
from sorter_logic.i18n import translator as tr
from sorter_logic.settings_store import load_language
from sorter_logic.mac_chrome import enable_tahoe_chrome
from timeline_stepper import TimelineStepper
from paths import resource_path

TOP_BAR_HEIGHT = 32


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
        self.main_window.setWindowIcon(QIcon(resource_path("packaging/icons/icon.png")))
        # On macOS the window is translucent so the native blur (added after
        # show, see enable_tahoe_chrome) shows through the frosted panes.
        if VIBRANCY:
            self.main_window.setAttribute(Qt.WA_TranslucentBackground, True)
        # Resizable window: the compact 760x552 layout is the *minimum*, and the
        # user can stretch it as large as they like - the content pane grows while
        # the sidebar keeps its width.
        self.main_window.setMinimumSize(760, 552)
        self.main_window.resize(760, 552)

        root_layout = QVBoxLayout(self.main_window)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Slim frosted top bar: clears the native traffic-light buttons on the
        # left (there is no title bar) and hosts the folder-compare tool on the
        # right.
        self.top_bar = QWidget()
        self.top_bar.setObjectName("topBar")
        self.top_bar.setFixedHeight(TOP_BAR_HEIGHT)
        # The bar height matches the native title-bar band (32px) and the icons
        # are centred, so they line up exactly with the traffic-light buttons -
        # one cohesive toolbar.
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(80, 0, 12, 0)
        top_layout.setSpacing(2)
        top_layout.addStretch(1)
        self.compare_btn = self._make_top_bar_button("compare.svg", self.open_compare)
        self.duplicates_btn = self._make_top_bar_button("duplicates.svg", self.open_duplicate_finder)
        top_layout.addWidget(self.duplicates_btn)
        top_layout.addWidget(self.compare_btn)
        root_layout.addWidget(self.top_bar)

        body = QWidget()
        main_layout = QHBoxLayout(body)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        tr.set_language(load_language(), _emit=False)

        self.sidebar = load_ui("ui/sidebar.ui")
        # Keep the sidebar a constant width; extra window width goes to content.
        self.sidebar.setFixedWidth(212)
        main_layout.addWidget(self.sidebar)

        # A short vertical line inset from the top/bottom edges (not a full-height
        # border) between the frosted sidebar and the opaque content.
        divider_container = QWidget()
        divider_container.setFixedWidth(1)
        divider_layout = QVBoxLayout(divider_container)
        divider_layout.setContentsMargins(0, 0, 0, 0)
        divider_layout.setSpacing(0)
        divider_line = QWidget()
        divider_line.setObjectName("sidebarDivider")
        divider_layout.addWidget(divider_line)
        main_layout.addWidget(divider_container)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)      # content pane absorbs resize

        root_layout.addWidget(body)

        self.welcome_step = WelcomeStep()
        self.source_step = SourceStep()
        self.destination_step = DestinationStep()
        self.sorting_step = SortingStep()
        self.summary_step = SummaryStep()

        # The .ui files were authored with different (and sometimes default,
        # cramped) layout margins. Enforce one generous content frame on every
        # step so the whole wizard breathes identically: heading, body, and the
        # nav row always sit on the same grid.
        for step in (self.welcome_step, self.source_step, self.destination_step,
                     self.sorting_step, self.summary_step):
            layout = step.window.layout()
            if layout is not None:
                layout.setContentsMargins(32, 28, 32, 24)
                layout.setSpacing(13)
            self.stack.addWidget(step.window)

        # The signature: a connected vertical timeline in place of a plain list
        # of step buttons. Preview-only - it reflects progress but doesn't
        # accept clicks, so users can't jump ahead of the step they're on.
        self.stepper = TimelineStepper()
        stepper_host = self.sidebar.findChild(QWidget, "stepperHost")
        stepper_host.layout().addWidget(self.stepper)

        self.sidebar_title = self.sidebar.findChild(QLabel, "sidebarTitle")
        self.sidebar_subtitle = self.sidebar.findChild(QLabel, "sidebarSubtitle")
        # The app name is the sidebar's identity - let it wrap to a second line
        # rather than clip when the font is large.
        self.sidebar_subtitle.setWordWrap(True)
        self.settings_btn = self.sidebar.findChild(QPushButton, "settingsButton")
        self.settings_btn.clicked.connect(self.open_settings)

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

        tr.language_changed.connect(self.retranslate)
        # Re-render accent-coloured text (welcome highlights, sidebar) when the
        # system theme or accent colour changes.
        theme_events.changed.connect(self.retranslate)
        self.retranslate()

        self.goto(0)

    def open_settings(self):
        SettingsDialog(self.main_window).exec()

    def _make_top_bar_button(self, icon_name, on_click):
        btn = QPushButton()
        btn.setObjectName("topBarButton")
        btn.setIcon(QIcon(resource_path(f"packaging/icons/{icon_name}")))
        btn.setIconSize(QSize(18, 18))
        btn.setFixedSize(28, 26)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(on_click)
        return btn

    def open_compare(self):
        # Non-modal so it lives alongside the wizard as its own window.
        FolderCompareDialog(self.main_window).show()

    def open_duplicate_finder(self):
        DuplicateFinderDialog(self.main_window).show()

    def retranslate(self, *_):
        self.sidebar_title.setText(tr.t("sidebar.title"))
        self.sidebar_subtitle.setText(tr.t("sidebar.subtitle"))
        self.stepper.set_titles([
            tr.t("sidebar.welcome"),
            tr.t("sidebar.source"),
            tr.t("sidebar.destination"),
            tr.t("sidebar.sorting"),
            tr.t("sidebar.summary"),
        ])
        self.settings_btn.setText(tr.t("sidebar.settings"))
        self.compare_btn.setToolTip(tr.t("compare.tooltip"))
        self.duplicates_btn.setToolTip(tr.t("dupfinder.tooltip"))
        for step in (self.welcome_step, self.source_step, self.destination_step,
                     self.sorting_step, self.summary_step):
            step.retranslate()

    def on_welcome_continue(self):
        self.completed_steps.add(0)
        self.goto(1)

    def on_source_continue(self):
        scan_result = self.source_step.get_data()["scan_result"]
        self.destination_step.set_required_size(scan_result["total_size"] if scan_result else 0)
        self.completed_steps.add(1)
        self.goto(2)

    def on_destination_continue(self):
        source_data = self.source_step.get_data()
        dest_data = self.destination_step.get_data()
        self.sorting_step.set_context(
            source_data["src_paths"], dest_data["dest_path"],
            dest_data["collection_name"], dest_data["use_folder_date"],
            dest_data["use_mtime"], dest_data["use_filename_date"],
            source_data["allowed_extensions"], dest_data["rename_to_date"],
            dest_data["move_files"], dest_data["folder_template"],
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
        self.stepper.set_state(self.current_step, self.completed_steps)

    def show(self):
        self.main_window.show()
        # Add the native title-bar removal + Finder-style vibrancy once the
        # window exists (no-op on non-macOS). Leave the traffic lights at their
        # default position - moving them natively proved too fragile - and line
        # the toolbar icons up with them instead.
        enable_tahoe_chrome(self.main_window)

    def cleanup(self):
        # Stop any running worker threads before the app tears down - a live
        # QThread destroyed at exit aborts the process.
        for step in (self.source_step, self.sorting_step):
            thread = getattr(step, "thread", None)
            if thread is not None and thread.isRunning():
                thread.requestInterruption()
                thread.quit()
                thread.wait(3000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("packaging/icons/icon.png")))
    apply_theme(app)

    wizard = WizardApp()
    wizard.show()
    app.aboutToQuit.connect(wizard.cleanup)

    app.exec()

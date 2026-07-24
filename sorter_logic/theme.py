"""
Look & feel shared by every step of the wizard.

Layout (sidebar + rounded cards/buttons) is modeled after the Raspberry Pi
Imager. The accent color is Claude's terracotta/orange instead of the
Imager's red.

apply_theme() also forces a light QPalette on the whole app. Without that,
plain QLabel/QLineEdit text falls back to the OS palette - on a system in
dark mode that's near-white text, which becomes invisible against the
explicit white backgrounds used throughout these pages.
"""

from PySide6.QtGui import QPalette, QColor

COLOR_PRIMARY = "#D97757"
COLOR_PRIMARY_PRESSED = "#B85C3E"
COLOR_PRIMARY_HOVER_BG = "#F3DDD3"
COLOR_PRIMARY_LIGHT = "#EAC0AC"
COLOR_SECONDARY_HOVER_BG = "#f2f2f2"
COLOR_BORDER = "#dcdcdc"
COLOR_GREEN = "#6cc04a"
COLOR_ORANGE = "#D9822B"
COLOR_BG = "#ffffff"
COLOR_CARD_BG = "#f5f5f5"
COLOR_LOG_BG = "#fcfcfd"
COLOR_TEXT = "#1a1a1a"
COLOR_MUTED = "#646464"
COLOR_SIDEBAR_FUTURE_TEXT = "#9a9a9a"
COLOR_PROGRESS_TRACK = "#E9E9EC"
COLOR_PROGRESS_GRADIENT_TOP = "#EF9772"
COLOR_PROGRESS_GRADIENT_BOTTOM = "#C96A4A"

THEME_COLOR = COLOR_PRIMARY

STYLESHEET = f"""
QWidget#mainWindow {{
    background: {COLOR_BG};
}}

QStackedWidget {{
    background: {COLOR_BG};
}}

QStackedWidget > QWidget {{
    background: {COLOR_BG};
}}

QWidget#sidebarWidget {{
    background: {COLOR_BG};
    min-width: 190px;
    max-width: 190px;
}}

QWidget#sidebarDivider {{
    background: {COLOR_BORDER};
}}

QWidget#sidebarWidget QLabel#sidebarTitle {{
    color: {COLOR_PRIMARY};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 22px 18px 0 18px;
}}

QWidget#sidebarWidget QLabel#sidebarSubtitle {{
    color: {COLOR_MUTED};
    font-size: 10px;
    padding: 0 18px 16px 18px;
}}

QWidget#sidebarWidget QPushButton {{
    text-align: left;
    border: none;
    background: transparent;
    color: {COLOR_SIDEBAR_FUTURE_TEXT};
    padding: 9px 14px;
    margin: 1px 10px;
    border-radius: 6px;
    font-size: 11px;
}}

QWidget#sidebarWidget QPushButton[visited="true"] {{
    color: {COLOR_PRIMARY};
}}

QWidget#sidebarWidget QPushButton:checked {{
    background: {COLOR_PRIMARY};
    color: white;
    font-weight: 600;
}}

QPushButton#settingsButton {{
    text-align: center;
    background: white;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    color: {COLOR_MUTED};
    font-size: 10px;
    padding: 6px 10px;
    margin: 8px 14px 16px 14px;
}}
QPushButton#settingsButton:hover {{
    background: {COLOR_SECONDARY_HOVER_BG};
    color: {COLOR_PRIMARY};
    border-color: {COLOR_PRIMARY};
}}

QLabel {{
    color: {COLOR_TEXT};
}}

QLabel[heading="true"] {{
    color: {COLOR_TEXT};
    font-size: 20px;
    font-weight: 700;
}}

QLabel[subheading="true"] {{
    color: {COLOR_MUTED};
    font-size: 12px;
}}

QLabel[muted="true"] {{
    color: {COLOR_MUTED};
    font-size: 11px;
}}

QLabel[cardNumber="true"] {{
    color: {COLOR_PRIMARY};
    font-size: 21px;
    font-weight: 700;
}}

QFrame[card="true"] {{
    background: {COLOR_CARD_BG};
    border-radius: 10px;
}}

QLineEdit {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    background: white;
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_PRIMARY_HOVER_BG};
}}

QLineEdit:read-only {{
    background: {COLOR_CARD_BG};
    color: {COLOR_MUTED};
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_PRIMARY};
}}

QComboBox {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    background: white;
    color: {COLOR_TEXT};
    min-height: 20px;
}}
QComboBox:focus {{
    border: 1px solid {COLOR_PRIMARY};
}}
QComboBox QAbstractItemView {{
    border: 1px solid {COLOR_BORDER};
    background: white;
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_PRIMARY_HOVER_BG};
    selection-color: {COLOR_PRIMARY};
    outline: none;
}}

QCheckBox {{
    color: {COLOR_TEXT};
    font-size: 12px;
}}

QPushButton[variant="primary"] {{
    background: {COLOR_PRIMARY};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 22px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton[variant="primary"]:hover {{
    background: {COLOR_PRIMARY_HOVER_BG};
    color: {COLOR_PRIMARY};
}}
QPushButton[variant="primary"]:pressed {{
    background: {COLOR_PRIMARY_PRESSED};
}}
QPushButton[variant="primary"]:disabled {{
    background: {COLOR_PRIMARY_LIGHT};
    color: white;
}}

QPushButton[variant="secondary"] {{
    background: white;
    color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 22px;
    font-size: 12px;
}}
QPushButton[variant="secondary"]:hover {{
    background: {COLOR_SECONDARY_HOVER_BG};
}}
QPushButton[variant="secondary"]:disabled {{
    color: #C9C9C9;
}}

QProgressBar {{
    border: none;
    border-radius: 4px;
    background: {COLOR_PROGRESS_TRACK};
    text-align: center;
    color: transparent;
    min-height: 8px;
    max-height: 8px;
}}
QProgressBar::chunk {{
    border-radius: 4px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLOR_PROGRESS_GRADIENT_TOP}, stop:0.55 {COLOR_PRIMARY}, stop:1 {COLOR_PROGRESS_GRADIENT_BOTTOM});
}}

QPlainTextEdit#logView {{
    background: {COLOR_LOG_BG};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    font-family: Menlo, Consolas, monospace;
    font-size: 11px;
    padding: 6px;
}}
"""


def apply_theme(app):
    # Force a light palette regardless of OS dark-mode: Qt widgets otherwise
    # inherit the system palette's (near-white) text color, which disappears
    # against the explicit white backgrounds this app uses everywhere.
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLOR_BG))
    palette.setColor(QPalette.WindowText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Base, QColor("white"))
    palette.setColor(QPalette.AlternateBase, QColor(COLOR_CARD_BG))
    palette.setColor(QPalette.Text, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Button, QColor(COLOR_BG))
    palette.setColor(QPalette.ButtonText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.ToolTipBase, QColor("white"))
    palette.setColor(QPalette.ToolTipText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.PlaceholderText, QColor(COLOR_MUTED))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(COLOR_SIDEBAR_FUTURE_TEXT))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(COLOR_SIDEBAR_FUTURE_TEXT))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)


def mark_primary(button):
    button.setProperty("variant", "primary")


def mark_secondary(button):
    button.setProperty("variant", "secondary")

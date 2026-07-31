"""
Look & feel for the whole wizard - now driven by the operating system.

Two things follow the OS live:
  * Light / dark - from QStyleHints.colorScheme(), re-applied on change.
  * Accent colour - from the user's macOS/Windows system accent
    (QPalette.Accent), so the buttons, the timeline and the progress bar are
    painted in whatever colour the person chose in System Settings.

Everything derives from those two inputs. `CUR` holds the resolved token set
for the active scheme; `theme_events.changed` fires whenever it is rebuilt so
custom-painted widgets (the timeline) and accent-coloured labels can refresh.
"""

import sys
from PySide6.QtGui import QPalette, QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QObject, Signal
from paths import resource_path

# On macOS the sidebar + top bar are left transparent so a native
# NSVisualEffectView (see mac_chrome.py) shows real Finder-style blur through
# them. Elsewhere they stay solid.
VIBRANCY = sys.platform == "darwin"

# Status colours read the same in light and dark, so they stay fixed.
COLOR_GREEN = "#2FB37A"
COLOR_ORANGE = "#E8912B"
FALLBACK_ACCENT = "#0A84FF"

_CHECK_SVG = resource_path("packaging/icons/check.svg").replace("\\", "/")
_CHEVRON_SVG = resource_path("packaging/icons/chevron-down.svg").replace("\\", "/")

# Resolved tokens for the active scheme (hex strings). Populated by apply_theme.
CUR = {}


class _ThemeEvents(QObject):
    changed = Signal()


theme_events = _ThemeEvents()


def accent():
    return CUR.get("accent", FALLBACK_ACCENT)


# --- colour maths -----------------------------------------------------------
def _mix(c1, c2, t):
    """Blend two QColors; t=0 -> c1, t=1 -> c2."""
    return QColor(
        round(c1.red() * (1 - t) + c2.red() * t),
        round(c1.green() * (1 - t) + c2.green() * t),
        round(c1.blue() * (1 - t) + c2.blue() * t),
    )


def _soften(c):
    """macOS renders its accent softer than the raw accent value - a touch
    less saturated. Mirror that so buttons read as a calm, faded system colour
    rather than a vivid, garish one."""
    h, s, l, a = c.getHsl()
    return QColor.fromHsl(h, int(s * 0.74), l, a)


def _read_system_accent(app):
    pal = app.palette()
    for role_name in ("Accent", "Highlight"):
        role = getattr(QPalette.ColorRole, role_name, None)
        if role is None:
            continue
        c = pal.color(role)
        if c.isValid():
            return c
    return QColor(FALLBACK_ACCENT)


def _tokens(dark, accent_color):
    a = _soften(QColor(accent_color))
    white, black = QColor("#FFFFFF"), QColor("#000000")

    if dark:
        surface = QColor("#242426")
        canvas = QColor("#1B1B1D")
        sidebar = QColor("#202022")
        ink = QColor("#F2F2F7")
        muted = QColor("#9A9AA3")
        faint = QColor("#67676E")
        hairline = QColor("#3A3A3F")
        card = QColor("#2E2E33")
        track = QColor("#3A3A3F")
        input_bg = QColor("#2C2C2E")
        readonly_bg = QColor("#27272A")
        soft = _mix(surface, a, 0.26)
    else:
        surface = white
        canvas = QColor("#F4F5FA")
        sidebar = QColor("#F3F4F8")
        ink = QColor("#1C2238")
        muted = QColor("#6E7488")
        faint = QColor("#AEB3C4")
        hairline = QColor("#E6E8F0")
        card = QColor("#F1F3F9")
        track = QColor("#E6E8F0")
        input_bg = white
        readonly_bg = card
        soft = _mix(white, a, 0.12)

    def hx(c):
        return c.name()

    # Frosted panes on macOS (real blur behind), solid elsewhere. A whisper of
    # tint over the blur keeps text readable, like Finder's sidebar.
    if VIBRANCY:
        window_bg = "transparent"
        sidebar_bg = "rgba(255, 255, 255, 0.05)" if dark else "rgba(255, 255, 255, 0.45)"
        topbar_bg = "transparent"
    else:
        window_bg = hx(canvas)
        sidebar_bg = hx(sidebar)
        topbar_bg = hx(sidebar)

    return {
        "dark": dark,
        "window_bg": window_bg,
        "sidebar_bg": sidebar_bg,
        "topbar_bg": topbar_bg,
        # Flat, minimal accent. Like macOS: a filled button brightens a touch
        # on hover and darkens when pressed; bordered buttons take a neutral
        # grey fill on hover, never a coloured one.
        "accent": hx(a),
        "accent_hover": hx(_mix(a, white, 0.10)),
        "accent_press": hx(_mix(a, black, 0.14)),
        "accent_disabled": hx(_mix(a, canvas, 0.60)),
        "hover_bg": hx(_mix(surface, ink, 0.13)),
        "press_bg": hx(_mix(surface, ink, 0.20)),
        "soft": hx(soft),
        "surface": hx(surface),
        "canvas": hx(canvas),
        "sidebar": hx(sidebar),
        "ink": hx(ink),
        "muted": hx(muted),
        "faint": hx(faint),
        "hairline": hx(hairline),
        "card": hx(card),
        "track": hx(track),
        "input_bg": hx(input_bg),
        "readonly_bg": hx(readonly_bg),
        "on_accent": "#FFFFFF",
    }


def _build_stylesheet(c):
    return f"""
QWidget#mainWindow {{ background: {c['window_bg']}; }}

QWidget#topBar {{ background: {c['topbar_bg']}; }}
QPushButton#topBarButton {{
    background: transparent;
    border: none;
    border-radius: 6px;
}}
QPushButton#topBarButton:hover {{ background: {c['hover_bg']}; }}
QPushButton#topBarButton:pressed {{ background: {c['press_bg']}; }}

QStackedWidget, QStackedWidget > QWidget {{ background: {c['surface']}; }}

QWidget#sidebarWidget {{
    background: {c['sidebar_bg']};
    min-width: 212px;
    max-width: 212px;
}}
QWidget#sidebarDivider {{ background: {c['hairline']}; }}

QWidget#sidebarWidget QLabel#sidebarTitle {{
    color: {c['accent']};
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.8px;
    padding: 22px 18px 0 20px;
}}
QWidget#sidebarWidget QLabel#sidebarSubtitle {{
    color: {c['ink']};
    font-size: 19px;
    font-weight: 700;
    padding: 3px 16px 14px 20px;
}}

QPushButton#settingsButton {{
    text-align: center;
    background: {c['surface']};
    border: 1px solid {c['hairline']};
    border-radius: 9px;
    color: {c['muted']};
    font-size: 11px;
    font-weight: 600;
    padding: 0 12px;
    min-height: 32px;
    margin: 6px 16px 16px 18px;
}}
QPushButton#settingsButton:hover {{
    background: {c['hover_bg']};
    color: {c['ink']};
}}
QPushButton#settingsButton:pressed {{ background: {c['press_bg']}; }}

QLabel {{ color: {c['ink']}; font-size: 12px; }}
QLabel[heading="true"] {{
    color: {c['ink']};
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
}}
QLabel[subheading="true"] {{ color: {c['muted']}; font-size: 13px; }}
QLabel[lead="true"] {{ color: {c['ink']}; font-size: 15px; }}
QLabel[muted="true"] {{ color: {c['muted']}; font-size: 12px; }}
QLabel#activityLog {{ color: {c['muted']}; font-size: 11px; }}
QLabel#spinnerGlyph {{ color: {c['accent']}; font-size: 11px; font-weight: 700; }}
QLabel#triviaText {{ color: {c['muted']}; font-size: 11px; font-style: italic; }}
QToolButton#advancedToggle {{
    color: {c['ink']};
    font-size: 13px;
    font-weight: 600;
    border: none;
    background: transparent;
    padding: 4px 0;
}}
QToolButton#advancedToggle:hover {{ color: {c['accent']}; }}
QLabel#optionDesc {{ color: {c['muted']}; font-size: 11px; padding: 0 0 6px 24px; }}
QLabel#optionHeading {{ color: {c['ink']}; font-size: 12px; font-weight: 600; padding: 8px 0 4px 0; }}
QLabel[cardNumber="true"] {{ color: {c['ink']}; font-size: 23px; font-weight: 700; }}

QFrame[card="true"] {{
    background: {c['card']};
    border: none;
    border-radius: 12px;
}}

QLineEdit {{
    border: 1px solid {c['hairline']};
    border-radius: 10px;
    padding: 9px 12px;
    background: {c['input_bg']};
    color: {c['ink']};
    selection-background-color: {c['soft']};
    selection-color: {c['accent']};
}}
QLineEdit:read-only {{ background: {c['readonly_bg']}; color: {c['muted']}; }}
QLineEdit:focus {{ border: 1.5px solid {c['accent']}; }}

QComboBox {{
    border: 1px solid {c['hairline']};
    border-radius: 10px;
    padding: 8px 14px;
    padding-right: 30px;
    background: {c['input_bg']};
    color: {c['ink']};
    min-height: 22px;
}}
QComboBox:hover {{ border-color: {c['accent']}; }}
QComboBox:focus, QComboBox:on {{ border: 1.5px solid {c['accent']}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border: none;
    background: transparent;
}}
QComboBox::down-arrow {{
    image: url("{_CHEVRON_SVG}");
    width: 12px;
    height: 12px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {c['hairline']};
    border-radius: 10px;
    background: {c['surface']};
    color: {c['ink']};
    outline: none;
    padding: 6px;
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding: 4px 10px;
    border-radius: 7px;
    color: {c['ink']};
}}
QComboBox QAbstractItemView::item:selected,
QComboBox QAbstractItemView::item:hover {{
    background: {c['soft']};
    color: {c['accent']};
}}

QCheckBox {{ color: {c['ink']}; font-size: 12px; spacing: 9px; padding: 3px 0; }}
QCheckBox::indicator {{
    width: 19px;
    height: 19px;
    border-radius: 6px;
    border: 1.5px solid {c['faint']};
    background: {c['input_bg']};
}}
QCheckBox::indicator:hover {{ border-color: {c['accent']}; }}
QCheckBox::indicator:checked {{
    border: none;
    background: {c['accent']};
    image: url("{_CHECK_SVG}");
}}
QCheckBox::indicator:indeterminate {{
    border: none;
    background: {c['accent']};
}}
QCheckBox#sectionHeader {{
    color: {c['muted']};
    font-size: 12px;
    font-weight: 700;
    padding-top: 8px;
}}

QPushButton[variant="primary"] {{
    background: {c['accent']};
    color: {c['on_accent']};
    border: 1px solid transparent;
    border-radius: 9px;
    padding: 0 22px;
    min-height: 36px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton[variant="primary"]:hover {{ background: {c['accent_hover']}; }}
QPushButton[variant="primary"]:pressed {{ background: {c['accent_press']}; }}
QPushButton[variant="primary"]:disabled {{
    background: {c['accent_disabled']};
    color: {c['surface']};
}}

QPushButton[variant="secondary"] {{
    background: {c['surface']};
    color: {c['ink']};
    border: 1px solid {c['hairline']};
    border-radius: 9px;
    padding: 0 18px;
    min-height: 36px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton[variant="secondary"]:hover {{ background: {c['hover_bg']}; border-color: {c['faint']}; }}
QPushButton[variant="secondary"]:pressed {{ background: {c['press_bg']}; }}
QPushButton[variant="secondary"]:disabled {{
    color: {c['faint']};
    border-color: {c['hairline']};
    background: {c['surface']};
}}

QProgressBar {{
    border: none;
    border-radius: 6px;
    background: {c['track']};
    text-align: center;
    color: transparent;
    min-height: 10px;
    max-height: 10px;
}}
QProgressBar::chunk {{ border-radius: 6px; background: {c['accent']}; }}

/* The sorting log reads like a terminal in both schemes, revealed under
   "Show details" the way the Ubuntu installer hides its console. */
QPlainTextEdit#logView {{
    background: #1E1E24;
    color: #D4D4DC;
    border: 1px solid #2C2C36;
    border-radius: 12px;
    font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 11px;
    padding: 10px 12px;
}}

QPushButton#detailsToggle {{
    text-align: left;
    background: transparent;
    border: none;
    color: {c['muted']};
    font-size: 12px;
    font-weight: 600;
    padding: 4px 2px;
}}
QPushButton#detailsToggle:hover {{ color: {c['accent']}; }}

QPushButton#rowRemove {{
    background: transparent;
    border: none;
    border-radius: 8px;
    color: {c['faint']};
    font-size: 14px;
}}
QPushButton#rowRemove:hover {{ background: {c['hover_bg']}; color: {c['ink']}; }}
QPushButton#rowRemove:disabled {{ color: {c['hairline']}; background: transparent; }}

QDialog {{ background: {c['canvas']}; }}
QScrollArea {{ background: transparent; border: none; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background: {c['faint']};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    height: 0;
}}
"""


def _apply_scheme(app):
    dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    accent_color = _read_system_accent(app)
    CUR.clear()
    CUR.update(_tokens(dark, accent_color))

    pal = QPalette()
    C = QColor
    pal.setColor(QPalette.Window, C(CUR["canvas"]))
    pal.setColor(QPalette.WindowText, C(CUR["ink"]))
    pal.setColor(QPalette.Base, C(CUR["input_bg"]))
    pal.setColor(QPalette.AlternateBase, C(CUR["card"]))
    pal.setColor(QPalette.Text, C(CUR["ink"]))
    pal.setColor(QPalette.Button, C(CUR["surface"]))
    pal.setColor(QPalette.ButtonText, C(CUR["ink"]))
    pal.setColor(QPalette.ToolTipBase, C(CUR["surface"]))
    pal.setColor(QPalette.ToolTipText, C(CUR["ink"]))
    pal.setColor(QPalette.PlaceholderText, C(CUR["muted"]))
    pal.setColor(QPalette.Highlight, C(CUR["accent"]))
    pal.setColor(QPalette.HighlightedText, C(CUR["on_accent"]))
    pal.setColor(QPalette.Disabled, QPalette.Text, C(CUR["faint"]))
    pal.setColor(QPalette.Disabled, QPalette.WindowText, C(CUR["faint"]))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, C(CUR["faint"]))
    app.setPalette(pal)
    app.setStyleSheet(_build_stylesheet(CUR))
    theme_events.changed.emit()


def apply_theme(app):
    app.setStyle("Fusion")
    if sys.platform == "darwin":
        app.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont))
    elif sys.platform == "win32":
        app.setFont(QFont("Segoe UI"))

    _apply_scheme(app)
    # Follow the OS: repaint on light/dark toggle and on accent changes.
    app.styleHints().colorSchemeChanged.connect(lambda *_: _apply_scheme(app))


def mark_primary(button):
    # Flat filled accent, the way macOS draws its default button - no glow.
    button.setProperty("variant", "primary")


def mark_secondary(button):
    button.setProperty("variant", "secondary")


def apply_card_shadow(widget):
    """Very faint elevation under a tinted tile - a whisper of depth."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(14)
    shadow.setColor(QColor(0, 0, 0, 45))
    shadow.setOffset(0, 2)
    widget.setGraphicsEffect(shadow)

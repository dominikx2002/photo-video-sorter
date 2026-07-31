"""
An iOS/macOS-style toggle switch: a rounded pill with a sliding white knob that
animates on change, tinted with the system accent when on. It subclasses
QCheckBox, so it behaves exactly like one (isChecked/setChecked/toggled) and can
carry a text label drawn to its right - a drop-in replacement for a checkbox.
"""

from PySide6.QtWidgets import QCheckBox
from PySide6.QtGui import QPainter, QColor, QFontMetrics
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QRectF, QSize

from sorter_logic import theme

_TRACK_W = 40
_TRACK_H = 22
_KNOB_MARGIN = 2
_GAP = 10          # space between the switch and its text


class ToggleSwitch(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._pos = 1.0 if self.isChecked() else 0.0
        self._anim = QPropertyAnimation(self, b"knobPos", self)
        self._anim.setDuration(140)
        self.toggled.connect(self._animate)
        self.setCursor(Qt.PointingHandCursor)

    def _animate(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def _get_knob(self):
        return self._pos

    def _set_knob(self, v):
        self._pos = v
        self.update()

    knobPos = Property(float, _get_knob, _set_knob)

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        tw = fm.horizontalAdvance(self.text()) if self.text() else 0
        extra = (_GAP + tw + 2) if self.text() else 0
        return QSize(_TRACK_W + extra, max(_TRACK_H, fm.height()))

    def minimumSizeHint(self):
        return self.sizeHint()

    def hitButton(self, pos):
        return self.rect().contains(pos)      # click anywhere on the row toggles

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = self.height()
        track_y = (h - _TRACK_H) / 2.0

        accent = QColor(theme.CUR.get("accent", "#0A84FF"))
        off = QColor(theme.CUR.get("track", "#3A3A3F"))
        col = QColor(
            round(off.red() + (accent.red() - off.red()) * self._pos),
            round(off.green() + (accent.green() - off.green()) * self._pos),
            round(off.blue() + (accent.blue() - off.blue()) * self._pos),
        )
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawRoundedRect(QRectF(0, track_y, _TRACK_W, _TRACK_H), _TRACK_H / 2, _TRACK_H / 2)

        knob_d = _TRACK_H - 2 * _KNOB_MARGIN
        knob_x = _KNOB_MARGIN + self._pos * (_TRACK_W - knob_d - 2 * _KNOB_MARGIN)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QRectF(knob_x, track_y + _KNOB_MARGIN, knob_d, knob_d))

        if self.text():
            p.setPen(QColor(theme.CUR.get("ink", "#EDEDED")))
            p.setFont(self.font())
            tx = _TRACK_W + _GAP
            p.drawText(QRectF(tx, 0, self.width() - tx, h),
                       Qt.AlignVCenter | Qt.AlignLeft, self.text())

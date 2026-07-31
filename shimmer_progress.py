"""
A progress bar with a highlight that sweeps left-to-right every 3 seconds -
like the classic Windows bar - so it always looks alive, never frozen.

Works in two modes:
  * determinate  - a solid accent fill up to value/maximum, with a soft white
                   sheen sweeping across the filled part;
  * busy         - set the range to (0, 0); no fill, just an accent glow band
                   sweeping over the track.

It exposes the slice of the QProgressBar API the app uses (setRange, setValue,
setMaximum, setTextVisible) so it drops straight in. Colours come from the live
theme, so it follows light/dark + the system accent.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QRectF

from sorter_logic import theme


def replace_progressbar(window, object_name):
    """Swap a plain QProgressBar defined in a .ui file for a ShimmerProgressBar
    in the exact same layout slot, and return the new bar. Lets the .ui keep a
    placeholder while every bar in the app shares one look and behaviour."""
    from PySide6.QtWidgets import QProgressBar
    old = window.findChild(QProgressBar, object_name)
    layout = old.parentWidget().layout()
    index = layout.indexOf(old)
    layout.removeWidget(old)
    old.deleteLater()
    bar = ShimmerProgressBar()
    bar.setTextVisible(False)
    layout.insertWidget(index, bar)
    return bar


class ShimmerProgressBar(QWidget):
    def __init__(self, parent=None, height=10):
        super().__init__(parent)
        self._value = 0
        self._max = 100
        self._busy = False
        self._shimmer = 0.0
        self.setFixedHeight(height)
        self._anim = QPropertyAnimation(self, b"shimmer", self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(3000)      # one sweep every 3 seconds
        self._anim.setLoopCount(-1)

    # --- animated property ---------------------------------------------------
    def _get_shimmer(self):
        return self._shimmer

    def _set_shimmer(self, v):
        self._shimmer = v
        self.update()

    shimmer = Property(float, _get_shimmer, _set_shimmer)

    # --- QProgressBar-ish API ------------------------------------------------
    def setRange(self, lo, hi):
        self._max = hi
        self._busy = (hi == 0)
        self.update()

    def setMaximum(self, m):
        self._max = m
        self._busy = (m == 0)
        self.update()

    def setValue(self, v):
        self._value = v
        self.update()

    def value(self):
        return self._value

    def maximum(self):
        return self._max

    # A Qt property mirror of the value, so a QPropertyAnimation(bar, b"animValue")
    # can animate the fill smoothly (used by the sorting step).
    animValue = Property(int, value, setValue)

    def setTextVisible(self, _visible):
        pass

    # --- keep the sweep running only while shown -----------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._anim.start()

    def hideEvent(self, event):
        self._anim.stop()
        super().hideEvent(event)

    # --- painting ------------------------------------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = float(self.width()), float(self.height())
        radius = h / 2.0
        accent = QColor(theme.CUR.get("accent", "#0A84FF"))

        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        p.setClipPath(clip)

        # track
        p.fillRect(QRectF(0, 0, w, h), QColor(theme.CUR.get("track", "#3A3A3F")))

        frac = 0.0
        if not self._busy and self._max:
            frac = max(0.0, min(1.0, self._value / self._max))
            if frac > 0:
                p.fillRect(QRectF(0, 0, frac * w, h), accent)

        # sweeping highlight
        band = w * 0.32
        x = self._shimmer * (w + band) - band
        grad = QLinearGradient(x, 0, x + band, 0)
        if self._busy:
            grad.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), 0))
            grad.setColorAt(0.5, QColor(accent.red(), accent.green(), accent.blue(), 170))
            grad.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 0))
            p.fillRect(QRectF(x, 0, band, h), grad)
        elif frac > 0:
            grad.setColorAt(0.0, QColor(255, 255, 255, 0))
            grad.setColorAt(0.5, QColor(255, 255, 255, 130))
            grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.save()
            fill_clip = QPainterPath()
            fill_clip.addRect(QRectF(0, 0, frac * w, h))
            p.setClipPath(fill_clip, Qt.IntersectClip)
            p.fillRect(QRectF(x, 0, band, h), grad)
            p.restore()

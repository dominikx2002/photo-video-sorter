r"""
A tiny "still working" line: a spinning /-\| glyph next to a rotating bit of
trivia, gently pulsing so it reads as alive during a long operation.

Feed start() a list of short strings; it cycles the spinner fast, the trivia
slowly, and pulses the whole line's opacity up and down. stop() freezes it.
Colours/size come from QSS via the object names spinnerGlyph / triviaText.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation

_FRAMES = ["/", "-", "\\", "|"]


class SpinnerTrivia(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        self.spinner = QLabel(_FRAMES[0])
        self.spinner.setObjectName("spinnerGlyph")
        self.spinner.setFixedWidth(9)
        self.spinner.setAlignment(Qt.AlignCenter)
        self.text = QLabel("")
        self.text.setObjectName("triviaText")
        lay.addWidget(self.spinner)
        lay.addWidget(self.text, 1)

        self._frame = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.setInterval(280)
        self._spin_timer.timeout.connect(self._tick_spin)

        self._facts = []
        self._fact_i = 0
        self._fact_timer = QTimer(self)
        self._fact_timer.setInterval(4500)
        self._fact_timer.timeout.connect(self._tick_fact)

        # slow opacity pulse over the whole line
        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(1.0)
        self.setGraphicsEffect(self._fx)
        self._pulse = QPropertyAnimation(self._fx, b"opacity", self)
        self._pulse.setDuration(4200)
        self._pulse.setLoopCount(-1)
        self._pulse.setKeyValueAt(0.0, 1.0)
        self._pulse.setKeyValueAt(0.5, 0.45)
        self._pulse.setKeyValueAt(1.0, 1.0)

    def start(self, facts):
        self._facts = list(facts or [])
        self._fact_i = 0
        self.text.setText(self._facts[0] if self._facts else "")
        self._frame = 0
        self.spinner.setText(_FRAMES[0])
        self._spin_timer.start()
        if len(self._facts) > 1:
            self._fact_timer.start()
        self._pulse.start()

    def stop(self):
        self._spin_timer.stop()
        self._fact_timer.stop()
        self._pulse.stop()
        self._fx.setOpacity(1.0)

    def _tick_spin(self):
        self._frame = (self._frame + 1) % len(_FRAMES)
        self.spinner.setText(_FRAMES[self._frame])

    def _tick_fact(self):
        if not self._facts:
            return
        self._fact_i = (self._fact_i + 1) % len(self._facts)
        self.text.setText(self._facts[self._fact_i])

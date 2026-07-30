"""
The app's signature element: a connected vertical timeline in the sidebar.

The product's whole job is putting photos back onto the timeline of when they
happened, so the setup itself is drawn as a timeline the user walks down.
Completed steps are filled nodes joined by an accent-coloured line; the current
step is an open node ringed in the same colour; steps still ahead are quiet
hollow nodes on a hairline track. Colours come from the live theme
(system accent + light/dark), so it repaints whenever the theme changes. It's
preview-only - it reports where you are, it doesn't accept clicks.
"""

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF

from sorter_logic import theme

NODE_R = 12
ROW_H = 54
TOP_PAD = 14
LEFT_PAD = 26
LABEL_GAP = 15


class TimelineStepper(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titles = []
        self.current = 0
        self.completed = set()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setMinimumHeight(TOP_PAD * 2 + ROW_H * 5)
        # Repaint whenever the system theme (light/dark or accent) changes.
        theme.theme_events.changed.connect(self.update)

    def set_titles(self, titles):
        self.titles = list(titles)
        self.update()

    def set_state(self, current, completed):
        self.current = current
        self.completed = set(completed)
        self.update()

    def _node_center(self, i):
        return QPointF(LEFT_PAD, TOP_PAD + NODE_R + i * ROW_H)

    def _accent_brush(self):
        # Flat, single accent colour - no gradient, no glow.
        return QBrush(QColor(theme.CUR["accent"]))

    def paintEvent(self, event):
        n = len(self.titles)
        if n == 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 1) Connector segments (drawn first so nodes sit on top). A segment is
        # "lit" once the step above it is done and we've moved past it.
        for i in range(n - 1):
            c0 = self._node_center(i)
            c1 = self._node_center(i + 1)
            top = QPointF(c0.x(), c0.y() + NODE_R + 4)
            bot = QPointF(c1.x(), c1.y() - NODE_R - 4)
            lit = i in self.completed and (i + 1 in self.completed or i + 1 == self.current)
            pen = QPen()
            pen.setWidthF(2.6)
            pen.setCapStyle(Qt.RoundCap)
            if lit:
                pen.setColor(QColor(theme.CUR["accent"]))
            else:
                pen.setColor(QColor(theme.CUR["hairline"]))
            p.setPen(pen)
            p.drawLine(top, bot)

        # 2) Nodes + labels.
        for i in range(n):
            c = self._node_center(i)
            is_current = i == self.current
            is_done = i in self.completed and not is_current

            node_rect = QRectF(c.x() - NODE_R, c.y() - NODE_R, NODE_R * 2, NODE_R * 2)

            if is_done:
                p.setPen(Qt.NoPen)
                p.setBrush(self._accent_brush())
                p.drawEllipse(node_rect)
                self._draw_check(p, c)
            elif is_current:
                # Open node: surface fill with a solid accent ring.
                ring = QPen(QColor(theme.CUR["accent"]))
                ring.setWidthF(2.6)
                p.setPen(ring)
                p.setBrush(QBrush(QColor(theme.CUR["surface"])))
                p.drawEllipse(node_rect.adjusted(1.3, 1.3, -1.3, -1.3))
                self._draw_number(p, c, i + 1, QColor(theme.CUR["accent"]), bold=True)
            else:
                p.setPen(QPen(QColor(theme.CUR["hairline"]), 1.6))
                p.setBrush(QBrush(QColor(theme.CUR["sidebar"])))
                p.drawEllipse(node_rect)
                self._draw_number(p, c, i + 1, QColor(theme.CUR["faint"]), bold=False)

            self._draw_label(p, c, self.titles[i], is_current, is_done)

    def _draw_check(self, p, c):
        path = QPainterPath()
        path.moveTo(c.x() - 5.5, c.y() + 0.5)
        path.lineTo(c.x() - 1.5, c.y() + 4.5)
        path.lineTo(c.x() + 6.0, c.y() - 4.5)
        pen = QPen(QColor("white"), 2.4)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    def _draw_number(self, p, c, num, color, bold):
        font = QFont()
        font.setPointSize(10)
        font.setBold(bold)
        p.setFont(font)
        p.setPen(QPen(color))
        rect = QRectF(c.x() - NODE_R, c.y() - NODE_R, NODE_R * 2, NODE_R * 2)
        p.drawText(rect, Qt.AlignCenter, str(num))

    def _draw_label(self, p, c, text, is_current, is_done):
        # Inherit the application's system font (SF Pro on macOS).
        font = QFont(self.font())
        font.setPointSize(13 if is_current else 12)
        font.setWeight(QFont.DemiBold if is_current else QFont.Normal)
        p.setFont(font)
        color = QColor(theme.CUR["ink"]) if (is_current or is_done) else QColor(theme.CUR["faint"])
        p.setPen(QPen(color))

        x = c.x() + NODE_R + LABEL_GAP
        avail = max(10, self.width() - x - 14)
        metrics = p.fontMetrics()
        elided = metrics.elidedText(text, Qt.ElideRight, int(avail))
        rect = QRectF(x, c.y() - ROW_H / 2, avail, ROW_H)
        p.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, elided)

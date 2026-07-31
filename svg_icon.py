"""
Render an SVG file, tinted to a given colour, into an inline <img> data-URI so
it can be dropped straight into RichText (e.g. a QLabel). The SVG's own colours
are irrelevant - every stroke/fill is recoloured to the target - so one generic
icon can be shown in the accent colour, white, etc.
"""

import re
import base64
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

_COLOR_ATTR = re.compile(r'(stroke|fill)="#[0-9A-Fa-f]{3,8}"')


def colored_svg_datauri(path, color, size=15):
    """Return an <img …> tag whose data-URI is the SVG at `path` recoloured to
    `color` and rasterised at `size` px, or None if the file can't be read."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            svg = f.read()
    except OSError:
        return None
    svg = _COLOR_ATTR.sub(lambda m: f'{m.group(1)}="{color}"', svg)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    pix.save(buffer, "PNG")
    b64 = base64.b64encode(bytes(data)).decode("ascii")
    return (f'<img src="data:image/png;base64,{b64}" '
            f'width="{size}" height="{size}" style="vertical-align: middle;">')

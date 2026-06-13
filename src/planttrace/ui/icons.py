from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def line_icon(name: str, color: str = "#f5f7f3") -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(color), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    draw_icon(painter, name)
    painter.end()
    return QIcon(pixmap)


def logo_pixmap(size: int = 32) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 32, size / 32)

    painter.setPen(QPen(QColor("#dfe6df"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawRoundedRect(QRectF(7, 5, 15, 20), 2, 2)
    painter.drawLine(QPointF(11, 10), QPointF(18, 10))
    painter.drawLine(QPointF(11, 15), QPointF(16, 15))

    painter.setPen(QPen(QColor("#63b89f"), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawLine(QPointF(8, 23), QPointF(14, 18))
    painter.drawLine(QPointF(14, 18), QPointF(20, 21))
    painter.drawEllipse(QRectF(18, 16, 8, 8))
    painter.drawLine(QPointF(24, 23), QPointF(28, 27))

    painter.end()
    return pixmap


def draw_icon(painter: QPainter, name: str) -> None:
    if name == "search":
        painter.drawEllipse(QRectF(5, 5, 10, 10))
        painter.drawLine(QPointF(14, 14), QPointF(20, 20))
    elif name == "profile":
        painter.drawEllipse(QRectF(9, 5, 6, 6))
        painter.drawArc(QRectF(6, 12, 12, 9), 0, 180 * 16)
        painter.drawLine(QPointF(16, 16), QPointF(21, 21))
    elif name == "extract":
        painter.drawRect(QRectF(5, 5, 14, 14))
        painter.drawLine(QPointF(8, 9), QPointF(16, 9))
        painter.drawLine(QPointF(8, 13), QPointF(16, 13))
    elif name == "template":
        painter.drawRoundedRect(QRectF(5, 4, 14, 16), 2, 2)
        painter.drawLine(QPointF(8, 8), QPointF(16, 8))
        painter.drawLine(QPointF(8, 12), QPointF(16, 12))
        painter.drawLine(QPointF(8, 16), QPointF(13, 16))
    elif name == "matrix":
        for x in (5, 11, 17):
            painter.drawLine(QPointF(x, 5), QPointF(x, 19))
        for y in (5, 12, 19):
            painter.drawLine(QPointF(5, y), QPointF(19, y))
    elif name == "batch":
        for y in (6, 12, 18):
            painter.drawLine(QPointF(8, y), QPointF(19, y))
            painter.drawPoint(QPointF(5, y))
    elif name == "family":
        painter.drawRect(QRectF(5, 6, 14, 12))
        painter.drawLine(QPointF(8, 10), QPointF(16, 10))
        painter.drawLine(QPointF(8, 14), QPointF(13, 14))
        painter.drawLine(QPointF(5, 6), QPointF(9, 3))
        painter.drawLine(QPointF(9, 3), QPointF(19, 3))
        painter.drawLine(QPointF(19, 3), QPointF(19, 6))
    elif name == "conflict":
        painter.drawLine(QPointF(12, 4), QPointF(21, 19))
        painter.drawLine(QPointF(21, 19), QPointF(3, 19))
        painter.drawLine(QPointF(3, 19), QPointF(12, 4))
        painter.drawLine(QPointF(12, 9), QPointF(12, 13))
        painter.drawPoint(QPointF(12, 16))
    elif name == "revision":
        painter.drawRect(QRectF(4, 6, 7, 12))
        painter.drawRect(QRectF(13, 6, 7, 12))
        painter.drawLine(QPointF(8, 10), QPointF(16, 10))
        painter.drawLine(QPointF(14, 8), QPointF(16, 10))
        painter.drawLine(QPointF(14, 12), QPointF(16, 10))
    elif name == "export":
        painter.drawRect(QRectF(5, 6, 14, 13))
        painter.drawLine(QPointF(12, 3), QPointF(12, 13))
        painter.drawLine(QPointF(8, 9), QPointF(12, 13))
        painter.drawLine(QPointF(16, 9), QPointF(12, 13))
    elif name == "rules":
        for x, y in ((7, 8), (13, 14), (18, 9)):
            painter.drawLine(QPointF(x, 5), QPointF(x, 19))
            painter.drawEllipse(QRectF(x - 2, y - 2, 4, 4))
    elif name == "coverage":
        painter.drawArc(QRectF(5, 6, 14, 14), 30 * 16, 120 * 16)
        painter.drawLine(QPointF(12, 15), QPointF(17, 10))
    elif name == "guide":
        painter.drawRoundedRect(QRectF(6, 5, 12, 15), 2, 2)
        painter.drawLine(QPointF(10, 9), QPointF(15, 9))
        painter.drawLine(QPointF(10, 13), QPointF(15, 13))
        painter.drawLine(QPointF(12, 20), QPointF(16, 17))
    elif name == "collapse":
        painter.drawLine(QPointF(8, 6), QPointF(16, 12))
        painter.drawLine(QPointF(16, 12), QPointF(8, 18))
    elif name == "expand":
        painter.drawLine(QPointF(16, 6), QPointF(8, 12))
        painter.drawLine(QPointF(8, 12), QPointF(16, 18))
    elif name == "index":
        painter.drawRect(QRectF(5, 5, 14, 14))
        painter.drawLine(QPointF(8, 8), QPointF(16, 8))
        painter.drawLine(QPointF(8, 12), QPointF(16, 12))
        painter.drawLine(QPointF(8, 16), QPointF(12, 16))
    else:
        painter.drawEllipse(QRectF(5, 5, 14, 14))


def activity_icon(name: str, color: str = "#f5f7f3") -> QIcon:
    names = {
        "Recherche": "search",
        "Corpus": "coverage",
        "Inventaire": "extract",
        "Controle": "conflict",
        "Livrables": "export",
    }
    return line_icon(names.get(name, "search"), color)

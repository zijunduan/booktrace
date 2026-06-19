from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def create_app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    painter.setBrush(QColor("#FFF8ED"))
    painter.setPen(QPen(QColor("#D8C39B"), 3))
    painter.drawRoundedRect(QRectF(5, 5, 54, 54), 13, 13)

    painter.setPen(QPen(QColor("#4A4038"), 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(QColor("#F2E9DA"))
    painter.drawRoundedRect(QRectF(17, 18, 14, 28), 4, 4)
    painter.drawRoundedRect(QRectF(33, 18, 14, 28), 4, 4)

    painter.setPen(QPen(QColor("#8A6A3F"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.drawLine(QPointF(31, 20), QPointF(31, 47))
    painter.drawLine(QPointF(21, 26), QPointF(27, 26))
    painter.drawLine(QPointF(37, 26), QPointF(43, 26))
    painter.drawLine(QPointF(21, 33), QPointF(27, 33))
    painter.drawLine(QPointF(37, 33), QPointF(43, 33))

    painter.end()
    return QIcon(pixmap)

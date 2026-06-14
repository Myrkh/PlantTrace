from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from planttrace.changelog import Release

_ACCENT = QColor("#2f6f62")
_LINE = QColor("#c4cbc2")
_MUTED = QColor("#8a958d")
_ROW_HEIGHT = 70
_DOT_X = 24
_TOP = 28


class Timeline(QWidget):
    """Vertical version timeline: a line, a dot per release, clickable."""

    selected = Signal(int)

    def __init__(self, entries: list[tuple[str, str]]) -> None:
        super().__init__()
        self._entries = entries
        self._current = 0
        self.setFixedWidth(176)
        self.setMinimumHeight(_TOP * 2 + _ROW_HEIGHT * max(len(entries) - 1, 1))

    def set_current(self, index: int) -> None:
        self._current = index
        self.update()

    def _node_y(self, index: int) -> int:
        return _TOP + index * _ROW_HEIGHT

    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if len(self._entries) > 1:
            painter.setPen(QPen(_LINE, 2))
            painter.drawLine(_DOT_X, self._node_y(0), _DOT_X, self._node_y(len(self._entries) - 1))

        version_font = QFont(self.font())
        version_font.setBold(True)
        date_font = QFont(self.font())
        date_font.setPointSizeF(max(version_font.pointSizeF() - 1.5, 7.0))

        for index, (version, date) in enumerate(self._entries):
            center_y = self._node_y(index)
            active = index == self._current
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.setBrush(_ACCENT if active else _LINE)
            radius = 7 if active else 5
            painter.drawEllipse(_DOT_X - radius, center_y - radius, radius * 2, radius * 2)

            painter.setPen(_ACCENT if active else QColor("#26312b"))
            painter.setFont(version_font)
            painter.drawText(_DOT_X + 16, center_y - 2, f"v{version}")
            painter.setPen(_MUTED)
            painter.setFont(date_font)
            painter.drawText(_DOT_X + 16, center_y + 14, date)
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        index = round((event.position().y() - _TOP) / _ROW_HEIGHT)
        if 0 <= index < len(self._entries) and index != self._current:
            self.set_current(index)
            self.selected.emit(index)


class ChangelogDialog(QDialog):
    def __init__(self, parent: object, releases: tuple[Release, ...], on_check_updates: Callable[[], None]) -> None:
        super().__init__(parent)
        self.releases = releases
        self.setObjectName("changelogDialog")
        self.setWindowTitle("Journal des nouveautes")
        self.setModal(False)
        self.resize(780, 560)

        title = QLabel("Journal des nouveautes")
        title.setObjectName("changelogTitle")

        self.scroller = QScrollArea()
        self.scroller.setObjectName("changelogScroller")
        self.scroller.setWidgetResizable(True)
        self.scroller.setFrameShape(QScrollArea.Shape.NoFrame)

        self.timeline = Timeline([(release.version, release.date) for release in releases])
        self.timeline.selected.connect(self.show_release)

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self.scroller, 1)
        body.addWidget(self.timeline)

        check_button = QPushButton("Verifier les mises a jour")
        check_button.setObjectName("secondaryButton")
        check_button.clicked.connect(on_check_updates)
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(check_button)
        footer.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addLayout(body, 1)
        layout.addLayout(footer)

        self.show_release(0)

    def show_release(self, index: int) -> None:
        self.timeline.set_current(index)
        release = self.releases[index]
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        heading = QLabel(f"v{release.version}   .   {release.date}")
        heading.setObjectName("releaseHeading")
        tagline = QLabel(release.tagline)
        tagline.setObjectName("releaseTagline")
        tagline.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(tagline)

        for section in release.sections:
            section_title = QLabel(section.title)
            section_title.setObjectName("sectionTitle")
            layout.addWidget(section_title)
            for item in section.items:
                bullet = QLabel(f"•  {item}")
                bullet.setObjectName("changeItem")
                bullet.setWordWrap(True)
                layout.addWidget(bullet)
        layout.addStretch()
        self.scroller.setWidget(container)

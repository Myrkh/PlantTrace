from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from planttrace.models import SearchResult
from planttrace.pdf_engine import render_page_preview

_CACHE_SIZE = 16
_EMPTY = "Selectionner un resultat pour afficher la page et la preuve."


class PreviewPane(QWidget):
    """Renders the PDF page of the selected result with the matched term highlighted."""

    def __init__(self) -> None:
        super().__init__()
        self._cache: OrderedDict[tuple[str, int], QPixmap] = OrderedDict()
        self._full_pixmap: QPixmap | None = None
        self._current_path = ""

        self.header = QLabel(_EMPTY)
        self.header.setObjectName("previewHeader")
        self.header.setWordWrap(True)
        self.open_button = QPushButton("Ouvrir le PDF")
        self.open_button.setObjectName("secondaryButton")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self._open_external)

        header_row = QHBoxLayout()
        header_row.addWidget(self.header, 1)
        header_row.addWidget(self.open_button)

        self.page_label = QLabel()
        self.page_label.setObjectName("previewPage")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.scroller = QScrollArea()
        self.scroller.setObjectName("previewScroller")
        self.scroller.setWidgetResizable(True)
        self.scroller.setWidget(self.page_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addLayout(header_row)
        layout.addWidget(self.scroller, 1)

    def clear(self) -> None:
        self._full_pixmap = None
        self._current_path = ""
        self.page_label.clear()
        self.header.setText(_EMPTY)
        self.open_button.setEnabled(False)

    def show_result(self, result: SearchResult) -> None:
        if not result.document_path or result.page is None:
            self.clear()
            return
        self._current_path = result.document_path
        self.header.setText(f"{Path(result.document_path).name}  -  p.{result.page}")
        self.open_button.setEnabled(True)
        if result.page_status in {"ocr_required", "ocr_failed"}:
            self._set_message("Page sans texte (OCR requis) : apercu image indisponible.")
            return
        pixmap = self._render(result)
        if pixmap is None:
            self._set_message("Apercu indisponible pour ce document.")
            return
        self._full_pixmap = pixmap
        self.page_label.setPixmap(self._fit(pixmap))

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        if self._full_pixmap is not None:
            self.page_label.setPixmap(self._fit(self._full_pixmap))

    def _set_message(self, text: str) -> None:
        self._full_pixmap = None
        self.page_label.clear()
        self.page_label.setText(text)

    def _render(self, result: SearchResult) -> QPixmap | None:
        key = (result.document_path, result.page)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        terms = list(dict.fromkeys(term for term in (result.found_as, result.query) if term))
        try:
            png, rects = render_page_preview(Path(result.document_path), result.page, terms)
        except Exception:
            return None
        pixmap = QPixmap.fromImage(QImage.fromData(png, "PNG"))
        if rects:
            painter = QPainter(pixmap)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 214, 10, 90))
            for x0, y0, x1, y1 in rects:
                painter.drawRect(int(x0), int(y0), int(x1 - x0), int(y1 - y0))
            painter.end()
        self._cache[key] = pixmap
        if len(self._cache) > _CACHE_SIZE:
            self._cache.popitem(last=False)
        return pixmap

    def _fit(self, pixmap: QPixmap) -> QPixmap:
        width = max(self.scroller.viewport().width() - 4, 200)
        if pixmap.width() <= width:
            return pixmap
        return pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)

    def _open_external(self) -> None:
        if self._current_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._current_path))

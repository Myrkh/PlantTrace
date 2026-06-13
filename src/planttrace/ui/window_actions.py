from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QLineEdit


class PathActionsMixin:
    def choose_project_folder(self) -> None:
        self.choose_folder(self.project_edit)
        self.refresh_coverage()
        self.rules_panel.load_project()

    def choose_folder(self, target: QLineEdit) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Dossier", target.text() or str(Path.cwd()))
        if folder:
            target.setText(folder)

    def project_root(self) -> Path:
        return Path(self.project_edit.text()).expanduser().resolve()


class NavigationActionsMixin:
    def open_search_result(self, row: int, _column: int) -> None:
        if row < len(self.results) and self.results[row].document_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.results[row].document_path))

    def open_guide_html(self) -> None:
        guide = guide_html_path()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(guide)))


def guide_html_path() -> Path:
    return resource_path("docs", "guide.html")


def app_icon_path() -> Path:
    return resource_path("assets", "planttrace.ico")


def resource_path(*parts: str) -> Path:
    module_path = Path(__file__).resolve()
    candidates: list[Path] = []
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root).joinpath(*parts))
    candidates.extend(
        [
            module_path.parents[3].joinpath(*parts),
            module_path.parents[2].joinpath(*parts),
            Path.cwd().joinpath(*parts),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]

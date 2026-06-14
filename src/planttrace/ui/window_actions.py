from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog, QLineEdit, QMessageBox

from ..updates import check_for_update


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
        result = self.result_for_row(row)
        if result is not None and result.document_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(result.document_path))

    def open_guide_html(self) -> None:
        guide = guide_html_path()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(guide)))

    def check_for_updates(self) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            info = check_for_update()
        finally:
            QApplication.restoreOverrideCursor()
        if info is None:
            QMessageBox.warning(self, "PlantTrace", "Verification impossible : aucune connexion a GitHub.")
            return
        if not info.available:
            self._set_version_label(f"V{info.current}", up_to_date=True)
            QMessageBox.information(self, "PlantTrace", f"PlantTrace est a jour (V{info.current}).")
            return
        self._set_version_label(f"V{info.current}  -  MAJ V{info.latest}", up_to_date=False)
        answer = QMessageBox.question(
            self,
            "Mise a jour disponible",
            f"Nouvelle version disponible.\n\nInstallee : V{info.current}\nDerniere : V{info.latest}\n\nOuvrir la page de telechargement ?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(info.url))

    def _set_version_label(self, text: str, *, up_to_date: bool) -> None:
        label = getattr(self, "version_label", None)
        if label is None:
            return
        label.setText(text)
        label.setStyleSheet("" if up_to_date else "color: #ffd479; font-weight: 700;")

    def show_changelog(self) -> None:
        from planttrace.changelog import RELEASES
        from planttrace.ui.changelog_dialog import ChangelogDialog

        dialog = ChangelogDialog(self, RELEASES, self.check_for_updates)
        self.changelog_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()


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

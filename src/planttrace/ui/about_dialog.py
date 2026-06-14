from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from planttrace import __version__
from planttrace.ui.icons import logo_pixmap


class AboutDialog(QDialog):
    def __init__(self, parent: object, on_changelog: Callable[[], None], on_report: Callable[[], None]) -> None:
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setWindowTitle("A propos de PlantTrace")
        self.setModal(True)
        self.setFixedWidth(440)

        logo = QLabel()
        logo.setPixmap(logo_pixmap(72))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name = QLabel("PlantTrace")
        name.setObjectName("aboutName")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version = QLabel(f"Version {__version__}")
        version.setObjectName("aboutVersion")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tagline = QLabel("Recherche et cross-référence documentaire industrielle — 100 % locale.")
        tagline.setObjectName("aboutTagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setWordWrap(True)

        body = QLabel(
            "Indexez vos dossiers PDF, retrouvez n'importe quel tag ou référence avec le fichier, "
            "la page et la preuve, puis produisez vos livrables. Aucune donnée ne quitte votre poste."
        )
        body.setObjectName("aboutBody")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)

        copyright_label = QLabel("Développé par Yoann Dumont · © 2026")
        copyright_label.setObjectName("aboutCopyright")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        report_button = QPushButton("Signaler un bug")
        report_button.setObjectName("secondaryButton")
        report_button.clicked.connect(lambda: self._run(on_report))
        changelog_button = QPushButton("Journal des nouveautés")
        changelog_button.setObjectName("secondaryButton")
        changelog_button.clicked.connect(lambda: self._run(on_changelog))
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(report_button)
        footer.addWidget(changelog_button)
        footer.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(8)
        layout.addWidget(logo)
        layout.addWidget(name)
        layout.addWidget(version)
        layout.addSpacing(4)
        layout.addWidget(tagline)
        layout.addWidget(body)
        layout.addSpacing(6)
        layout.addWidget(copyright_label)
        layout.addSpacing(8)
        layout.addLayout(footer)

    def _run(self, action: Callable[[], None]) -> None:
        self.accept()
        action()

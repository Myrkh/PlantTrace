from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


@dataclass
class ExportAction:
    label: QLabel
    button: QPushButton
    count: Callable[[], int]
    run: Callable[[], None]
    empty_text: str
    ready_text: str


class ExportsPanel(QWidget):
    def __init__(self, window: object) -> None:
        super().__init__()
        self.window = window
        self.summary_label = QLabel()
        self.actions: list[ExportAction] = []
        self.build_ui()

    def build_ui(self) -> None:
        self.summary_label.setObjectName("metricLabel")
        self.summary_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.summary_label)
        self.add_action(
            layout,
            "Pack livrable projet",
            "Archive ZIP locale avec manifeste d'audit, README, exports disponibles et absences batch qualifiees.",
            "Creer pack ZIP",
            self.pack_count,
            self.window.export_project_pack,
            "Lancer au moins une indexation, recherche, batch ou extraction avant pack.",
            "element(s) pret(s) pour le pack.",
        )
        self.add_action(
            layout,
            "Preuve recherche",
            "Occurrences de la derniere recherche : fichier, page, extrait, type de preuve et statuts.",
            "Exporter recherche",
            lambda: len(self.window.results),
            self.window.export_search_xlsx,
            "Lancer une recherche avant export.",
            "resultat(s) de recherche pret(s).",
        )
        self.add_action(
            layout,
            "Matrice batch",
            "Liste de references analysee en masse : present, absent qualifie, documents et pages.",
            "Exporter batch",
            lambda: len(self.window.batch_panel.results),
            self.window.batch_panel.export_results,
            "Lancer une analyse batch avant export.",
            "ligne(s) batch prete(s).",
        )
        self.add_action(
            layout,
            "Inventaire extraction",
            "References detectees automatiquement par les regles projet : TAG, LINE, DOC, INITIALS.",
            "Exporter extraction",
            lambda: len(self.window.extraction_hits),
            self.window.export_extraction_xlsx,
            "Lancer Extraction avant export.",
            "reference(s) extraite(s) prete(s).",
        )
        self.add_action(
            layout,
            "Fiche reference",
            "Dossier consolide d'une reference : occurrences, associations, familles et alertes.",
            "Exporter fiche",
            lambda: 1 if self.window.reference_panel.profile else 0,
            self.window.reference_panel.export_profile,
            "Generer une fiche avant export.",
            "fiche prete.",
        )
        self.add_action(
            layout,
            "Matrice projet",
            "References extraites croisees avec familles documentaires, conflits et revisions.",
            "Exporter matrice",
            lambda: len(self.window.matrix_panel.rows),
            self.window.matrix_panel.export_results,
            "Construire Matrice avant export.",
            "ligne(s) matrice prete(s).",
        )
        self.add_action(
            layout,
            "Template registre TAG",
            "Tableau metier TAG, description, lignes, documents, familles, sources et alertes.",
            "Exporter template",
            lambda: len(self.window.templates_panel.current_run.rows) if self.window.templates_panel.current_run else 0,
            self.window.templates_panel.export_results,
            "Executer Templates avant export.",
            "ligne(s) template prete(s).",
        )
        self.add_action(
            layout,
            "Familles documentaires",
            "Classement des PDF indexés par famille documentaire avec confiance et preuve.",
            "Exporter familles",
            lambda: len(self.window.families_panel.families),
            self.window.families_panel.export_results,
            "Lancer Familles avant export.",
            "document(s) classe(s).",
        )
        self.add_action(
            layout,
            "Conflits potentiels",
            "Valeurs contradictoires detectees autour d'une meme reference, avec documents et pages.",
            "Exporter conflits",
            lambda: len(self.window.conflicts_panel.findings),
            self.window.conflicts_panel.export_results,
            "Lancer Conflits avant export.",
            "conflit(s) pret(s).",
        )
        self.add_action(
            layout,
            "Delta revisions",
            "References ajoutees, supprimees ou modifiees entre deux dossiers PDF de revision.",
            "Exporter revisions",
            lambda: len(self.window.revisions_panel.changes),
            self.window.revisions_panel.export_results,
            "Lancer Revisions avant export.",
            "delta(s) pret(s).",
        )
        self.add_action(
            layout,
            "Rapport couverture",
            "Etat de lecture du corpus : pages texte, OCR requis, OCR echec et couverture par PDF.",
            "Exporter couverture",
            self.coverage_count,
            self.window.coverage_panel.export_report,
            "Indexer le corpus avant export.",
            "document(s) couvert(s).",
        )
        layout.addStretch()
        self.refresh()

    def add_action(
        self,
        layout: QVBoxLayout,
        title: str,
        description: str,
        button_text: str,
        count: Callable[[], int],
        run: Callable[[], None],
        empty_text: str,
        ready_text: str,
    ) -> None:
        row = QFrame()
        row.setObjectName("exportRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(14, 12, 14, 12)
        row_layout.setSpacing(14)

        copy = QVBoxLayout()
        name = QLabel(title)
        name.setObjectName("exportTitle")
        body = QLabel(description)
        body.setObjectName("exportDescription")
        body.setWordWrap(True)
        status = QLabel()
        status.setObjectName("mutedLabel")
        copy.addWidget(name)
        copy.addWidget(body)
        copy.addWidget(status)

        button = QPushButton(button_text)
        button.clicked.connect(lambda: self.run_export(run))
        row_layout.addLayout(copy, 1)
        row_layout.addWidget(button)
        layout.addWidget(row)
        self.actions.append(ExportAction(status, button, count, run, empty_text, ready_text))

    def refresh(self) -> None:
        ready = 0
        for action in self.actions:
            count = action.count()
            enabled = count > 0
            ready += 1 if enabled else 0
            action.button.setEnabled(enabled)
            action.label.setText(f"{count} {action.ready_text}" if enabled else action.empty_text)
        self.summary_label.setText(
            f"{ready}/{len(self.actions)} livrable(s) pret(s). Le pack regroupe ZIP, XLSX et audit local."
        )

    def coverage_count(self) -> int:
        self.window.coverage_panel.refresh()
        return len(self.window.coverage_panel.documents)

    def pack_count(self) -> int:
        return (
            len(self.window.results)
            + len(self.window.batch_panel.results)
            + len(self.window.extraction_hits)
            + (1 if self.window.reference_panel.profile else 0)
            + len(self.window.matrix_panel.rows)
            + (len(self.window.templates_panel.current_run.rows) if self.window.templates_panel.current_run else 0)
            + len(self.window.families_panel.families)
            + len(self.window.conflicts_panel.findings)
            + len(self.window.revisions_panel.changes)
            + self.coverage_count()
        )

    def run_export(self, action: Callable[[], None]) -> None:
        action()
        self.refresh()

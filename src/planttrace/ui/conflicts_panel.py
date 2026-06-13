from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from planttrace.conflicts import ConflictFinding, detect_conflicts
from planttrace.export import export_conflicts


class ConflictsPanel(QWidget):
    def __init__(self, project_root: Callable[[], Path]) -> None:
        super().__init__()
        self.project_root = project_root
        self.findings: list[ConflictFinding] = []
        self.status_label = QLabel()
        self.run_button = QPushButton("Analyser conflits")
        self.export_button = QPushButton("Exporter conflits")
        self.table = QTableWidget(0, 8)
        self.build_ui()

    def build_ui(self) -> None:
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setText("Detecte les valeurs contradictoires autour d'une meme reference. Les resultats sont des conflits potentiels a verifier.")
        self.export_button.setObjectName("secondaryButton")
        self.run_button.clicked.connect(self.run_analysis)
        self.export_button.clicked.connect(self.export_results)
        self.configure_table()

        actions = QHBoxLayout()
        actions.addWidget(self.run_button)
        actions.addWidget(self.export_button)
        actions.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addLayout(actions)
        layout.addWidget(self.table, 1)

    def configure_table(self) -> None:
        headers = ["Reference", "Champ", "Severite", "Valeurs", "Documents", "Pages", "Preuves", "Synthese"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {3, 7} else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(index, mode)

    def run_analysis(self) -> None:
        try:
            self.findings = detect_conflicts(self.project_root())
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Analyse conflits impossible: {exc}")
            return
        self.fill_table()
        self.status_label.setText(f"{len(self.findings)} conflit(s) potentiel(s). Chaque ligne doit etre verifiee avec les sources.")

    def export_results(self) -> None:
        if not self.findings:
            QMessageBox.warning(self, "PlantTrace", "Aucun conflit a exporter.")
            return
        output = self.pick_export_path()
        if output:
            export_conflicts(self.findings, output)
            self.status_label.setText(f"Export conflits: {output}")

    def pick_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export conflits", str(self.project_root() / "planttrace-conflicts.xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def fill_table(self) -> None:
        rows = [conflict_row_values(finding) for finding in self.findings]
        self.table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))


def conflict_row_values(finding: ConflictFinding) -> list[str]:
    return [
        finding.reference,
        finding.field,
        finding.severity,
        finding.values,
        finding.documents,
        finding.pages,
        str(finding.evidence_count),
        finding.summary,
    ]

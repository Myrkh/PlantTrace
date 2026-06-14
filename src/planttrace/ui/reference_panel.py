from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from planttrace.reference_exports import export_reference_profile
from planttrace.reference_profile import ReferenceProfile, build_reference_profile


class ReferencePanel(QWidget):
    def __init__(self, window: object) -> None:
        super().__init__()
        self.window = window
        self.profile: ReferenceProfile | None = None
        self.query_edit = QLineEdit()
        self.status_label = QLabel()
        self.run_button = QPushButton("Generer fiche")
        self.export_button = QPushButton("Exporter fiche")
        self.occurrences_table = QTableWidget(0, 7)
        self.associations_table = QTableWidget(0, 6)
        self.alerts_table = QTableWidget(0, 7)
        self.build_ui()

    def build_ui(self) -> None:
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setText("Consolide une reference : occurrences, familles documentaires, associations, conflits et revisions.")
        self.query_edit.setPlaceholderText("FV1100, 10-P-12345, HTI199...")
        self.query_edit.returnPressed.connect(self.generate_profile)
        self.export_button.setObjectName("secondaryButton")
        self.run_button.clicked.connect(self.generate_profile)
        self.export_button.clicked.connect(self.export_profile)
        self.configure_tables()

        actions = QHBoxLayout()
        actions.addWidget(self.query_edit, 2)
        actions.addWidget(self.run_button)
        actions.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addLayout(actions)
        layout.addWidget(QLabel("Complétude documentaire"))
        self.completeness_widget = QWidget()
        self.completeness_layout = QHBoxLayout(self.completeness_widget)
        self.completeness_layout.setContentsMargins(0, 0, 0, 0)
        self.completeness_layout.setSpacing(6)
        layout.addWidget(self.completeness_widget)
        layout.addWidget(QLabel("Occurrences"))
        layout.addWidget(self.occurrences_table, 2)
        layout.addWidget(QLabel("Associations detectees"))
        layout.addWidget(self.associations_table, 1)
        layout.addWidget(QLabel("Alertes"))
        layout.addWidget(self.alerts_table, 1)

    def configure_tables(self) -> None:
        self.configure_table(self.occurrences_table, ["Famille", "Fichier", "Page", "Type", "Trouve", "Extrait", "Page status"], {1, 5})
        self.configure_table(self.associations_table, ["Type", "Valeur", "Preuves", "Documents", "Pages", "Extrait"], {3, 5})
        self.configure_table(self.alerts_table, ["Source", "Severite", "Champ", "Valeurs", "Documents", "Pages", "Synthese"], {3, 6})

    def configure_table(self, table: QTableWidget, headers: list[str], stretch_columns: set[int]) -> None:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in stretch_columns else QHeaderView.ResizeMode.ResizeToContents
            table.horizontalHeader().setSectionResizeMode(index, mode)

    def generate_profile(self) -> None:
        query = self.query_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "PlantTrace", "Saisir une reference avant de generer la fiche.")
            return
        try:
            self.profile = build_reference_profile(self.window.project_root(), query, self.window.conflicts_panel.findings, self.window.revisions_panel.changes)
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Fiche reference impossible: {exc}")
            return
        self.fill_tables()
        self.status_label.setText(
            f"{self.profile.query}: {self.profile.occurrence_count} occurrence(s), {self.profile.document_count} document(s), "
            f"{self.profile.association_count} association(s), {self.profile.alert_count} alerte(s). Familles: {self.profile.family_summary}"
        )

    def export_profile(self) -> None:
        if self.profile is None:
            QMessageBox.warning(self, "PlantTrace", "Generer une fiche avant export.")
            return
        output = self.pick_export_path()
        if output:
            export_reference_profile(self.profile, output)
            self.status_label.setText(f"Export fiche reference: {output}")

    def pick_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export fiche reference", str(self.window.project_root() / "planttrace-fiche-reference.xlsx"), "Excel (*.xlsx)")
        return Path(output) if output else None

    def fill_completeness(self) -> None:
        while self.completeness_layout.count():
            item = self.completeness_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if self.profile is None:
            return
        for name, present in self.profile.completeness:
            chip = QLabel(name)
            chip.setObjectName("famChipOk" if present else "famChipMissing")
            self.completeness_layout.addWidget(chip)
        self.completeness_layout.addStretch()

    def fill_tables(self) -> None:
        if self.profile is None:
            return
        self.fill_completeness()
        fill_table(self.occurrences_table, [[item.family, item.filename, str(item.page), item.match_type, item.found_as, item.excerpt, item.page_status] for item in self.profile.occurrences])
        fill_table(self.associations_table, [[item.kind, item.value, str(item.evidence_count), item.documents, item.pages, item.excerpt] for item in self.profile.associations])
        fill_table(self.alerts_table, [[item.source, item.severity, item.field, item.values, item.documents, item.pages, item.summary] for item in self.profile.alerts])


def fill_table(table: QTableWidget, rows: list[list[str]]) -> None:
    table.setRowCount(len(rows))
    for row_index, values in enumerate(rows):
        for column, value in enumerate(values):
            table.setItem(row_index, column, QTableWidgetItem(value))

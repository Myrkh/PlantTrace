from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from planttrace.extractor import match_excerpt, normalize_value
from planttrace.models import ExtractionRule
from planttrace.rule_packs import RulePack, available_preset_names, export_rule_pack, import_rule_pack, load_preset_pack, project_rule_pack
from planttrace.rules import load_rules, load_stoplist, save_rules, save_stoplist
from planttrace.ui.rule_builder_panel import RuleBuilderPanel


class RulesPanel(QWidget):
    def __init__(self, project_root: Callable[[], Path]) -> None:
        super().__init__()
        self.project_root = project_root
        self.rules: list[ExtractionRule] = []
        self.sidebar = RuleBuilderPanel()
        self.pack_combo = QComboBox()
        self.apply_pack_button = QPushButton("Charger preset")
        self.import_pack_button = QPushButton("Importer pack")
        self.export_pack_button = QPushButton("Exporter pack")
        self.add_button = QPushButton("Creer")
        self.update_button = QPushButton("Modifier")
        self.test_button = QPushButton("Tester")
        self.save_button = QPushButton("Sauver")
        self.delete_button = QPushButton("Supprimer")
        self.status_label = QLabel()
        self.table = QTableWidget(0, 4)
        self.test_text = QPlainTextEdit()
        self.test_results = QTableWidget(0, 3)
        self.stoplist = QPlainTextEdit()
        self.build_ui()
        self.configure_pack_controls()
        self.load_project()

    def build_ui(self) -> None:
        self.table.setHorizontalHeaderLabels(["Active", "Type", "Nom", "Confiance"])
        self.table.cellClicked.connect(lambda row, _column: self.select_rule(row))
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeaderItem(0).setToolTip("Oui = cette regle est appliquee dans Extraction. Non = elle reste dans le registre mais n'est pas executee.")
        self.table.setMinimumHeight(200)
        self.test_text.setPlaceholderText("Coller ici un extrait de PDF pour tester la regle du panneau gauche.")
        self.test_results.setHorizontalHeaderLabels(["Type", "Valeur", "Extrait"])
        self.test_results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.test_results.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.test_results.setMinimumHeight(150)
        self.stoplist.setPlaceholderText("Valeurs ignorees, une par ligne. Ex: RJ45, BP13, PLAN619")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 12)
        layout.setSpacing(10)
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        layout.addWidget(section("Registre des regles"))
        layout.addLayout(self.registry_actions())
        layout.addWidget(self.table, 2)
        layout.addWidget(section("Tester une regle"))
        layout.addWidget(self.test_text, 1)
        layout.addLayout(self.test_actions())
        layout.addWidget(section("Apercu des valeurs detectees"))
        layout.addWidget(self.test_results, 1)
        layout.addWidget(section("Stoplist projet"))
        layout.addWidget(self.stoplist, 1)

    def configure_pack_controls(self) -> None:
        self.pack_combo.addItems(available_preset_names())
        for button in [self.import_pack_button, self.export_pack_button]:
            button.setObjectName("secondaryButton")
        self.apply_pack_button.clicked.connect(self.apply_preset_pack)
        self.import_pack_button.clicked.connect(self.import_pack)
        self.export_pack_button.clicked.connect(self.export_pack)
        self.add_button.clicked.connect(self.add_rule)
        self.update_button.clicked.connect(self.update_rule)
        self.test_button.clicked.connect(self.test_rule)
        self.save_button.clicked.connect(self.save_project)
        self.delete_button.clicked.connect(self.delete_rule)
        self.delete_button.setObjectName("dangerButton")

    def pack_controls(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(self.pack_combo)
        layout.addWidget(self.apply_pack_button)
        row = QHBoxLayout()
        row.addWidget(self.import_pack_button)
        row.addWidget(self.export_pack_button)
        layout.addLayout(row)
        return layout

    def registry_actions(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(self.add_button)
        row.addWidget(self.update_button)
        row.addWidget(self.save_button)
        row.addWidget(self.delete_button)
        row.addStretch()
        return row

    def test_actions(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(self.test_button)
        row.addStretch()
        return row

    def load_project(self) -> None:
        self.rules = load_rules(self.project_root())
        self.stoplist.setPlainText("\n".join(sorted(load_stoplist(self.project_root()))))
        self.populate_table()
        if self.rules:
            self.table.selectRow(0)
        self.update_status()

    def populate_table(self) -> None:
        self.table.setRowCount(len(self.rules))
        for row, rule in enumerate(self.rules):
            values = ["oui" if rule.enabled else "non", rule.kind, rule.name, rule.confidence]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.update_status()

    def selected_row(self) -> int | None:
        indexes = self.table.selectedIndexes()
        return indexes[0].row() if indexes else None

    def select_rule(self, row: int) -> None:
        if 0 <= row < len(self.rules):
            self.table.selectRow(row)
            self.sidebar.set_rule(self.rules[row])

    def add_rule(self) -> None:
        rule = self.form_rule()
        if not rule:
            return
        self.rules.append(rule)
        self.populate_table()
        self.table.selectRow(len(self.rules) - 1)

    def update_rule(self) -> None:
        row = self.selected_row()
        rule = self.form_rule()
        if row is None or not rule:
            return
        self.rules[row] = rule
        self.populate_table()
        self.table.selectRow(row)

    def delete_rule(self) -> None:
        row = self.selected_row()
        if row is None:
            return
        del self.rules[row]
        self.populate_table()

    def test_rule(self) -> None:
        rule = self.form_rule()
        if not rule:
            return
        rows = []
        sample = self.test_text.toPlainText()
        for match in re.finditer(rule.pattern, sample, flags=re.IGNORECASE):
            rows.append((rule.kind, normalize_value(match.group(0)), match_excerpt(sample, match.start(), match.end())))
        self.fill_test_results(rows)

    def save_project(self) -> None:
        save_rules(self.project_root(), self.rules)
        save_stoplist(self.project_root(), set(self.stoplist.toPlainText().splitlines()))
        self.update_status()
        QMessageBox.information(self, "PlantTrace", "Regles et stoplist sauvegardees.")

    def apply_preset_pack(self) -> None:
        self.apply_pack(load_preset_pack(self.pack_combo.currentText()))

    def import_pack(self) -> None:
        path = self.pick_import_pack_path()
        if not path:
            return
        try:
            self.apply_pack(import_rule_pack(path))
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Import pack impossible: {exc}")

    def export_pack(self) -> None:
        path = self.pick_export_pack_path()
        if not path:
            return
        pack = project_rule_pack("PlantTrace project rules", self.rules, set(self.stoplist.toPlainText().splitlines()))
        try:
            export_rule_pack(pack, path)
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Export pack impossible: {exc}")
            return
        QMessageBox.information(self, "PlantTrace", f"Pack exporte: {path}")

    def apply_pack(self, pack: RulePack) -> None:
        self.rules = list(pack.rules)
        self.stoplist.setPlainText("\n".join(sorted(pack.stoplist)))
        self.populate_table()
        if self.rules:
            self.table.selectRow(0)
            self.select_rule(0)
        self.status_label.setText(f"Pack charge: {pack.name}. Cliquer Sauver pour l'appliquer au projet.")

    def pick_import_pack_path(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(self, "Importer pack de regles", str(self.project_root()), "Rule Pack (*.json)")
        return Path(path) if path else None

    def pick_export_pack_path(self) -> Path | None:
        path, _ = QFileDialog.getSaveFileName(self, "Exporter pack de regles", str(self.project_root() / "planttrace-rule-pack.json"), "Rule Pack (*.json)")
        return Path(path) if path else None

    def form_rule(self) -> ExtractionRule | None:
        try:
            return self.sidebar.current_rule()
        except (ValueError, re.error) as exc:
            QMessageBox.warning(self, "PlantTrace", str(exc))
            return None

    def fill_test_results(self, rows: list[tuple[str, str, str]]) -> None:
        self.test_results.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self.test_results.setItem(row, column, QTableWidgetItem(value))

    def update_status(self) -> None:
        active = sum(1 for rule in self.rules if rule.enabled)
        target = self.project_root() / ".planttrace" / "rules.json"
        state = "sauvegarde" if target.exists() else "non sauvegarde"
        self.status_label.setText(
            f"Registre: {len(self.rules)} regle(s), {active} active(s), etat {state}. "
            "Toutes les regles actives sont appliquees automatiquement quand tu vas dans Extraction puis Extraire."
        )
        self.table.setToolTip(self.status_label.text())


def section(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("panelTitle")
    return label

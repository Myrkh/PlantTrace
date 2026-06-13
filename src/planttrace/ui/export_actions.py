from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from planttrace.deliverable import build_deliverable_pack
from planttrace.export import export_extraction, export_results


class ExportActionsMixin:
    def export_search_xlsx(self) -> None:
        if not self.results:
            return
        output = self.pick_export_path("planttrace-results.xlsx")
        if output:
            export_results(self.results, output)
            self.statusBar().showMessage(f"Export: {output}", 8000)

    def export_extraction_xlsx(self) -> None:
        if not self.extraction_hits:
            return
        output = self.pick_export_path("planttrace-extraction.xlsx")
        if output:
            export_extraction(self.extraction_hits, output)
            self.statusBar().showMessage(f"Export: {output}", 8000)

    def pick_export_path(self, filename: str) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export", str(self.project_root() / filename), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def export_project_pack(self) -> None:
        output = self.pick_pack_path()
        if not output:
            return
        try:
            pack = build_deliverable_pack(
                self.project_root(),
                output,
                self.results,
                self.batch_panel.results,
                self.extraction_hits,
                conflict_findings=self.conflicts_panel.findings,
                revision_changes=self.revisions_panel.changes,
                doc_families=self.families_panel.families,
                reference_profile=self.reference_panel.profile,
                project_matrix=self.matrix_panel.rows,
                template_run=self.templates_panel.current_run,
            )
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Pack livrable impossible: {exc}")
            return
        self.statusBar().showMessage(f"Pack livrable: {pack.output}", 8000)

    def pick_pack_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Pack livrable ZIP", str(self.project_root() / "planttrace-livrable.zip"), "ZIP (*.zip)")
        return Path(output) if output else None

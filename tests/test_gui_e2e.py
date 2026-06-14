from __future__ import annotations

import os
from pathlib import Path

import fitz

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton

from planttrace.app import MainWindow
from tests.support import make_pdf, run_root


def test_gui_end_to_end_user_pipeline(monkeypatch) -> None:
    project_root = run_root()
    pdf_root = project_root / "pdfs"
    pdf_root.mkdir()
    make_pdf(pdf_root / "loop.pdf", ["FV-1100 is connected to line 10-P-12345. JDY checked the Bouygues package."])
    make_pdf(pdf_root / "conflict.pdf", ["FV-1100 is connected to line 10-P-99999."])
    make_blank_pdf(pdf_root / "scan.pdf")
    master_source = project_root / "master-source"
    master_source.mkdir()
    make_master_source(master_source / "HTI199-020-INS-0002-LST_04.xlsx")
    tags_template = project_root / "Tags Template.xlsx"
    links_template = project_root / "Tags Documents Links Template.xlsx"
    make_master_template(tags_template, "Tags List", ["PlantNo", "Site", "TagNo", "Description", "TagType", "Sector", "System", "SubSystem", "Class", "CommunicationTag", "Deleted"])
    make_master_template(links_template, "Tags Documents Links List", ["PlantNo", "TagNo", "Site", "DocumentID", "Deleted"])
    old_revision = project_root / "revision-old"
    new_revision = project_root / "revision-new"
    old_revision.mkdir()
    new_revision.mkdir()
    make_pdf(old_revision / "pid.pdf", ["FV-1100 is connected to line 10-P-12345. PT-2000 remains old only."])
    make_pdf(new_revision / "pid.pdf", ["FV-1100 is connected to line 10-P-99999. XV-3000 is new only."])

    app = QApplication.instance() or QApplication([])
    messages: list[tuple[str, str]] = []
    opened_urls: list[str] = []
    export_index = {"count": 0}

    monkeypatch.setattr(QMessageBox, "information", lambda _parent, title, text: messages.append((title, text)))
    monkeypatch.setattr(QMessageBox, "warning", lambda _parent, title, text: messages.append((title, text)))
    monkeypatch.setattr(QMessageBox, "critical", lambda _parent, title, text: messages.append((title, text)))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", folder_picker(project_root, pdf_root))
    monkeypatch.setattr("planttrace.ui.workers.rebuild_embeddings", lambda _project_root: 0)

    window = MainWindow()
    monkeypatch.setattr(window, "run_worker", sync_worker(window))
    monkeypatch.setattr(window, "pick_export_path", lambda filename: next_export_path(project_root, filename, export_index))
    monkeypatch.setattr(window.batch_panel, "pick_export_path", lambda: next_export_path(project_root, "planttrace-batch.xlsx", export_index))
    monkeypatch.setattr(window.coverage_panel, "pick_export_path", lambda: next_export_path(project_root, "planttrace-coverage.xlsx", export_index))
    monkeypatch.setattr(window.coverage_panel, "pick_triage_export_path", lambda: project_root / "ocr-triage.xlsx")
    monkeypatch.setattr(window.reference_panel, "pick_export_path", lambda: project_root / "reference.xlsx")
    monkeypatch.setattr(window.matrix_panel, "pick_export_path", lambda: project_root / "matrix.xlsx")
    monkeypatch.setattr(window.templates_panel, "pick_export_path", lambda: project_root / "template.xlsx")
    monkeypatch.setattr(window.families_panel, "pick_export_path", lambda: project_root / "families.xlsx")
    monkeypatch.setattr(window.conflicts_panel, "pick_export_path", lambda: project_root / "conflicts.xlsx")
    monkeypatch.setattr(window.revisions_panel, "pick_export_path", lambda: project_root / "revisions.xlsx")
    monkeypatch.setattr(window, "pick_pack_path", lambda: next_export_path(project_root, "planttrace-livrable.zip", export_index))
    monkeypatch.setattr(window.rules_panel, "pick_export_pack_path", lambda: project_root / "rules-pack.json")
    monkeypatch.setattr(window.rules_panel, "pick_import_pack_path", lambda: project_root / "rules-pack.json")
    monkeypatch.setattr("planttrace.ui.window_actions.QDesktopServices.openUrl", lambda url: opened_urls.append(url.toLocalFile()) or True)
    monkeypatch.setattr("planttrace.ui.coverage_panel.QDesktopServices.openUrl", lambda url: opened_urls.append(url.toLocalFile()) or True)

    window.resize(1440, 820)
    window.show()
    app.processEvents()
    screenshots = project_root / "screenshots"
    screenshots.mkdir()

    grab(window, screenshots / "01-search-open.png")
    click_folder_buttons(window)
    assert Path(window.project_edit.text()) == project_root
    assert Path(window.pdf_edit.text()) == pdf_root
    assert_visible_button(window, "Indexer")
    assert_visible_button(window, "Vectoriser")

    window.index_button.click()
    assert "docs 3" in window.coverage_label.text()
    window.embed_button.click()
    assert window.index_button.isEnabled()

    window.query_edit.setText("FV1100")
    window.search_button.click()
    assert window.results
    assert window.results[0].found_as == "FV-1100"
    window.search_export_button.click()
    assert (project_root / "export-1-planttrace-results.xlsx").exists()
    window.open_search_result(0, 0)
    assert opened_urls[-1].endswith(".pdf")

    click_subactivity(window, "Corpus", "Familles")
    for text in ["Classifier documents", "Exporter familles"]:
        assert_visible_button(window.families_panel, text)
    click_button(window.families_panel, "Classifier documents")
    assert table_contains(window.families_panel.table, "Loop diagram")
    click_button(window.families_panel, "Exporter familles")
    assert (project_root / "families.xlsx").exists()
    grab(window, screenshots / "02-families-after-run.png")

    click_subactivity(window, "Controle", "Batch")
    window.batch_panel.references_edit.setPlainText("FV1100\nJDY\nNOHITVALUE")
    window.batch_panel.run_button.click()
    assert table_contains(window.batch_panel.table, "FV1100")
    assert table_contains(window.batch_panel.table, "absent_indexed_text")
    window.batch_panel.export_button.click()
    assert (project_root / "export-2-planttrace-batch.xlsx").exists()
    grab(window, screenshots / "03-batch-after-run.png")

    click_subactivity(window, "Inventaire", "Regles")
    assert window.stack.currentIndex() == 2
    assert window.side_stack.currentIndex() == 1
    for text in ["Charger preset", "Importer pack", "Exporter pack", "Creer", "Modifier", "Tester", "Sauver", "Supprimer"]:
        assert_visible_button(window, text)
    grab(window, screenshots / "04-rules-open.png")

    rules = window.rules_panel
    rules.sidebar.name.setText("Tags E2E")
    rules.sidebar.prefixes.setText("FV, PT")
    rules.sidebar.min_digits.setCurrentText("3")
    rules.sidebar.max_digits.setCurrentText("5")
    rules.test_text.setPlainText("FV-1100 and PT2045A are in this loop note.")
    click_button(window, "Tester")
    assert table_contains(rules.test_results, "FV-1100")

    start_count = rules.table.rowCount()
    click_button(window, "Creer")
    assert rules.table.rowCount() == start_count + 1
    rules.sidebar.name.setText("Tags E2E modifies")
    click_button(window, "Modifier")
    assert table_contains(rules.table, "Tags E2E modifies")
    click_button(window, "Exporter pack")
    assert (project_root / "rules-pack.json").exists()
    click_button(window, "Charger preset")
    assert table_contains(rules.table, "Instrument tags")
    click_button(window, "Importer pack")
    assert table_contains(rules.table, "Tags E2E modifies")
    click_button(window, "Sauver")
    assert (project_root / ".planttrace" / "rules.json").exists()

    click_subactivity(window, "Inventaire", "Extraction")
    assert window.side_panel.isHidden()
    window.extract_button.click()
    assert table_contains(window.extract_table, "FV-1100")
    window.extract_export_button.click()
    assert (project_root / "export-3-planttrace-extraction.xlsx").exists()
    grab(window, screenshots / "05-extraction-after-run.png")

    click_subactivity(window, "Controle", "Conflits")
    for text in ["Analyser conflits", "Exporter conflits"]:
        assert_visible_button(window.conflicts_panel, text)
    click_button(window.conflicts_panel, "Analyser conflits")
    assert table_contains(window.conflicts_panel.table, "FV-1100")
    assert table_contains(window.conflicts_panel.table, "10-P-99999")
    click_button(window.conflicts_panel, "Exporter conflits")
    assert (project_root / "conflicts.xlsx").exists()
    grab(window, screenshots / "06-conflicts-after-run.png")

    click_subactivity(window, "Controle", "Revisions")
    for text in ["Comparer revisions", "Exporter delta"]:
        assert_visible_button(window.revisions_panel, text)
    window.revisions_panel.old_edit.setText(str(old_revision))
    window.revisions_panel.new_edit.setText(str(new_revision))
    click_button(window.revisions_panel, "Comparer revisions")
    assert table_contains(window.revisions_panel.table, "FV-1100")
    assert table_contains(window.revisions_panel.table, "modified")
    click_button(window.revisions_panel, "Exporter delta")
    assert (project_root / "revisions.xlsx").exists()
    grab(window, screenshots / "07-revisions-after-run.png")

    click_subactivity(window, "Inventaire", "Templates")
    for text in ["Executer template", "Exporter template"]:
        assert_visible_button(window.templates_panel, text)
    click_button(window.templates_panel, "Executer template")
    assert table_contains(window.templates_panel.table, "FV-1100")
    assert table_contains(window.templates_panel.table, "10-P-12345")
    click_button(window.templates_panel, "Exporter template")
    assert (project_root / "template.xlsx").exists()
    grab(window, screenshots / "08-templates-after-run.png")

    click_subactivity(window, "Livrables", "Master Register")
    window.master_register_panel.source_edit.setText(str(master_source))
    window.master_register_panel.tags_template_edit.setText(str(tags_template))
    window.master_register_panel.links_template_edit.setText(str(links_template))
    window.master_register_panel.output_edit.setText(str(project_root / "master-register"))
    window.master_register_panel.plant_edit.setText("HTI199")
    window.master_register_panel.site_edit.setText("GPS")
    click_button(window.master_register_panel, "Generer Master Register")
    assert table_contains(window.master_register_panel.table, "520FT1101")
    assert (project_root / "master-register" / "Tags Template - PlantTrace.xlsx").exists()
    assert (project_root / "master-register" / "Tags Documents Links Template - PlantTrace.xlsx").exists()
    grab(window, screenshots / "09-master-register-after-run.png")

    click_subactivity(window, "Controle", "Matrice")
    for text in ["Construire matrice", "Exporter matrice"]:
        assert_visible_button(window.matrix_panel, text)
    click_button(window.matrix_panel, "Construire matrice")
    assert table_contains(window.matrix_panel.table, "FV-1100")
    assert table_contains(window.matrix_panel.table, "high:LINE")
    click_button(window.matrix_panel, "Exporter matrice")
    assert (project_root / "matrix.xlsx").exists()
    grab(window, screenshots / "10-matrix-after-run.png")

    click_subactivity(window, "Recherche", "Fiche")
    for text in ["Generer fiche", "Exporter fiche"]:
        assert_visible_button(window.reference_panel, text)
    window.reference_panel.query_edit.setText("FV1100")
    click_button(window.reference_panel, "Generer fiche")
    assert table_contains(window.reference_panel.occurrences_table, "FV-1100")
    assert table_contains(window.reference_panel.associations_table, "10-P-12345")
    assert table_contains(window.reference_panel.alerts_table, "Conflits")
    click_button(window.reference_panel, "Exporter fiche")
    assert (project_root / "reference.xlsx").exists()
    grab(window, screenshots / "11-reference-after-run.png")

    click_subactivity(window, "Corpus", "Couverture")
    assert not window.side_panel.isHidden()
    assert table_contains(window.coverage_panel.table, "loop.pdf")
    assert table_contains(window.coverage_panel.task_table, "scan.pdf")
    window.coverage_panel.filter_combo.setCurrentText("OK")
    assert table_contains(window.coverage_panel.table, "loop.pdf")
    window.coverage_panel.filter_combo.setCurrentText("Tous")
    for text in ["Ouvrir PDF", "Exporter triage OCR"]:
        assert_visible_button(window.coverage_panel, text)
    window.coverage_panel.task_table.selectRow(0)
    click_button(window.coverage_panel, "Ouvrir PDF")
    assert opened_urls[-1].endswith("scan.pdf")
    click_button(window.coverage_panel, "Exporter triage OCR")
    assert (project_root / "ocr-triage.xlsx").exists()
    window.coverage_panel.export_button.click()
    assert (project_root / "export-4-planttrace-coverage.xlsx").exists()
    grab(window, screenshots / "12-coverage-after-run.png")

    click_subactivity(window, "Livrables", "Exports")
    assert window.side_panel.isHidden()
    for text in ["Creer pack ZIP", "Exporter recherche", "Exporter batch", "Exporter extraction", "Exporter fiche", "Exporter matrice", "Exporter template", "Exporter familles", "Exporter conflits", "Exporter revisions", "Exporter couverture"]:
        assert_visible_button(window.exports_panel, text)
    click_button(window.exports_panel, "Creer pack ZIP")
    click_button(window.exports_panel, "Exporter recherche")
    click_button(window.exports_panel, "Exporter batch")
    click_button(window.exports_panel, "Exporter extraction")
    click_button(window.exports_panel, "Exporter fiche")
    click_button(window.exports_panel, "Exporter matrice")
    click_button(window.exports_panel, "Exporter template")
    click_button(window.exports_panel, "Exporter familles")
    click_button(window.exports_panel, "Exporter conflits")
    click_button(window.exports_panel, "Exporter revisions")
    click_button(window.exports_panel, "Exporter couverture")
    assert (project_root / "export-5-planttrace-livrable.zip").exists()
    assert (project_root / "export-6-planttrace-results.xlsx").exists()
    assert (project_root / "export-7-planttrace-batch.xlsx").exists()
    assert (project_root / "export-8-planttrace-extraction.xlsx").exists()
    assert (project_root / "export-9-planttrace-coverage.xlsx").exists()
    assert (project_root / "reference.xlsx").exists()
    assert (project_root / "matrix.xlsx").exists()
    assert (project_root / "template.xlsx").exists()
    assert (project_root / "families.xlsx").exists()
    assert (project_root / "conflicts.xlsx").exists()
    assert (project_root / "revisions.xlsx").exists()
    grab(window, screenshots / "13-exports-ready.png")

    click_subactivity(window, "Inventaire", "Regles")
    selected_count = rules.table.rowCount()
    rules.table.selectRow(selected_count - 1)
    click_button(window, "Supprimer")
    assert rules.table.rowCount() == selected_count - 1

    trigger_menu_action(window, "Ouvrir le guide HTML local")
    assert opened_urls[-1].endswith("guide.html")
    assert Path(opened_urls[-1]).exists()

    click_every_activity(window)
    toggle = find_button(window, "Replier")
    toggle.click()
    assert window.activity_collapsed is True
    toggle.click()
    assert window.activity_collapsed is False

    for path in screenshots.glob("*.png"):
        assert path.stat().st_size > 0
    window.close()


def sync_worker(window: MainWindow):
    def run(worker, finished_slot):
        worker.finished.connect(finished_slot)
        worker.failed.connect(window.on_worker_failed)
        worker.run()
        return False

    return run


def folder_picker(project_root: Path, pdf_root: Path):
    calls = {"count": 0}

    def pick(_parent, _title, _start):
        calls["count"] += 1
        return str(project_root if calls["count"] == 1 else pdf_root)

    return pick


def make_blank_pdf(path: Path) -> None:
    document = fitz.open()
    document.new_page()
    document.save(path)
    document.close()


def make_master_template(path: Path, sheet_name: str, headers: list[str]) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(headers)
    workbook.save(path)


def make_master_source(path: Path) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "LISTE"
    sheet.append(["TAG", "SERVICE", "FONCTION", "PID", "DATA SHEET", "SYSTEME_FUT"])
    sheet.append(["520FT1101", "CHARGE PTT UCO", "DELTA P", "HTI199-020-PRO-3304-PID", "HTI199-020-INS-2235-SPE", "UCN16 HPM11/12"])
    workbook.save(path)


def next_export_path(project_root: Path, filename: str, index: dict[str, int]) -> Path:
    index["count"] += 1
    return project_root / f"export-{index['count']}-{filename}"


def click_folder_buttons(window: MainWindow) -> None:
    buttons = [button for button in window.side_stack.findChildren(QPushButton) if button.objectName() == "folderButton"]
    assert len(buttons) >= 2
    buttons[0].click()
    buttons[1].click()


def click_activity(window: MainWindow, text: str) -> None:
    find_button(window, text, object_name="activityButton").click()


def click_subactivity(window: MainWindow, activity: str, subactivity: str) -> None:
    click_activity(window, activity)
    tabs = window.subactivity_tabs[activity]
    for index in range(tabs.count()):
        if tabs.tabText(index) == subactivity:
            tabs.setCurrentIndex(index)
            return
    raise AssertionError(f"Tab not found: {activity}/{subactivity}")


def click_every_activity(window: MainWindow) -> None:
    for text in ["Recherche", "Corpus", "Inventaire", "Controle", "Livrables"]:
        click_activity(window, text)


def click_button(root: object, text: str) -> None:
    find_button(root, text).click()


def find_button(root: object, text: str, object_name: str | None = None) -> QPushButton:
    for button in root.findChildren(QPushButton):
        if button.text() == text and (object_name is None or button.objectName() == object_name):
            return button
    raise AssertionError(f"Button not found: {text}")


def assert_visible_button(root: object, text: str) -> None:
    button = find_button(root, text)
    assert button.isVisible()
    assert button.isEnabled()
    assert button.width() > 0
    assert button.height() > 0


def trigger_menu_action(window: MainWindow, text: str) -> None:
    for menu_action in window.menuBar().actions():
        menu = menu_action.menu()
        if not menu:
            continue
        for action in menu.actions():
            if action.text() == text:
                action.trigger()
                return
    raise AssertionError(f"Menu action not found: {text}")


def table_contains(table, expected: str) -> bool:
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            item = table.item(row, column)
            if item and expected in item.text():
                return True
    return False


def grab(window: MainWindow, output: Path) -> None:
    window.grab().save(str(output))

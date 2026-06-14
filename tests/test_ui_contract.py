from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QScrollArea

from planttrace.app import MainWindow
from planttrace.cli import main as cli_main
from planttrace.models import ExtractionHit, SearchResult
from planttrace.ui.command_palette import CommandPalette, build_commands
from planttrace.ui.presenters import extraction_row_values, result_row_values
from planttrace.ui.rules_panel import RulesPanel
from planttrace.ui.views import ACTIVITIES
from planttrace.ui.window_actions import app_icon_path, guide_html_path
from tests.support import make_pdf, run_root


def test_activity_contract_is_stable() -> None:
    assert ACTIVITIES == ["Recherche", "Corpus", "Inventaire", "Controle", "Livrables"]
    assert RulesPanel is not None


def test_local_icons_are_available() -> None:
    assert (Path("assets") / "planttrace-logo.svg").exists()
    assert (Path("assets") / "planttrace.ico").exists()
    assert (Path("docs") / "guide.html").exists()


def test_guide_path_prefers_pyinstaller_bundle(monkeypatch) -> None:
    bundle_root = run_root()
    guide = bundle_root / "docs" / "guide.html"
    icon = bundle_root / "assets" / "planttrace.ico"
    guide.parent.mkdir()
    icon.parent.mkdir()
    guide.write_text("<!doctype html>", encoding="utf-8")
    icon.write_bytes(b"icon")

    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_root), raising=False)

    assert guide_html_path() == guide
    assert app_icon_path() == icon


def test_main_window_constructs_without_event_loop() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.windowTitle() == "PlantTrace"
    assert not window.windowIcon().isNull()
    assert window.stack.count() == 5
    assert window.subactivity_tabs["Recherche"].count() == 2
    assert window.subactivity_tabs["Inventaire"].count() == 3
    assert window.subactivity_tabs["Livrables"].count() == 2
    assert isinstance(window.subactivity_tabs["Livrables"].widget(0), QScrollArea)
    assert [action.text() for action in window.menuBar().actions()] == ["Fichier", "Modifier", "Affichage", "Fenetre", "Outils", "Aide"]
    tool_actions = [action for action in window.menuBar().actions() if action.text() == "Outils"][0].menu().actions()
    palette_action = [action for action in tool_actions if action.text() == "Palette de commande"][0]
    assert palette_action.shortcut().toString() == "Ctrl+Shift+P"
    assert window.rules_panel.sidebar is not None
    assert window.exports_panel is not None
    assert window.master_register_panel is not None
    assert not window.side_panel.isHidden()
    assert window.side_stack.currentWidget().widget().width() <= window.side_stack.width()
    window.on_activity_selected(1)
    assert not window.side_panel.isHidden()
    window.on_activity_selected(2)
    assert not window.side_panel.isHidden()
    window.subactivity_tabs["Inventaire"].setCurrentIndex(1)
    assert window.side_panel.isHidden()
    window.on_activity_selected(3)
    assert window.side_panel.isHidden()
    assert any(button.text() == "Indexer" for button in window.findChildren(QPushButton))
    window.activity_toggle_button.click()
    assert window.activity_collapsed is True
    assert window.activity_toggle_button.text() == ""
    assert not window.activity_toggle_button.icon().isNull()
    window.activity_toggle_button.click()
    assert window.activity_collapsed is False
    assert any(button.text() == "Sauver" for button in window.findChildren(QPushButton))
    assert "Extraction" in window.rules_panel.status_label.text()

    window.close()


def test_command_palette_filters_and_runs_navigation() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    commands = build_commands(window)

    assert any(command.title == "Indexer" for command in commands)
    assert any(command.title == "Inventaire > Regles" for command in commands)
    assert any(command.title == "Controle > Conflits" for command in commands)

    palette = CommandPalette(window, commands)
    palette.search.setText("conflits")
    palette.execute_current()

    assert window.stack.currentIndex() == ACTIVITIES.index("Controle")
    assert window.subactivity_tabs["Controle"].tabText(window.subactivity_tabs["Controle"].currentIndex()) == "Conflits"

    window.close()


def test_command_palette_corpus_search_groups_by_family() -> None:
    app = QApplication.instance() or QApplication([])
    root = run_root()
    pdf_dir = root / "pdfs"
    pdf_dir.mkdir()
    make_pdf(pdf_dir / "loop_diagram.pdf", ["Loop diagram FV-1100 process control"])
    cli_main(["index", "--project", str(root), "--pdf-root", str(pdf_dir), "--force"])

    window = MainWindow()
    window.project_edit.setText(str(root.resolve()))
    palette = CommandPalette(window, build_commands(window))
    palette.search.setText("FV1100")
    palette.run_corpus_search()

    texts = [palette.list.item(index).text() for index in range(palette.list.count())]
    assert any("FV-1100" in text for text in texts)
    assert "Loop diagram" in texts

    window.close()


def test_search_presenter_matches_table_contract() -> None:
    result = SearchResult("FV1100", "exact_normalized", "loop.pdf", 1, 100.0, "FV-1100", "excerpt", "ok", "ok")

    row = result_row_values(result)

    assert row == ["exact_normalized", "loop.pdf", "1", "100.0000", "FV-1100", "excerpt", "ok", "ok"]


def test_extraction_presenter_matches_table_contract() -> None:
    hit = ExtractionHit("TAG", "FV-1100", "Instrument tags", "loop.pdf", 1, "excerpt", "high", "ok", "ok")

    row = extraction_row_values(hit)

    assert row == ["TAG", "FV-1100", "Instrument tags", "loop.pdf", "1", "excerpt", "high", "ok", "ok"]

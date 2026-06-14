from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFormLayout, QMenu, QMessageBox, QSpinBox, QComboBox, QTableWidget

from planttrace.pdf_engine import ocr_available
from planttrace.semantic import semantic_status
from planttrace.ui.views import select_activity_by_name, select_subactivity, set_activity_bar_collapsed
from planttrace.ui.window_actions import app_icon_path, guide_html_path


def build_menu_bar(window: object) -> None:
    file_menu = add_menu(window, "Fichier")
    add_action(file_menu, "Ouvrir projet...", window.choose_project_folder, "Ctrl+O")
    add_action(file_menu, "Choisir dossier PDF...", lambda: window.choose_folder(window.pdf_edit))
    file_menu.addSeparator()
    add_action(file_menu, "Exporter livrable ZIP", window.export_project_pack, "Ctrl+E")
    file_menu.addSeparator()
    add_action(file_menu, "Quitter", window.close, "Alt+F4")

    edit_menu = add_menu(window, "Modifier")
    add_action(edit_menu, "Copier lignes selectionnees", lambda: copy_selected_rows(window), "Ctrl+C")
    add_action(edit_menu, "Copier chemins PDF", lambda: copy_selected_column(window, ["Fichier"]))
    add_action(edit_menu, "Copier extraits", lambda: copy_selected_column(window, ["Extrait"]))

    view_menu = add_menu(window, "Affichage")
    add_action(view_menu, "Replier la barre d'activite", lambda: set_activity_bar_collapsed(window, window.activity_buttons, window.activity_toggle_button, True))
    add_action(view_menu, "Deplier la barre d'activite", lambda: set_activity_bar_collapsed(window, window.activity_buttons, window.activity_toggle_button, False))
    add_action(view_menu, "Masquer / afficher le panneau lateral", window.toggle_side_panel, "Ctrl+B")
    view_menu.addSeparator()
    add_action(view_menu, "Recherche", lambda: select_activity_by_name(window, "Recherche"))
    add_action(view_menu, "Corpus", lambda: select_activity_by_name(window, "Corpus"))
    add_action(view_menu, "Inventaire", lambda: select_activity_by_name(window, "Inventaire"))
    add_action(view_menu, "Controle", lambda: select_activity_by_name(window, "Controle"))
    add_action(view_menu, "Livrables", lambda: select_activity_by_name(window, "Livrables"))

    window_menu = add_menu(window, "Fenetre")
    add_action(window_menu, "Plein ecran", lambda: toggle_full_screen(window), "F11")
    add_action(window_menu, "Reinitialiser disposition", lambda: reset_layout(window))

    tools_menu = add_menu(window, "Outils")
    add_action(tools_menu, "Palette de commande", lambda: open_command_palette(window), "Ctrl+Shift+P")
    tools_menu.addSeparator()
    add_action(tools_menu, "Indexer", window.start_index)
    add_action(tools_menu, "Vectoriser", window.start_embed)
    add_action(tools_menu, "Verifier couverture", lambda: select_subactivity(window, "Corpus", "Couverture"))
    tools_menu.addSeparator()
    add_action(tools_menu, "Parametres...", lambda: open_settings(window))
    add_action(tools_menu, "Diagnostic environnement", lambda: show_environment_diagnostic(window))

    help_menu = add_menu(window, "Aide")
    add_action(help_menu, "Ouvrir le guide HTML local", window.open_guide_html, "F1")
    add_action(help_menu, "Verifier les mises a jour", window.check_for_updates)
    add_action(help_menu, "Signaler un bug", window.report_bug)
    add_action(help_menu, "A propos de PlantTrace", lambda: show_about(window))
    window.planttrace_menus = [file_menu, edit_menu, view_menu, window_menu, tools_menu, help_menu]


def add_menu(window: object, title: str) -> QMenu:
    menu = QMenu(title, window.menuBar())
    window.menuBar().addMenu(menu)
    return menu


def add_action(menu: object, text: str, callback: object, shortcut: str | None = None) -> QAction:
    action = QAction(text, menu)
    if shortcut:
        action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(lambda _checked=False: callback())
    menu.addAction(action)
    return action


def current_table(window: object) -> QTableWidget | None:
    focused = QApplication.focusWidget()
    if isinstance(focused, QTableWidget):
        return focused
    for table in window.findChildren(QTableWidget):
        if table.isVisible() and table.selectionModel().hasSelection():
            return table
    return None


def copy_selected_rows(window: object) -> None:
    table = current_table(window)
    if table is None:
        window.statusBar().showMessage("Aucune table selectionnee.", 5000)
        return
    rows = sorted({index.row() for index in table.selectedIndexes()})
    if not rows and table.currentRow() >= 0:
        rows = [table.currentRow()]
    text = "\n".join(row_text(table, row) for row in rows)
    QApplication.clipboard().setText(text)
    window.statusBar().showMessage(f"{len(rows)} ligne(s) copiee(s).", 5000)


def toggle_full_screen(window: object) -> None:
    if window.isFullScreen():
        window.showNormal()
    else:
        window.showFullScreen()


def reset_layout(window: object) -> None:
    set_activity_bar_collapsed(window, window.activity_buttons, window.activity_toggle_button, False)
    select_activity_by_name(window, "Recherche")
    window.statusBar().showMessage("Disposition reinitialisee.", 5000)


def copy_selected_column(window: object, headers: list[str]) -> None:
    table = current_table(window)
    if table is None:
        window.statusBar().showMessage("Aucune table selectionnee.", 5000)
        return
    column = find_column(table, headers)
    if column is None:
        window.statusBar().showMessage("Colonne introuvable dans la table active.", 5000)
        return
    rows = sorted({index.row() for index in table.selectedIndexes()}) or list(range(table.rowCount()))
    values = [table.item(row, column).text() for row in rows if table.item(row, column)]
    QApplication.clipboard().setText("\n".join(values))
    window.statusBar().showMessage(f"{len(values)} valeur(s) copiee(s).", 5000)


def row_text(table: QTableWidget, row: int) -> str:
    values: list[str] = []
    for column in range(table.columnCount()):
        item = table.item(row, column)
        values.append(item.text() if item else "")
    return "\t".join(values)


def find_column(table: QTableWidget, headers: list[str]) -> int | None:
    for column in range(table.columnCount()):
        header = table.horizontalHeaderItem(column)
        if header and header.text() in headers:
            return column
    return None


def open_settings(window: object) -> None:
    dialog = QDialog(window)
    dialog.setWindowTitle("Parametres PlantTrace")

    ocr_lang = QComboBox(dialog)
    ocr_lang.addItems(["eng", "fra", "eng+fra"])
    ocr_lang.setCurrentText(window.ocr_lang_edit.text().strip() or "eng")

    max_results = QSpinBox(dialog)
    max_results.setRange(25, 5000)
    max_results.setSingleStep(25)
    max_results.setValue(window.max_search_results)

    form = QFormLayout(dialog)
    form.addRow("Langue OCR par defaut", ocr_lang)
    form.addRow("Resultats recherche max", max_results)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        window.ocr_lang_edit.setText(ocr_lang.currentText())
        window.max_search_results = max_results.value()
        window.statusBar().showMessage("Parametres appliques.", 5000)


def show_environment_diagnostic(window: object) -> None:
    status = semantic_status(window.project_root())
    lines = [
        f"Projet: {window.project_root()}",
        f"Dossier PDF: {Path(window.pdf_edit.text()).expanduser() if window.pdf_edit.text() else '(non defini)'}",
        f"OCR Tesseract: {'detecte' if ocr_available() else 'non detecte'}",
        f"Semantique: {'active' if status.available else 'offline'} - {status.message}",
        f"Guide HTML: {guide_html_path()}",
        f"Icone app: {app_icon_path()}",
    ]
    QMessageBox.information(window, "Diagnostic PlantTrace", "\n".join(lines))


def show_about(window: object) -> None:
    from planttrace.ui.about_dialog import AboutDialog

    AboutDialog(window, window.show_changelog, window.report_bug).exec()


def open_command_palette(window: object) -> None:
    from planttrace.ui.command_palette import open_command_palette as open_palette

    open_palette(window)

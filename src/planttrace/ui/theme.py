from __future__ import annotations


APP_STYLESHEET = """
QMainWindow {
    background: #f4f5f3;
}
QWidget#appShell {
    background: #f4f5f3;
}
QWidget {
    color: #1f2522;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMenuBar {
    background: #ffffff;
    border-bottom: 1px solid #d6dcd4;
}
QMenuBar::item {
    padding: 5px 10px;
    background: transparent;
}
QMenuBar::item:selected {
    background: #edf1eb;
}
QMenu {
    background: #ffffff;
    border: 1px solid #c8cec7;
}
QMenu::item {
    padding: 6px 28px 6px 18px;
}
QMenu::item:selected {
    background: #edf1eb;
}
QTabWidget#activityTabs::pane {
    border: 0;
    padding-top: 8px;
}
QWidget#pageRoot {
    background: #ffffff;
    border: 1px solid #d6dcd4;
    border-radius: 10px;
}
QTabBar::tab {
    background: #e7ebe5;
    color: #26312b;
    border: 1px solid #c4cbc2;
    border-radius: 4px;
    padding: 7px 14px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    background: #2f6f62;
    color: #ffffff;
    border-color: #2f6f62;
}
QTabBar::tab:hover:!selected {
    background: #dce2da;
}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {
    background: #ffffff;
    border: 1px solid #c8cec7;
    border-radius: 6px;
    min-height: 30px;
    padding: 4px 8px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {
    border: 1px solid #287a68;
}
QPushButton {
    background: #2f6f62;
    color: #ffffff;
    border: 0;
    border-radius: 6px;
    min-height: 32px;
    padding: 6px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background: #245f55;
}
QPushButton#primaryButton {
    background: #2f6f62;
    color: #ffffff;
    border: 0;
}
QPushButton#primaryButton:hover {
    background: #245f55;
}
QPushButton#secondaryButton {
    background: #e7ebe5;
    color: #1f2522;
    border: 1px solid #c4cbc2;
}
QPushButton#secondaryButton:hover {
    background: #dce2da;
}
QPushButton#dangerButton {
    background: #f4e8e4;
    color: #7b3e31;
    border: 1px solid #d8b8ae;
}
QPushButton#dangerButton:hover {
    background: #ecd9d3;
}
QPushButton#folderButton {
    background: #e7ebe5;
    color: #1f2522;
    border: 1px solid #c4cbc2;
    min-width: 38px;
}
QPushButton#folderButton:hover {
    background: #dce2da;
}
QFrame#sidePanel {
    background: #ffffff;
    border: 1px solid #d6dcd4;
    border-radius: 10px;
}
QPushButton#sidePanelToggle {
    background: #e7ebe5;
    color: #455149;
    border: 1px solid #d6dcd4;
    border-radius: 6px;
    padding: 0;
}
QPushButton#sidePanelToggle:hover {
    background: #d3dccf;
}
QScrollArea#sideScroller {
    background: transparent;
    border: 0;
}
QScrollArea#contentScroller {
    background: #f4f5f3;
    border: 0;
}
QScrollArea#previewScroller {
    background: #ffffff;
    border: 1px solid #d6dcd4;
    border-radius: 8px;
}
QLabel#previewHeader {
    font-weight: 700;
    color: #26312b;
}
QStackedWidget#sideStack, QWidget#sideContent {
    background: #ffffff;
}
QFrame#activityBar {
    background: #202723;
    border: 0;
    border-radius: 10px;
}
QPushButton#activityButton {
    background: transparent;
    color: #dfe6df;
    border: 0;
    border-radius: 8px;
    min-height: 42px;
    text-align: left;
    padding: 8px 10px;
}
QPushButton#activityButton:hover {
    background: #29332e;
}
QPushButton#activityButton:checked {
    background: #2f6f62;
    color: #ffffff;
}
QPushButton#paletteLauncher {
    background: #2a322d;
    color: #cdd6cf;
    border: 1px solid #36403a;
    border-radius: 8px;
    text-align: left;
    padding: 8px 10px;
    min-height: 36px;
    font-weight: 600;
}
QPushButton#paletteLauncher:hover {
    background: #323b35;
}
QLabel#appTitle {
    font-size: 18pt;
    font-weight: 700;
    color: #17201c;
}
QLabel#panelTitle {
    font-size: 10pt;
    font-weight: 700;
    color: #455149;
    padding-top: 12px;
}
QLabel#metricLabel {
    background: #edf1eb;
    border: 1px solid #d7ded4;
    border-radius: 4px;
    padding: 7px 9px;
    color: #26312b;
}
QLabel#guideCard {
    background: #ffffff;
    border: 1px solid #d7ded4;
    border-left: 4px solid #2f6f62;
    border-radius: 4px;
    padding: 12px 14px;
    color: #26312b;
    line-height: 145%;
}
QLabel#mutedLabel {
    color: #56635c;
    font-weight: 600;
}
QFrame#exportRow {
    background: #ffffff;
    border: 1px solid #d7ded4;
    border-left: 4px solid #2f6f62;
    border-radius: 4px;
}
QLabel#exportTitle {
    font-size: 11pt;
    font-weight: 800;
    color: #1f2522;
}
QLabel#exportDescription {
    color: #56635c;
}
QCheckBox {
    min-height: 26px;
    spacing: 8px;
}
QTableWidget {
    background: #ffffff;
    gridline-color: #d9ded7;
    border: 0;
    selection-background-color: #cfe5de;
    selection-color: #14201b;
    alternate-background-color: #f8faf7;
}
QDialog#commandPalette {
    background: #f4f5f3;
}
QDialog#changelogDialog {
    background: #f4f5f3;
}
QDialog#aboutDialog {
    background: #f4f5f3;
}
QLabel#aboutName {
    font-size: 20pt;
    font-weight: 800;
    color: #17201c;
}
QLabel#aboutVersion {
    color: #2f6f62;
    font-weight: 700;
}
QLabel#aboutTagline {
    color: #26312b;
    font-weight: 600;
}
QLabel#aboutBody {
    color: #56635c;
}
QLabel#aboutCopyright {
    color: #8a958d;
    font-size: 9pt;
}
QLabel#changelogTitle {
    font-size: 16pt;
    font-weight: 800;
    color: #17201c;
}
QScrollArea#changelogScroller {
    background: #ffffff;
    border: 1px solid #d6dcd4;
    border-radius: 10px;
}
QLabel#releaseHeading {
    font-size: 13pt;
    font-weight: 800;
    color: #1f2522;
}
QLabel#releaseTagline {
    color: #56635c;
    font-style: italic;
}
QLabel#sectionTitle {
    font-size: 11pt;
    font-weight: 800;
    color: #2f6f62;
    padding-top: 10px;
}
QLabel#changeItem {
    color: #26312b;
    line-height: 140%;
}
QLineEdit#paletteSearch {
    min-height: 38px;
    font-size: 11pt;
}
QListWidget#paletteList {
    background: #ffffff;
    border: 1px solid #d6dcd4;
    border-radius: 10px;
    padding: 6px;
    outline: 0;
}
QListWidget#paletteList::item {
    border-radius: 6px;
    padding: 10px 12px;
}
QListWidget#paletteList::item:selected {
    background: #cfe5de;
    color: #14201b;
}
QHeaderView::section {
    background: #e9eee7;
    border: 0;
    border-right: 1px solid #d2d8d0;
    border-bottom: 1px solid #c9d0c7;
    padding: 7px;
    font-weight: 700;
    color: #253029;
}
QStatusBar {
    background: #202723;
    color: #f5f7f3;
}
QLabel#versionLabel {
    color: #9fb0a6;
    font-size: 9pt;
    font-weight: 600;
    padding-right: 8px;
}
QPushButton#footerBugButton {
    background: transparent;
    border: 0;
    border-radius: 4px;
    min-height: 0;
    padding: 2px 6px;
}
QPushButton#footerBugButton:hover {
    background: #2f3a34;
}
"""

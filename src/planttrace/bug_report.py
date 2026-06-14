from __future__ import annotations

import platform

from . import __version__

REPORT_EMAIL = "yoann.dumont76@gmail.com"


def subject() -> str:
    return f"[PlantTrace v{__version__}] Rapport de bug"


def diagnostic_text(project_root: str, ocr_detected: bool, semantic: str) -> str:
    return "\n".join(
        [
            "--- Diagnostic PlantTrace (ne pas modifier) ---",
            f"Version : {__version__}",
            f"OS : {platform.platform()}",
            f"OCR Tesseract : {'detecte' if ocr_detected else 'non detecte'}",
            f"Semantique : {semantic}",
            f"Projet : {project_root}",
            "-----------------------------------------------",
        ]
    )


def report_body(diagnostic: str) -> str:
    return "\n".join(
        [
            "Decrivez le probleme (etapes, resultat attendu, resultat obtenu) :",
            "",
            "",
            "",
            diagnostic,
        ]
    )

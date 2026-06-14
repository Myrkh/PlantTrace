from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import rmtree
from zipfile import ZipFile


def is_supported() -> bool:
    """L'auto-update ne s'applique qu'a l'app packagee (frozen)."""
    return bool(getattr(sys, "frozen", False))


def install_dir() -> Path:
    return Path(sys.executable).resolve().parent


def staging_root() -> Path:
    return Path(tempfile.gettempdir()) / "PlantTrace-update"


def apply_update(asset_zip: Path) -> None:
    """Extrait le nouveau build puis lance un helper detache qui remplace l'app et la relance.

    La base d'indexation .planttrace vit dans le dossier projet, pas dans le dossier
    d'installation : elle n'est donc jamais touchee par le remplacement.
    """
    root = staging_root()
    staging = root / "new"
    if staging.exists():
        rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    with ZipFile(asset_zip) as archive:
        archive.extractall(staging)
    new_app = _locate_app_dir(staging)
    helper = _write_helper(root, os.getpid(), new_app, install_dir(), Path(sys.executable))
    subprocess.Popen(
        ["cmd", "/c", str(helper)],
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        close_fds=True,
    )


def _locate_app_dir(staging: Path) -> Path:
    """Le zip de release contient un dossier PlantTrace/ ; on le retrouve, ou la racine."""
    if (staging / "PlantTrace.exe").exists():
        return staging
    for candidate in sorted(path for path in staging.iterdir() if path.is_dir()):
        if (candidate / "PlantTrace.exe").exists():
            return candidate
    return staging


def _write_helper(root: Path, pid: int, new_app: Path, target: Path, exe: Path) -> Path:
    helper = root / "apply_update.bat"
    script = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        ":waitloop\r\n"
        f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul\r\n'
        "if not errorlevel 1 (\r\n"
        "    timeout /t 1 /nobreak >nul\r\n"
        "    goto waitloop\r\n"
        ")\r\n"
        f'robocopy "{new_app}" "{target}" /MIR /R:3 /W:1 /NFL /NDL /NJH /NJS /NC /NS >nul\r\n'
        f'start "" "{exe}"\r\n'
        '(goto) 2>nul & del "%~f0"\r\n'
    )
    helper.write_text(script, encoding="utf-8")
    return helper

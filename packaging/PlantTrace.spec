# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path


ROOT = Path(SPECPATH).parent
ICON = ROOT / "assets" / "planttrace.ico"

datas = [
    (str(ROOT / "assets" / "planttrace-logo.svg"), "assets"),
    (str(ROOT / "assets" / "planttrace.ico"), "assets"),
    (str(ROOT / "docs" / "guide.html"), "docs"),
]

excluded_optional_semantic_stack = [
    "sentence_transformers",
    "torch",
    "transformers",
    "huggingface_hub",
    "tokenizers",
    "safetensors",
]

a = Analysis(
    [str(ROOT / "packaging" / "planttrace_gui.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_optional_semantic_stack,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PlantTrace",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if ICON.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PlantTrace",
)

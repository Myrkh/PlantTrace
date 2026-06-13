from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    root = Path.cwd()
    model_path = root / ".planttrace" / "models" / "embedding-model"
    checks = {
        "python": sys.version.split()[0],
        "pymupdf": module_available("fitz"),
        "pyside6": module_available("PySide6"),
        "openpyxl": module_available("openpyxl"),
        "numpy": module_available("numpy"),
        "pytesseract_python": module_available("pytesseract"),
        "tesseract_exe": shutil.which("tesseract") or "",
        "sentence_transformers": module_available("sentence_transformers"),
        "local_embedding_model": str(model_path) if model_path.exists() else "",
    }
    print(json.dumps(checks, indent=2))
    required = ["pymupdf", "pyside6", "openpyxl", "numpy"]
    return 0 if all(checks[name] for name in required) else 1


if __name__ == "__main__":
    raise SystemExit(main())

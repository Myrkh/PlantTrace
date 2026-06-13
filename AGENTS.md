# PlantTrace - AGENTS.md

## Mission

PlantTrace is a local Windows-first desktop tool for industrial PDF cross-reference search. It is not a GED, not a chatbot, and not a generic RAG product.

## Non-negotiables

- 100% local runtime: no cloud API, no telemetry, no network calls in index/search. The only sanctioned network touchpoint is `updates.py`, an explicit user-initiated check of the latest GitHub Release (no data sent).
- Evidence first: every positive result must cite PDF path, page, excerpt, match type, and page status.
- Absence is qualified: never say a reference is absent from the project unless the indexed/OCR coverage is complete.
- Exact industrial matching beats semantic matching.
- Keep the UI simple: choose folder, index, search, inspect, export.

## Commands

```powershell
python -m pip install -e .[dev]
python -m pytest -p no:cacheprovider tests
python tools\check_environment.py
planttrace index --project . --pdf-root samples --force
planttrace search --project . --query FV1100 --mode hybrid --output results.xlsx
planttrace coverage --project .
planttrace-gui
```

Use `--ocr` only when the Windows `tesseract` executable is installed. Use `planttrace embed --project .` only when a local SentenceTransformers model exists under `.planttrace\models\embedding-model` or `PLANTTRACE_EMBED_MODEL`.

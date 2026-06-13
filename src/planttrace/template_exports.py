from __future__ import annotations

from pathlib import Path

from .export import export_csv, export_xlsx
from .templates import TagRegisterRow, TemplateRun


TAG_REGISTER_HEADERS = [
    "tag",
    "description",
    "lines",
    "documents",
    "families",
    "source_documents",
    "source_pages",
    "evidence_count",
    "conflicts",
    "revisions",
    "best_excerpt",
]


def export_template_run(run: TemplateRun, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [tag_register_to_row(row) for row in run.rows]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output, TAG_REGISTER_HEADERS, "tag_register")
    else:
        export_csv(rows, output, TAG_REGISTER_HEADERS)


def tag_register_to_row(row: TagRegisterRow) -> dict[str, object]:
    return {
        "tag": row.tag,
        "description": row.description,
        "lines": row.lines,
        "documents": row.documents,
        "families": row.families,
        "source_documents": row.source_documents,
        "source_pages": row.source_pages,
        "evidence_count": row.evidence_count,
        "conflicts": row.conflicts,
        "revisions": row.revisions,
        "best_excerpt": row.best_excerpt,
    }

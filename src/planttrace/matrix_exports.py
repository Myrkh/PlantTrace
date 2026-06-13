from __future__ import annotations

from pathlib import Path

from .export import export_csv, export_xlsx
from .project_matrix import ProjectMatrixRow


PROJECT_MATRIX_HEADERS = [
    "kind",
    "reference",
    "occurrence_count",
    "document_count",
    "family_summary",
    "pid_pfd",
    "loop",
    "datasheet",
    "terminal_jb",
    "io_plc",
    "instrument_list",
    "vendor",
    "admin_review",
    "unknown",
    "documents",
    "pages",
    "conflicts",
    "revisions",
    "best_excerpt",
]


def export_project_matrix(rows: list[ProjectMatrixRow], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = [project_matrix_to_row(row) for row in rows]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(payload, output, PROJECT_MATRIX_HEADERS, "project_matrix")
    else:
        export_csv(payload, output, PROJECT_MATRIX_HEADERS)


def project_matrix_to_row(row: ProjectMatrixRow) -> dict[str, object]:
    return {
        "kind": row.kind,
        "reference": row.reference,
        "occurrence_count": row.occurrence_count,
        "document_count": row.document_count,
        "family_summary": row.family_summary,
        "pid_pfd": row.pid_pfd,
        "loop": row.loop,
        "datasheet": row.datasheet,
        "terminal_jb": row.terminal_jb,
        "io_plc": row.io_plc,
        "instrument_list": row.instrument_list,
        "vendor": row.vendor,
        "admin_review": row.admin_review,
        "unknown": row.unknown,
        "documents": row.documents,
        "pages": row.pages,
        "conflicts": row.conflicts,
        "revisions": row.revisions,
        "best_excerpt": row.best_excerpt,
    }

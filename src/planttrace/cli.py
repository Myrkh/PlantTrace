from __future__ import annotations

import argparse
import json
from pathlib import Path

from .export import export_extraction, export_results
from .extractor import extract_references
from .indexer import index_folder
from .models import ProjectPaths
from .search import search
from .semantic import rebuild_embeddings, semantic_status
from .store import PlantTraceStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="planttrace")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index")
    index_parser.add_argument("--project", required=True, type=Path)
    index_parser.add_argument("--pdf-root", required=True, type=Path)
    index_parser.add_argument("--force", action="store_true")
    index_parser.add_argument("--ocr", action="store_true")
    index_parser.add_argument("--ocr-lang", default="eng")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--project", required=True, type=Path)
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--mode", choices=["auto", "exact", "text", "fuzzy", "semantic", "hybrid"], default="hybrid")
    search_parser.add_argument("--limit", type=int, default=50)
    search_parser.add_argument("--output", type=Path)
    search_parser.add_argument("--json", action="store_true")

    coverage_parser = subparsers.add_parser("coverage")
    coverage_parser.add_argument("--project", required=True, type=Path)

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("--project", required=True, type=Path)
    extract_parser.add_argument("--limit", type=int, default=10000)
    extract_parser.add_argument("--output", type=Path)
    extract_parser.add_argument("--json", action="store_true")

    embed_parser = subparsers.add_parser("embed")
    embed_parser.add_argument("--project", required=True, type=Path)

    semantic_parser = subparsers.add_parser("semantic-status")
    semantic_parser.add_argument("--project", required=True, type=Path)

    args = parser.parse_args(argv)
    if args.command == "index":
        report = index_folder(args.project, args.pdf_root, force=args.force, enable_ocr=args.ocr, ocr_lang=args.ocr_lang)
        print(json.dumps(report.__dict__, indent=2))
        return 0 if report.failed == 0 else 1
    if args.command == "search":
        results = search(args.project, args.query, mode=args.mode, limit=args.limit)
        if args.output:
            export_results(results, args.output)
        if args.json:
            print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))
        else:
            for result in results:
                location = f"{result.document_path} p.{result.page}" if result.document_path else "not found"
                print(f"{result.match_type} | {location} | {result.excerpt}")
        return 0 if results and results[0].match_type != "not_found_in_indexed_text" else 1
    if args.command == "coverage":
        store = PlantTraceStore(ProjectPaths(args.project.resolve()))
        print(json.dumps(store.coverage(), indent=2))
        return 0
    if args.command == "extract":
        hits = extract_references(args.project, limit=args.limit)
        if args.output:
            export_extraction(hits, args.output)
        if args.json:
            print(json.dumps([hit.__dict__ for hit in hits], ensure_ascii=False, indent=2))
        else:
            for hit in hits[: args.limit]:
                print(f"{hit.kind} | {hit.value} | {hit.document_path} p.{hit.page} | {hit.excerpt}")
        return 0
    if args.command == "embed":
        count = rebuild_embeddings(args.project)
        print(json.dumps({"embedded_chunks": count}, indent=2))
        return 0
    if args.command == "semantic-status":
        status = semantic_status(args.project)
        print(json.dumps(status.__dict__, indent=2))
        return 0 if status.available else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
from pathlib import Path

from app.services.ontology_markdown_validator import validate_markdown_ontology

# Standard validation gate for the consolidated ontology subset.
# Default target set: CONSOLIDATED-02, CONSOLIDATED-04, CONSOLIDATED-09.

DEFAULT_DOCS = [
    Path("Logi ontol core doc/CONSOLIDATED-02-warehouse-flow.md"),
    Path("Logi ontol core doc/CONSOLIDATED-04-barge-bulk-cargo.md"),
    Path("Logi ontol core doc/CONSOLIDATED-09-operations.md"),
]


def main(argv: list[str]) -> int:
    doc_paths = [Path(arg) for arg in argv] if argv else DEFAULT_DOCS

    reports = validate_markdown_ontology(doc_paths)
    all_conform = True

    for report in reports:
        status = "PASS" if report.conforms else "FAIL"
        print(f"[{status}] {report.path}")
        print(
            "  "
            f"shape_blocks={report.shape_block_count} "
            f"data_blocks={report.data_block_count} "
            f"jsonld_blocks={report.jsonld_block_count} "
            f"shape_triples={report.shape_triples} "
            f"data_triples={report.data_triples}"
        )
        if report.results_text:
            print("  results:")
            for line in report.results_text.splitlines():
                print(f"    {line}")
        all_conform = all_conform and report.conforms

    return 0 if all_conform else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

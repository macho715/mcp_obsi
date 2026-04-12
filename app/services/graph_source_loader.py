from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

REQUIRED_JPT_SHEETS = [
    "1_Decklog",
    "3_Voyage_Master",
    "4_Voyage_Rollup",
    "6_Reconciliation",
    "7_Exceptions",
    "8_Decklog_Context",
]


@dataclass(slots=True)
class LoadedGraphSources:
    shipment_rows: list[dict[str, object]]
    warehouse_rows: list[dict[str, object]]
    jpt_sheets: dict[str, list[dict[str, object]]]
    inland_cost_rows: list[dict[str, object]]
    analysis_notes: list[dict[str, object]]


def _read_markdown_note(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    frontmatter: dict[str, object] = {}

    if text.startswith("---"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[0] == "---":
            end_index = None
            for index, line in enumerate(lines[1:], start=1):
                if line == "---":
                    end_index = index
                    break
            if end_index is not None:
                raw_frontmatter = "\n".join(lines[1:end_index])
                frontmatter = yaml.safe_load(raw_frontmatter) or {}

    return {"path": str(path), "frontmatter": frontmatter, "body": text}


def load_graph_sources(
    hvdc_status_path: Path,
    warehouse_status_path: Path,
    jpt_reconciled_path: Path,
    inland_cost_path: Path,
    analyses_dir: Path,
) -> LoadedGraphSources:
    shipment_rows = pd.read_excel(hvdc_status_path).to_dict("records")
    warehouse_rows = pd.read_excel(warehouse_status_path).to_dict("records")
    jpt_excel = pd.ExcelFile(jpt_reconciled_path)
    missing_sheets = [sheet for sheet in REQUIRED_JPT_SHEETS if sheet not in jpt_excel.sheet_names]
    if missing_sheets:
        raise ValueError(f"Missing required JPT sheets: {', '.join(missing_sheets)}")

    jpt_sheets = {
        sheet: pd.read_excel(jpt_reconciled_path, sheet_name=sheet).to_dict("records")
        for sheet in REQUIRED_JPT_SHEETS
    }
    inland_cost_rows = pd.read_excel(inland_cost_path).to_dict("records")
    analysis_notes = [_read_markdown_note(path) for path in sorted(analyses_dir.glob("*.md"))]

    return LoadedGraphSources(
        shipment_rows=shipment_rows,
        warehouse_rows=warehouse_rows,
        jpt_sheets=jpt_sheets,
        inland_cost_rows=inland_cost_rows,
        analysis_notes=analysis_notes,
    )

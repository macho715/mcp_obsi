from pathlib import Path

import pandas as pd
import pytest

from app.services.graph_source_loader import load_graph_sources


def test_load_graph_sources_reads_required_tabs_and_markdown(tmp_path: Path):
    hvdc_status = tmp_path / "HVDC STATUS.xlsx"
    warehouse_status = tmp_path / "HVDC WAREHOUSE STATUS.xlsx"
    jpt = tmp_path / "JPT-reconciled_v6.0.xlsx"
    inland = tmp_path / "HVDC Logistics cost(inland,domestic).xlsx"
    analyses = tmp_path / "analyses"
    analyses.mkdir()

    pd.DataFrame([{"SCT SHIP NO.": "HVDC-001"}]).to_excel(hvdc_status, index=False)
    pd.DataFrame(
        [{"SCT SHIP NO.": "HVDC-001", "Case No.": "CASE-01"}]
    ).to_excel(warehouse_status, index=False)
    with pd.ExcelWriter(jpt) as writer:
        pd.DataFrame([{"Vessel": "JOPETWIL 71"}]).to_excel(
            writer,
            sheet_name="1_Decklog",
            index=False,
        )
        pd.DataFrame([{"Voyage No": "V001"}]).to_excel(
            writer,
            sheet_name="3_Voyage_Master",
            index=False,
        )
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(
            writer,
            sheet_name="4_Voyage_Rollup",
            index=False,
        )
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(
            writer,
            sheet_name="6_Reconciliation",
            index=False,
        )
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(
            writer,
            sheet_name="7_Exceptions",
            index=False,
        )
        pd.DataFrame([{"Normalized Invoice Number": "INV-1"}]).to_excel(
            writer,
            sheet_name="8_Decklog_Context",
            index=False,
        )
    pd.DataFrame([{"Invoice No": "INV-001", "Shipment No": "HVDC-001"}]).to_excel(
        inland,
        index=False,
    )
    (analyses / "guideline_jopetwil_71_group.md").write_text(
        "---\ntitle: Guide\nslug: guideline_jopetwil_71_group\n---\ncontent",
        encoding="utf-8",
    )

    sources = load_graph_sources(
        hvdc_status_path=hvdc_status,
        warehouse_status_path=warehouse_status,
        jpt_reconciled_path=jpt,
        inland_cost_path=inland,
        analyses_dir=analyses,
    )

    assert len(sources.shipment_rows) == 1
    assert len(sources.warehouse_rows) == 1
    assert "1_Decklog" in sources.jpt_sheets
    assert len(sources.analysis_notes) == 1


def test_load_graph_sources_raises_for_missing_required_jpt_sheets(tmp_path: Path):
    hvdc_status = tmp_path / "HVDC STATUS.xlsx"
    warehouse_status = tmp_path / "HVDC WAREHOUSE STATUS.xlsx"
    jpt = tmp_path / "JPT-reconciled_v6.0.xlsx"
    inland = tmp_path / "HVDC Logistics cost(inland,domestic).xlsx"
    analyses = tmp_path / "analyses"
    analyses.mkdir()

    pd.DataFrame([{"SCT SHIP NO.": "HVDC-001"}]).to_excel(hvdc_status, index=False)
    pd.DataFrame(
        [{"SCT SHIP NO.": "HVDC-001", "Case No.": "CASE-01"}]
    ).to_excel(warehouse_status, index=False)
    with pd.ExcelWriter(jpt) as writer:
        pd.DataFrame([{"Vessel": "JOPETWIL 71"}]).to_excel(
            writer,
            sheet_name="1_Decklog",
            index=False,
        )
        pd.DataFrame([{"Voyage No": "V001"}]).to_excel(
            writer,
            sheet_name="3_Voyage_Master",
            index=False,
        )
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(
            writer,
            sheet_name="4_Voyage_Rollup",
            index=False,
        )
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(
            writer,
            sheet_name="6_Reconciliation",
            index=False,
        )
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(
            writer,
            sheet_name="8_Decklog_Context",
            index=False,
        )
    pd.DataFrame([{"Invoice No": "INV-001", "Shipment No": "HVDC-001"}]).to_excel(
        inland,
        index=False,
    )

    with pytest.raises(ValueError, match="Missing required JPT sheets: 7_Exceptions"):
        load_graph_sources(
            hvdc_status_path=hvdc_status,
            warehouse_status_path=warehouse_status,
            jpt_reconciled_path=jpt,
            inland_cost_path=inland,
            analyses_dir=analyses,
        )

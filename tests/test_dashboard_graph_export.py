import json
from pathlib import Path

import pandas as pd

from app.services.graph_projection_builder import build_dashboard_projection
from scripts.build_dashboard_graph_data import export_dashboard_graph_data


def test_build_dashboard_projection_emits_flat_consumer_contract():
    shipment_id = "https://hvdc.logistics/resource/shipment/HVDC-001"
    event_id = "https://hvdc.logistics/resource/arrival/HVDC-001/agi/2026-04-01"
    location_id = "https://hvdc.logistics/resource/site/agi"
    lesson_id = "https://hvdc.logistics/resource/lesson/HVDC-001/lesson-1"

    nodes, edges, audits = build_dashboard_projection(
        shipments=[
            {
                "id": shipment_id,
                "label": "HVDC-001",
                "type": "Shipment",
            }
        ],
        events=[
            {
                "id": event_id,
                "label": "AGI",
                "type": "ArrivalEvent",
                "subject_id": shipment_id,
                "location_id": location_id,
            }
        ],
        lessons=[
            {
                "id": lesson_id,
                "label": "Delay at AGI",
                "type": "IncidentLesson",
                "shipment_id": shipment_id,
                "location_id": location_id,
            }
        ],
    )

    node_by_id = {node["data"]["id"]: node["data"] for node in nodes}
    edge_keys = {
        (edge["data"]["source"], edge["data"]["target"], edge["data"]["label"]) for edge in edges
    }

    assert shipment_id in node_by_id
    assert node_by_id[shipment_id]["type"] == "Shipment"
    assert location_id in node_by_id
    assert node_by_id[location_id]["type"] == "SiteLocation"
    assert (shipment_id, location_id, "occurredAt") in edge_keys
    assert (shipment_id, lesson_id, "relatedToLesson") in edge_keys
    assert audits["projection"]["unknown_nodes"] == 0


def test_export_dashboard_graph_data_emits_consumer_contract(tmp_path: Path):
    excel_path = tmp_path / "hvdc_status.xlsx"
    wiki_dir = tmp_path / "wiki" / "analyses"
    wiki_dir.mkdir(parents=True)
    output_dir = tmp_path / "out"

    df = pd.DataFrame(
        [
            {
                "SCT SHIP NO.": "SHIP-001",
                "PO No.": "PO-001",
                "VENDOR": "Vendor A",
                "VESSEL NAME/ FLIGHT No.": "Vessel A",
                "MOSB": "2026-04-01",
                "DSV Indoor": "2026-04-02",
                "AGI": "2026-04-03",
            }
        ]
    )
    df.to_excel(excel_path, index=False)

    (wiki_dir / "delay-a.md").write_text(
        """---
title: Delay at AGI
slug: delay-at-agi
tags:
  - agi
  - mosb
---
Issue body
""",
        encoding="utf-8",
    )
    (wiki_dir / "logistics_issue_delay_at_agi.md").write_text(
        """---
title: Delay at AGI
slug: delay-at-agi
tags:
  - agi
---
Issue body
""",
        encoding="utf-8",
    )

    export_dashboard_graph_data(
        excel_path=excel_path,
        wiki_dir=wiki_dir,
        output_dir=output_dir,
    )

    nodes_path = output_dir / "nodes.json"
    edges_path = output_dir / "edges.json"
    nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
    edges = json.loads(edges_path.read_text(encoding="utf-8"))

    export_dashboard_graph_data(
        excel_path=excel_path,
        wiki_dir=wiki_dir,
        output_dir=output_dir,
    )
    assert json.loads(nodes_path.read_text(encoding="utf-8")) == nodes
    assert json.loads(edges_path.read_text(encoding="utf-8")) == edges

    assert nodes
    assert edges
    assert all("data" in node for node in nodes)
    required_node_keys = {"id", "label", "type", "rdf-schema#label"}
    required_edge_keys = {"id", "source", "target", "label"}
    assert all(required_node_keys <= set(node["data"].keys()) for node in nodes)
    assert all("data" in edge for edge in edges)
    assert all(required_edge_keys <= set(edge["data"].keys()) for edge in edges)

    node_ids = {node["data"]["id"] for node in nodes}
    assert all(edge["data"]["source"] in node_ids for edge in edges)
    assert all(edge["data"]["target"] in node_ids for edge in edges)
    assert [node["data"]["id"] for node in nodes] == [
        node["data"]["id"]
        for node in sorted(
            nodes,
            key=lambda node: (node["data"]["type"], node["data"]["label"], node["data"]["id"]),
        )
    ]
    assert [edge["data"]["id"] for edge in edges] == [
        edge["data"]["id"]
        for edge in sorted(
            edges,
            key=lambda edge: (
                edge["data"]["source"],
                edge["data"]["target"],
                edge["data"]["label"],
            ),
        )
    ]

    issue_nodes = [node for node in nodes if node["data"]["type"] == "LogisticsIssue"]
    assert len(issue_nodes) == 1
    assert issue_nodes[0]["data"]["label"] == "Delay at AGI"
    assert all(node["data"]["type"] != "rdf-schema#Class" for node in nodes)
    assert all(node["data"]["type"] != "Unknown" for node in nodes)

    node_ids = {node["data"]["id"] for node in nodes}
    shipment_legacy_id = "http://hvdc.logistics/ontology/shipment/SHIP-001"
    shipment_canonical_id = "https://hvdc.logistics/resource/shipment/SHIP-001"
    location_legacy_id = "http://hvdc.logistics/ontology/site/AGI"
    location_canonical_id = "https://hvdc.logistics/resource/site/agi"
    lesson_id = "http://hvdc.logistics/ontology/lesson/delay-at-agi"

    assert shipment_legacy_id in node_ids
    assert shipment_canonical_id not in node_ids
    assert location_legacy_id in node_ids
    assert location_canonical_id not in node_ids
    assert sum(
        1
        for node in nodes
        if node["data"]["type"] == "Shipment" and node["data"]["label"] == "SHIP-001"
    ) == 1
    assert (location_legacy_id, lesson_id, "relatedToLesson") in {
        (edge["data"]["source"], edge["data"]["target"], edge["data"]["label"]) for edge in edges
    }


def test_export_dashboard_graph_data_keeps_legacy_id_style_for_values_with_spaces_and_slashes(
    tmp_path: Path,
):
    excel_path = tmp_path / "hvdc_status.xlsx"
    wiki_dir = tmp_path / "wiki" / "analyses"
    wiki_dir.mkdir(parents=True)
    output_dir = tmp_path / "out"

    df = pd.DataFrame(
        [
            {
                "SCT SHIP NO.": "SHIP 002",
                "PO No.": "PO 002",
                "VENDOR": "BMT Co., Ltd",
                "VESSEL NAME/ FLIGHT No.": "EK0118 / EK09113",
            }
        ]
    )
    df.to_excel(excel_path, index=False)

    export_dashboard_graph_data(
        excel_path=excel_path,
        wiki_dir=wiki_dir,
        output_dir=output_dir,
    )

    nodes = json.loads((output_dir / "nodes.json").read_text(encoding="utf-8"))
    edges = json.loads((output_dir / "edges.json").read_text(encoding="utf-8"))
    node_ids = {node["data"]["id"] for node in nodes}
    required_edge_keys = {"id", "source", "target", "label"}
    assert all(required_edge_keys <= set(edge["data"].keys()) for edge in edges)
    assert all(edge["data"]["source"] in node_ids for edge in edges)
    assert all(edge["data"]["target"] in node_ids for edge in edges)

    assert "http://hvdc.logistics/ontology/vendor/BMT_Co.,_Ltd" in node_ids
    assert "http://hvdc.logistics/ontology/vessel/EK0118_/_EK09113" in node_ids

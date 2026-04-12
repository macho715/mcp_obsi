from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from rdflib import Graph, Namespace, URIRef

from app.services.graph_canonical_builder import build_canonical_graph
from app.services.graph_knowledge_builder import build_knowledge_objects
from app.services.graph_mapping_builder import build_compatibility_mappings
from app.services.graph_normalizer import normalize_sources
from app.services.graph_projection_builder import build_dashboard_projection
from app.services.graph_resolver import resolve_analysis_note, resolve_location
from app.services.graph_source_loader import LoadedGraphSources, load_graph_sources

HVDC_BASE = "http://hvdc.logistics/ontology/"
HVDC = Namespace(HVDC_BASE)

DEFAULT_EXCEL_PATH = Path("Logi ontol core doc/HVDC STATUS.xlsx")
DEFAULT_WAREHOUSE_STATUS_PATH = Path("Logi ontol core doc/HVDC WAREHOUSE STATUS.xlsx")
DEFAULT_JPT_RECONCILED_PATH = Path("Logi ontol core doc/JPT-reconciled_v6.0.xlsx")
DEFAULT_INLAND_COST_PATH = Path("Logi ontol core doc/HVDC Logistics cost(inland,domestic).xlsx")
DEFAULT_WIKI_DIR = Path("vault/wiki/analyses")
DEFAULT_OUTPUT_DIR = Path("kg-dashboard/public/data")
DEFAULT_TTL_PATH = Path("vault/knowledge_graph.ttl")
DEFAULT_AUDIT_DIR = Path("runtime/audits")

REQUIRED_EXCEL_COLUMNS = [
    "SCT SHIP NO.",
    "PO No.",
    "VENDOR",
    "VESSEL NAME/ FLIGHT No.",
]

WAREHOUSE_COLUMNS = [
    "DSV Indoor",
    "DSV Outdoor",
    "DSV MZD",
    "DSV Kizad",
    "JDN MZD",
    "JDN Waterfront",
    "AAA Storage",
    "ZENER (WH)",
    "Hauler DG Storage",
    "Vijay Tanks",
]

SITE_COLUMNS = ["SHU", "MIR", "DAS", "AGI"]


def normalize_fragment(value: str) -> str:
    return re.sub(r"\s+", "_", value.strip())


def node_uri(kind: str, value: str) -> str:
    return str(URIRef(HVDC[f"{kind}/{normalize_fragment(value)}"]))


def _safe_uri(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.replace(" ", "_")


def _legacy_dashboard_id(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.startswith("http://hvdc.logistics/ontology/"):
        return text

    for prefix in (
        "https://hvdc.logistics/resource/",
        "http://hvdc.logistics/resource/",
    ):
        if not text.startswith(prefix):
            continue
        parts = text.rstrip("/").split("/")
        if len(parts) < 2:
            return text
        kind = parts[-2]
        value_text = parts[-1]
        if kind in {"site", "hub"}:
            value_text = value_text.upper()
        if kind in {"shipment", "site", "hub", "carrier", "pattern"}:
            return node_uri(kind, value_text)
        return text

    return text


def _is_present(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"nan", "none"}


def _read_frontmatter(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    frontmatter = yaml.safe_load(parts[1]) or {}
    return frontmatter if isinstance(frontmatter, dict) else {}


def _read_analysis_notes(analyses_dir: Path) -> list[dict[str, Any]]:
    if not analyses_dir.exists():
        return []

    notes: list[dict[str, Any]] = []
    for path in sorted(analyses_dir.glob("*.md")):
        notes.append(
            {
                "path": str(path),
                "frontmatter": _read_frontmatter(path),
                "body": path.read_text(encoding="utf-8"),
            }
        )
    return notes


def _required_columns(df: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_EXCEL_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required Excel columns: {', '.join(missing)}")


def _legacy_tag_targets(tag: str) -> tuple[str, str, str] | None:
    lowered = tag.strip().lower()
    if lowered in {"shu", "mir", "das", "agi"}:
        return ("site", lowered.upper(), "occursAt")
    if lowered == "jpt71":
        return ("vessel", "JPT71", "relatedTo")
    if lowered in {"abu_dhabi", "mosb"}:
        return ("hub", "MOSB", "occursAt")
    if lowered == "dsv":
        return ("warehouse", "DSV Indoor", "occursAt")
    return None


def _resolved_operational_anchor(tag: str) -> tuple[str, str, str] | None:
    decision = resolve_location(tag)
    if decision.status == "resolved" and decision.target_id:
        return ("uri", decision.target_id, "occursAt")
    legacy = _legacy_tag_targets(tag)
    if legacy is not None:
        return legacy
    return None


def _read_shipment_rows(excel_path: Path) -> list[dict[str, Any]]:
    df = pd.read_excel(excel_path)
    _required_columns(df)
    return df.to_dict("records")


def _load_sources_bundle(
    excel_path: Path,
    warehouse_status_path: Path,
    jpt_reconciled_path: Path,
    inland_cost_path: Path,
    analyses_dir: Path,
) -> LoadedGraphSources:
    source_paths = (
        excel_path,
        warehouse_status_path,
        jpt_reconciled_path,
        inland_cost_path,
    )
    if all(path.exists() for path in source_paths):
        return load_graph_sources(
            excel_path,
            warehouse_status_path,
            jpt_reconciled_path,
            inland_cost_path,
            analyses_dir,
        )

    shipment_rows = _read_shipment_rows(excel_path)
    warehouse_rows = (
        pd.read_excel(warehouse_status_path).to_dict("records")
        if warehouse_status_path.exists()
        else []
    )
    inland_cost_rows = (
        pd.read_excel(inland_cost_path).to_dict("records") if inland_cost_path.exists() else []
    )
    return LoadedGraphSources(
        shipment_rows=shipment_rows,
        warehouse_rows=warehouse_rows,
        jpt_sheets={},
        inland_cost_rows=inland_cost_rows,
        analysis_notes=_read_analysis_notes(analyses_dir),
    )


def _build_legacy_shipment_projection(
    shipment_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}

    for row in shipment_rows:
        ship_no = str(row.get("SCT SHIP NO.", "")).strip()
        if not _is_present(ship_no):
            continue

        shipment_id = node_uri("shipment", ship_no)
        nodes[shipment_id] = {
            "data": {
                "id": shipment_id,
                "label": ship_no,
                "type": "Shipment",
                "rdf-schema#label": ship_no,
            }
        }

        po_no = str(row.get("PO No.", "")).strip()
        if _is_present(po_no):
            order_id = node_uri("order", po_no)
            nodes[order_id] = {
                "data": {
                    "id": order_id,
                    "label": po_no,
                    "type": "Order",
                    "rdf-schema#label": po_no,
                }
            }
            edges[(shipment_id, order_id, "hasOrder")] = {
                "data": {
                    "id": f"{shipment_id}|hasOrder|{order_id}",
                    "source": shipment_id,
                    "target": order_id,
                    "label": "hasOrder",
                }
            }

        vendor = str(row.get("VENDOR", "")).strip()
        if _is_present(vendor):
            vendor_id = node_uri("vendor", vendor)
            nodes[vendor_id] = {
                "data": {
                    "id": vendor_id,
                    "label": vendor,
                    "type": "Vendor",
                    "rdf-schema#label": vendor,
                }
            }
            edges[(shipment_id, vendor_id, "suppliedBy")] = {
                "data": {
                    "id": f"{shipment_id}|suppliedBy|{vendor_id}",
                    "source": shipment_id,
                    "target": vendor_id,
                    "label": "suppliedBy",
                }
            }

        vessel = str(row.get("VESSEL NAME/ FLIGHT No.", "")).strip()
        if _is_present(vessel):
            vessel_id = node_uri("vessel", vessel)
            nodes[vessel_id] = {
                "data": {
                    "id": vessel_id,
                    "label": vessel,
                    "type": "Vessel",
                    "rdf-schema#label": vessel,
                }
            }
            edges[(shipment_id, vessel_id, "transportedBy")] = {
                "data": {
                    "id": f"{shipment_id}|transportedBy|{vessel_id}",
                    "source": shipment_id,
                    "target": vessel_id,
                    "label": "transportedBy",
                }
            }

        mosb = str(row.get("MOSB", "")).strip()
        if _is_present(mosb):
            hub_id = node_uri("hub", "MOSB")
            nodes[hub_id] = {
                "data": {
                    "id": hub_id,
                    "label": "MOSB",
                    "type": "Hub",
                    "rdf-schema#label": "MOSB",
                }
            }
            edges[(shipment_id, hub_id, "consolidatedAt")] = {
                "data": {
                    "id": f"{shipment_id}|consolidatedAt|{hub_id}",
                    "source": shipment_id,
                    "target": hub_id,
                    "label": "consolidatedAt",
                }
            }

        for warehouse in WAREHOUSE_COLUMNS:
            if warehouse not in row or not _is_present(row.get(warehouse)):
                continue
            warehouse_id = node_uri("warehouse", warehouse)
            nodes[warehouse_id] = {
                "data": {
                    "id": warehouse_id,
                    "label": warehouse,
                    "type": "Warehouse",
                    "rdf-schema#label": warehouse,
                }
            }
            edges[(shipment_id, warehouse_id, "storedAt")] = {
                "data": {
                    "id": f"{shipment_id}|storedAt|{warehouse_id}",
                    "source": shipment_id,
                    "target": warehouse_id,
                    "label": "storedAt",
                }
            }

        for site in SITE_COLUMNS:
            if site not in row or not _is_present(row.get(site)):
                continue
            site_id = node_uri("site", site)
            nodes[site_id] = {
                "data": {
                    "id": site_id,
                    "label": site,
                    "type": "Site",
                    "rdf-schema#label": site,
                }
            }
            edges[(shipment_id, site_id, "deliveredTo")] = {
                "data": {
                    "id": f"{shipment_id}|deliveredTo|{site_id}",
                    "source": shipment_id,
                    "target": site_id,
                    "label": "deliveredTo",
                }
            }

    return list(nodes.values()), list(edges.values())


def _issue_projection_targets(tag: str) -> tuple[str, str, str] | None:
    target = _resolved_operational_anchor(tag)
    if target is None:
        return None
    if target[0] == "uri":
        return target
    return target


def _build_issue_projection(
    notes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    unresolved: list[str] = []

    for note in notes:
        frontmatter = note.get("frontmatter")
        if not isinstance(frontmatter, dict):
            continue

        title = str(frontmatter.get("title", "")).strip()
        slug = str(frontmatter.get("slug", "")).strip()
        if not title or not slug:
            continue

        issue_id = node_uri("issue", slug)
        nodes[issue_id] = {
            "data": {
                "id": issue_id,
                "label": title,
                "type": "LogisticsIssue",
                "rdf-schema#label": title,
            }
        }

        raw_tags = frontmatter.get("tags", [])
        if isinstance(raw_tags, str):
            tags = [raw_tags]
        else:
            tags = [str(tag) for tag in raw_tags]

        projected = False
        for tag in tags:
            target = _issue_projection_targets(tag)
            if not target:
                continue
            kind, label, edge_label = target
            if kind == "uri":
                target_id = label
                target_label = label.rstrip("/").split("/")[-1]
                target_type = "Location"
            else:
                target_id = node_uri(kind, label)
                target_type = kind.capitalize() if kind != "hub" else "Hub"
                target_label = label
            nodes[target_id] = {
                "data": {
                    "id": target_id,
                    "label": target_label,
                    "type": target_type,
                    "rdf-schema#label": target_label,
                }
            }
            edges[(issue_id, target_id, edge_label)] = {
                "data": {
                    "id": f"{issue_id}|{edge_label}|{target_id}",
                    "source": issue_id,
                    "target": target_id,
                    "label": edge_label,
                }
            }
            projected = True

        if not projected:
            unresolved.append(slug)

    return list(nodes.values()), list(edges.values()), unresolved


def _notes_to_canonical_lessons(
    notes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    lessons: list[dict[str, Any]] = []
    unmapped: list[str] = []

    for note in notes:
        frontmatter = note.get("frontmatter")
        if not isinstance(frontmatter, dict):
            continue

        slug = str(frontmatter.get("slug", "")).strip()
        title = str(frontmatter.get("title", "")).strip() or slug
        if not slug:
            continue

        note_kind = resolve_analysis_note(note).get("class_name")
        if note_kind != "IncidentLesson":
            continue

        anchor_id: str | None = None
        raw_tags = frontmatter.get("tags", [])
        tags = [raw_tags] if isinstance(raw_tags, str) else list(raw_tags or [])
        for tag in tags:
            if not isinstance(tag, str):
                continue
            target = _issue_projection_targets(tag)
            if target is None:
                continue
            kind, label, _edge_label = target
            if kind == "uri":
                anchor_id = label
            else:
                anchor_id = node_uri(kind, label)
            break

        if anchor_id is None:
            unmapped.append(slug)
            continue

        lesson_record: dict[str, Any] = {
            "id": node_uri("lesson", slug),
            "label": title,
            "type": "IncidentLesson",
        }
        if "/shipment/" in anchor_id:
            lesson_record["shipment_id"] = anchor_id
        elif "/carrier/" in anchor_id:
            lesson_record["carrier_id"] = anchor_id
        elif "/pattern/" in anchor_id:
            lesson_record["pattern_id"] = anchor_id
        else:
            lesson_record["location_id"] = anchor_id
        lessons.append(lesson_record)

    return lessons, unmapped


def _emit_ttl(graph: Graph, ttl_path: Path) -> None:
    ttl_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=ttl_path, format="turtle")


def _emit_json(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "nodes.json").write_text(
        json.dumps(nodes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "edges.json").write_text(
        json.dumps(edges, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _emit_audit_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_for_projection(
    normalized: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    shipments = [
        {
            "id": _legacy_dashboard_id(shipment.id),
            "label": shipment.shipment_no,
            "type": "Shipment",
        }
        for shipment in normalized.shipments
    ]
    events = [
        {
            "subject_id": _legacy_dashboard_id(event.subject_id),
            "location_id": _legacy_dashboard_id(event.location_id),
            "location_label": (
                event.location_id.rstrip("/").split("/")[-1].upper() if event.location_id else None
            ),
        }
        for event in normalized.route_events
        if event.location_id
    ]
    return shipments, events, []


def _merge_payloads(*payload_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for payload_group in payload_groups:
        for payload in payload_group:
            data = payload.get("data", {})
            node_id = data.get("id")
            if not node_id:
                continue
            existing = merged.get(node_id)
            if existing is None:
                merged[node_id] = payload
                continue
            existing["data"].update(
                {key: value for key, value in data.items() if value is not None}
            )
    return sorted(
        merged.values(),
        key=lambda item: (
            item["data"]["type"],
            item["data"]["label"],
            item["data"]["id"],
        ),
    )


def _merge_edges(*payload_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for payload_group in payload_groups:
        for payload in payload_group:
            data = payload.get("data", {})
            edge_id = data.get("id")
            if not edge_id:
                continue
            merged[edge_id] = payload
    return sorted(
        merged.values(),
        key=lambda item: (
            item["data"]["source"],
            item["data"]["target"],
            item["data"]["label"],
        ),
    )


def export_dashboard_graph_data(
    excel_path: Path = DEFAULT_EXCEL_PATH,
    wiki_dir: Path = DEFAULT_WIKI_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    ttl_path: Path | None = DEFAULT_TTL_PATH,
    warehouse_status_path: Path | None = None,
    jpt_reconciled_path: Path | None = None,
    inland_cost_path: Path | None = None,
    audit_dir: Path = DEFAULT_AUDIT_DIR,
) -> None:
    base_dir = excel_path.parent
    warehouse_status_path = warehouse_status_path or base_dir / DEFAULT_WAREHOUSE_STATUS_PATH.name
    jpt_reconciled_path = jpt_reconciled_path or base_dir / DEFAULT_JPT_RECONCILED_PATH.name
    inland_cost_path = inland_cost_path or base_dir / DEFAULT_INLAND_COST_PATH.name

    sources = _load_sources_bundle(
        excel_path=excel_path,
        warehouse_status_path=warehouse_status_path,
        jpt_reconciled_path=jpt_reconciled_path,
        inland_cost_path=inland_cost_path,
        analyses_dir=wiki_dir,
    )
    normalized = normalize_sources(
        {
            "shipment_rows": sources.shipment_rows,
            "warehouse_rows": sources.warehouse_rows,
            "jpt_sheets": sources.jpt_sheets,
            "inland_cost_rows": sources.inland_cost_rows,
            "analysis_notes": sources.analysis_notes,
        }
    )
    knowledge = build_knowledge_objects(sources.analysis_notes)
    canonical_lessons, unmapped_lessons = _notes_to_canonical_lessons(sources.analysis_notes)
    compatibility_mappings = build_compatibility_mappings()
    dashboard_lessons = [
        {
            **lesson,
            "id": _safe_uri(lesson.get("id")),
            "shipment_id": _legacy_dashboard_id(_safe_uri(lesson.get("shipment_id"))),
            "location_id": _legacy_dashboard_id(_safe_uri(lesson.get("location_id"))),
            "carrier_id": _legacy_dashboard_id(_safe_uri(lesson.get("carrier_id"))),
            "pattern_id": _legacy_dashboard_id(_safe_uri(lesson.get("pattern_id"))),
        }
        for lesson in canonical_lessons
    ]

    canonical_graph = build_canonical_graph(
        shipments=[
            {
                "id": _safe_uri(shipment.id),
                "shipment_no": shipment.shipment_no,
                "vendor_name": shipment.vendor_name,
            }
            for shipment in normalized.shipments
        ],
        cases=[
            {
                "id": _safe_uri(case.id),
                "shipment_id": _safe_uri(case.shipment_id),
                "case_no": case.case_no,
            }
            for case in normalized.cases
        ],
        events=[
            {
                "id": _safe_uri(event.id),
                "event_type": event.event_type,
                "subject_id": _safe_uri(event.subject_id),
                "location_id": _safe_uri(event.location_id),
                "event_date": event.event_date,
            }
            for event in normalized.route_events
        ],
        lessons=[
            {
                **lesson,
                "id": _safe_uri(lesson.get("id")),
                "shipment_id": _safe_uri(lesson.get("shipment_id")),
                "location_id": _safe_uri(lesson.get("location_id")),
                "carrier_id": _safe_uri(lesson.get("carrier_id")),
                "pattern_id": _safe_uri(lesson.get("pattern_id")),
            }
            for lesson in canonical_lessons
        ],
    )
    for triple in compatibility_mappings:
        canonical_graph.add(triple)

    if ttl_path is not None:
        _emit_ttl(canonical_graph, ttl_path)

    dashboard_shipments, dashboard_events, _ = _normalize_for_projection(normalized)
    projected_nodes, projected_edges, projection_audit = build_dashboard_projection(
        shipments=dashboard_shipments,
        events=dashboard_events,
        lessons=dashboard_lessons,
    )
    legacy_nodes, legacy_edges = _build_legacy_shipment_projection(sources.shipment_rows)
    issue_nodes, issue_edges, unresolved_issue_notes = _build_issue_projection(
        sources.analysis_notes
    )

    nodes = _merge_payloads(projected_nodes, legacy_nodes, issue_nodes)
    edges = _merge_edges(projected_edges, legacy_edges, issue_edges)
    _emit_json(nodes, edges, output_dir)

    dropped_rows = [
        index
        for index, row in enumerate(sources.shipment_rows)
        if not _is_present(row.get("SCT SHIP NO."))
    ]
    unresolved_attribution = []
    for row in sources.inland_cost_rows:
        if not _is_present(row.get("Shipment No")):
            unresolved_attribution.append(str(row))

    source_audit = {
        "dropped_rows": dropped_rows,
        "loaded_shipments": len(sources.shipment_rows),
        "loaded_notes": len(sources.analysis_notes),
    }
    resolution_audit = {
        "unresolved_attribution": unresolved_attribution,
        "weak_cost_attribution_confidence": [],
    }
    mapping_audit = {
        "unmapped_lessons": sorted(set(unmapped_lessons + unresolved_issue_notes)),
        "unresolved_compatibility_mappings": [],
        "knowledge_counts": {
            "guides": len(knowledge.guides),
            "rules": len(knowledge.rules),
            "lessons": len(knowledge.lessons),
            "evidence": len(knowledge.evidence),
            "patterns": len(knowledge.patterns),
        },
    }

    _emit_audit_json(audit_dir / "hvdc_ttl_source_audit.json", source_audit)
    _emit_audit_json(audit_dir / "hvdc_ttl_resolution_audit.json", resolution_audit)
    _emit_audit_json(
        audit_dir / "hvdc_ttl_projection_audit.json",
        projection_audit,
    )
    _emit_audit_json(audit_dir / "hvdc_ttl_mapping_audit.json", mapping_audit)


if __name__ == "__main__":
    export_dashboard_graph_data()

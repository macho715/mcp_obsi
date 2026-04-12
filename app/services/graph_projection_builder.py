from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _pick_text(item: Mapping[str, Any] | Any, *keys: str) -> str | None:
    for key in keys:
        if isinstance(item, Mapping) and key in item:
            value = item.get(key)
        else:
            value = getattr(item, key, None)
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in {"nan", "none"}:
            return text
    return None


def _tail(value: str | None) -> str:
    if not value:
        return ""
    return value.rstrip("/").split("/")[-1]


def _node_payload(
    node_id: str,
    label: str,
    type_name: str,
    **extra: Any,
) -> dict[str, Any]:
    data = {
        "id": node_id,
        "label": label,
        "type": type_name,
        "rdf-schema#label": label,
    }
    data.update(extra)
    return {"data": data}


def _edge_payload(source: str, target: str, label: str) -> dict[str, Any]:
    return {
        "data": {
            "id": f"{source}|{label}|{target}",
            "source": source,
            "target": target,
            "label": label,
        }
    }


def _upsert_node(
    nodes: dict[str, dict[str, Any]],
    node_id: str,
    label: str,
    type_name: str,
    **extra: Any,
) -> None:
    payload = _node_payload(node_id, label, type_name, **extra)
    existing = nodes.get(node_id)
    if existing is None:
        nodes[node_id] = payload
        return

    existing_data = existing["data"]
    existing_data.update({key: value for key, value in extra.items() if value is not None})
    if not existing_data.get("label") and label:
        existing_data["label"] = label
    if not existing_data.get("rdf-schema#label") and label:
        existing_data["rdf-schema#label"] = label


def _upsert_edge(
    edges: dict[tuple[str, str, str], dict[str, Any]],
    source: str,
    target: str,
    label: str,
) -> None:
    edges[(source, target, label)] = _edge_payload(source, target, label)


def _coerce_text(record: Mapping[str, Any] | Any, *keys: str) -> str | None:
    return _pick_text(record, *keys)


def build_dashboard_projection(*, shipments, events, lessons):
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    unknown_nodes = 0

    for shipment in shipments or []:
        shipment_id = _coerce_text(shipment, "id")
        shipment_label = _coerce_text(shipment, "label", "shipment_no", "shipmentNo")
        shipment_type = _coerce_text(shipment, "type") or "Shipment"
        if not shipment_id or not shipment_label:
            unknown_nodes += 1
            continue
        _upsert_node(
            nodes,
            shipment_id,
            shipment_label,
            shipment_type,
            countryOfExport=_coerce_text(shipment, "country_of_export", "countryOfExport"),
            portOfLoading=_coerce_text(shipment, "port_of_loading", "portOfLoading"),
            portOfDischarge=_coerce_text(shipment, "port_of_discharge", "portOfDischarge"),
            shipMode=_coerce_text(shipment, "ship_mode", "shipMode"),
            actualDeparture=_coerce_text(shipment, "actual_departure", "actualDeparture"),
            actualArrival=_coerce_text(shipment, "actual_arrival", "actualArrival"),
        )

    for event in events or []:
        subject_id = _coerce_text(event, "subject_id", "subjectId", "shipment_id", "shipmentId")
        location_id = _coerce_text(event, "location_id", "locationId")
        if not subject_id or not location_id:
            unknown_nodes += 1
            continue

        location_label = _coerce_text(
            event,
            "location_label",
            "locationName",
            "label",
            "name",
        )
        if not location_label:
            location_label = _tail(location_id) or location_id
        location_type = _coerce_text(event, "location_type", "locationType") or "SiteLocation"

        _upsert_node(nodes, location_id, location_label, location_type)
        _upsert_edge(edges, subject_id, location_id, "occurredAt")

    for lesson in lessons or []:
        lesson_id = _coerce_text(lesson, "id")
        lesson_label = _coerce_text(lesson, "label", "title", "slug")
        lesson_type = _coerce_text(lesson, "type") or "IncidentLesson"
        anchor_id = None
        for anchor_key in (
            "shipment_id",
            "location_id",
            "carrier_id",
            "pattern_id",
            "shipmentId",
            "locationId",
            "carrierId",
            "patternId",
        ):
            anchor_id = _coerce_text(lesson, anchor_key)
            if anchor_id:
                break
        if not lesson_id or not lesson_label or not anchor_id:
            unknown_nodes += 1
            continue

        _upsert_node(
            nodes,
            lesson_id,
            lesson_label,
            lesson_type,
            analysisPath=_coerce_text(lesson, "analysisPath"),
            analysisVault=_coerce_text(lesson, "analysisVault"),
        )
        _upsert_edge(edges, anchor_id, lesson_id, "relatedToLesson")

    node_payload = sorted(
        nodes.values(),
        key=lambda item: (
            item["data"]["type"],
            item["data"]["label"],
            item["data"]["id"],
        ),
    )
    edge_payload = sorted(
        edges.values(),
        key=lambda item: (
            item["data"]["source"],
            item["data"]["target"],
            item["data"]["label"],
        ),
    )

    return node_payload, edge_payload, {"projection": {"unknown_nodes": unknown_nodes}}

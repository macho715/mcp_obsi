from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

HVDC = Namespace("http://hvdc.logistics/ontology/")
HVDCE = Namespace("http://hvdc.logistics/ontology/event/")
HVDCK = Namespace("http://hvdc.logistics/ontology/knowledge/")
HVDCM = Namespace("http://hvdc.logistics/ontology/mapping/")

_TYPE_BY_BUCKET = {
    "shipments": HVDC.Shipment,
    "cases": HVDC.Case,
    "cargo_items": HVDC.CargoItem,
    "document_refs": HVDC.DocumentRef,
    "status_snapshots": HVDC.StatusSnapshot,
    "events": HVDC.Event,
    "invoices": HVDC.Invoice,
    "charge_summaries": HVDC.ChargeSummary,
    "settlement_records": HVDC.SettlementRecord,
    "reconciliation_records": HVDC.ReconciliationRecord,
    "cost_attributions": HVDC.CostAttribution,
    "guides": HVDC.Guide,
    "rules": HVDC.Rule,
    "lessons": HVDC.Lesson,
    "patterns": HVDC.Pattern,
    "evidence": HVDC.Evidence,
    "mappings": HVDC.Mapping,
}


def _coerce_sources(
    args: tuple[object, ...],
    kwargs: dict[str, Any],
) -> dict[str, Iterable[Mapping[str, Any]]]:
    if args:
        if len(args) != 1 or not isinstance(args[0], Mapping):
            raise TypeError(
                "build_canonical_graph accepts either a single mapping or keyword buckets"
            )
        sources = dict(args[0])
        sources.update(kwargs)
        return sources
    return dict(kwargs)


def _as_uri(value: Any) -> URIRef | None:
    if value is None:
        return None
    if isinstance(value, URIRef):
        return value
    text = str(value).strip()
    if not text:
        return None
    return URIRef(text)


def _item_value(item: Mapping[str, Any] | Any, *keys: str) -> Any:
    if isinstance(item, Mapping):
        for key in keys:
            if key in item:
                return item.get(key)
        return None
    for key in keys:
        if hasattr(item, key):
            return getattr(item, key)
    return None


def _item_values(item: Mapping[str, Any] | Any, *keys: str) -> list[Any]:
    value = _item_value(item, *keys)
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [item for item in value if item is not None]
    return [value]


def _add_node(
    graph: Graph,
    subject: URIRef,
    rdf_type: URIRef,
    item: Mapping[str, Any] | Any,
) -> None:
    graph.add((subject, RDF.type, rdf_type))
    deterministic_id = _item_value(item, "deterministic_id", "deterministicId")
    if deterministic_id is None:
        deterministic_id = str(subject)
    graph.add((subject, HVDC.deterministicId, Literal(str(deterministic_id))))

    label = _item_value(item, "label")
    if label is None:
        label = _item_value(item, "name")
    if label is not None:
        graph.add((subject, RDFS.label, Literal(str(label))))


def build_canonical_graph(*args: object, **kwargs: Any) -> Graph:
    sources = _coerce_sources(args, kwargs)

    graph = Graph()
    graph.bind("hvdc", HVDC)
    graph.bind("hvdce", HVDCE)
    graph.bind("hvdck", HVDCK)
    graph.bind("hvdcm", HVDCM)

    for bucket, rdf_type in _TYPE_BY_BUCKET.items():
        items = sources.get(bucket) or []
        for item in items:
            subject = _as_uri(_item_value(item, "id"))
            if subject is None:
                continue
            _add_node(graph, subject, rdf_type, item)

            if bucket == "cases":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasCase, subject))
            elif bucket == "cargo_items":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                case_id = _as_uri(_item_value(item, "case_id", "caseId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasCargoItem, subject))
                if case_id is not None:
                    graph.add((case_id, HVDC.hasCargoItem, subject))
            elif bucket == "document_refs":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasDocumentRef, subject))
            elif bucket == "status_snapshots":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasStatusSnapshot, subject))
            elif bucket == "events":
                subject_id = _as_uri(_item_value(item, "subject_id", "subjectId", "shipment_id"))
                if subject_id is not None:
                    graph.add((subject, HVDC.hasSubject, subject_id))
                    graph.add((subject_id, HVDC.hasEvent, subject))
            elif bucket == "invoices":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasInvoice, subject))
            elif bucket == "charge_summaries":
                invoice_id = _as_uri(_item_value(item, "invoice_id", "invoiceId"))
                if invoice_id is not None:
                    graph.add((invoice_id, HVDC.hasChargeSummary, subject))
            elif bucket == "settlement_records":
                invoice_id = _as_uri(_item_value(item, "invoice_id", "invoiceId"))
                if invoice_id is not None:
                    graph.add((invoice_id, HVDC.hasSettlementRecord, subject))
            elif bucket == "reconciliation_records":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasReconciliationRecord, subject))
            elif bucket == "cost_attributions":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                invoice_id = _as_uri(_item_value(item, "invoice_id", "invoiceId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasCostAttribution, subject))
                if invoice_id is not None:
                    graph.add((invoice_id, HVDC.hasCostAttribution, subject))
            elif bucket == "guides":
                rule_ids = _item_values(item, "rule_ids", "ruleIds")
                for rule_id_value in rule_ids:
                    rule_id = _as_uri(rule_id_value)
                    if rule_id is not None:
                        graph.add((subject, HVDC.hasRule, rule_id))
            elif bucket == "rules":
                guide_id = _as_uri(_item_value(item, "guide_id", "guideId"))
                if guide_id is not None:
                    graph.add((guide_id, HVDC.hasRule, subject))
                    graph.add((subject, HVDC.hasGuide, guide_id))
            elif bucket == "lessons":
                for anchor_key in (
                    "shipment_id",
                    "location_id",
                    "carrier_id",
                    "pattern_id",
                    "anchor_id",
                    "shipmentId",
                    "locationId",
                    "carrierId",
                    "patternId",
                    "anchorId",
                ):
                    anchor_id = _as_uri(_item_value(item, anchor_key))
                    if anchor_id is not None:
                        graph.add((subject, HVDC.hasAnchor, anchor_id))
                        break
            elif bucket == "patterns":
                continue
            elif bucket == "evidence":
                pattern_id = _as_uri(_item_value(item, "pattern_id", "patternId"))
                if pattern_id is not None:
                    graph.add((subject, HVDC.supportsPattern, pattern_id))
            elif bucket == "mappings":
                source_id = _as_uri(_item_value(item, "source_id", "sourceId"))
                target_id = _as_uri(_item_value(item, "target_id", "targetId"))
                if source_id is not None:
                    graph.add((subject, HVDC.mapsSource, source_id))
                if target_id is not None:
                    graph.add((subject, HVDC.mapsTarget, target_id))

    return graph

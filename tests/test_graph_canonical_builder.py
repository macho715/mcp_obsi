from rdflib import Namespace, URIRef
from rdflib.namespace import RDF

from app.services.graph_canonical_builder import build_canonical_graph


def test_build_canonical_graph_links_core_entities():
    shipment_id = URIRef("https://hvdc.logistics/resource/shipment/HVDC-001")
    case_id = URIRef("https://hvdc.logistics/resource/case/HVDC-001/CASE-01")
    cargo_item_id = URIRef("https://hvdc.logistics/resource/cargo/HVDC-001/CASE-01/PKG-01")
    document_ref_id = URIRef("https://hvdc.logistics/resource/doc/bl/BL-001")
    status_snapshot_id = URIRef("https://hvdc.logistics/resource/status/HVDC-001/current")
    event_id = URIRef("https://hvdc.logistics/resource/event/HVDC-001/ARRIVAL-01")
    invoice_id = URIRef("https://hvdc.logistics/resource/invoice/INV-001")
    charge_summary_id = URIRef("https://hvdc.logistics/resource/charge/INV-001/storage")
    settlement_record_id = URIRef("https://hvdc.logistics/resource/settlement/INV-001")
    reconciliation_record_id = URIRef("https://hvdc.logistics/resource/recon/V001")
    cost_attribution_id = URIRef("https://hvdc.logistics/resource/cost/INV-001/storage")
    guide_id = URIRef("https://hvdc.logistics/resource/guide/g-001")
    rule_id = URIRef("https://hvdc.logistics/resource/rule/r-001")
    lesson_id = URIRef("https://hvdc.logistics/resource/lesson/l-001")
    pattern_id = URIRef("https://hvdc.logistics/resource/pattern/p-001")
    evidence_id = URIRef("https://hvdc.logistics/resource/evidence/e-001")
    mapping_id = URIRef("https://hvdc.logistics/resource/mapping/m-001")

    graph = build_canonical_graph(
        shipments=[
            {"id": shipment_id, "deterministic_id": "shipment:HVDC-001"},
        ],
        cases=[
            {
                "id": case_id,
                "shipment_id": shipment_id,
                "deterministic_id": "case:HVDC-001:CASE-01",
            },
        ],
        cargo_items=[
            {
                "id": cargo_item_id,
                "shipment_id": shipment_id,
                "case_id": case_id,
                "deterministic_id": "cargo:HVDC-001:CASE-01:PKG-01",
            }
        ],
        document_refs=[
            {
                "id": document_ref_id,
                "shipment_id": shipment_id,
                "deterministic_id": "doc:BL-001",
            }
        ],
        status_snapshots=[
            {
                "id": status_snapshot_id,
                "shipment_id": shipment_id,
                "deterministic_id": "status:HVDC-001:current",
            }
        ],
        events=[
            {
                "id": event_id,
                "subject_id": shipment_id,
                "deterministic_id": "event:HVDC-001:ARRIVAL-01",
            }
        ],
        invoices=[
            {
                "id": invoice_id,
                "shipment_id": shipment_id,
                "deterministic_id": "invoice:INV-001",
            }
        ],
        charge_summaries=[
            {
                "id": charge_summary_id,
                "invoice_id": invoice_id,
                "deterministic_id": "charge:INV-001:storage",
            }
        ],
        settlement_records=[
            {
                "id": settlement_record_id,
                "invoice_id": invoice_id,
                "deterministic_id": "settlement:INV-001",
            }
        ],
        reconciliation_records=[
            {
                "id": reconciliation_record_id,
                "shipment_id": shipment_id,
                "deterministic_id": "recon:V001",
            }
        ],
        cost_attributions=[
            {
                "id": cost_attribution_id,
                "shipment_id": shipment_id,
                "invoice_id": invoice_id,
                "deterministic_id": "cost:INV-001:storage",
            }
        ],
        guides=[
            {
                "id": guide_id,
                "rule_ids": [rule_id],
                "deterministic_id": "guide:g-001",
            }
        ],
        rules=[
            {
                "id": rule_id,
                "guide_id": guide_id,
                "deterministic_id": "rule:r-001",
            }
        ],
        lessons=[
            {
                "id": lesson_id,
                "anchor_id": shipment_id,
                "deterministic_id": "lesson:l-001",
            }
        ],
        patterns=[
            {
                "id": pattern_id,
                "deterministic_id": "pattern:p-001",
            }
        ],
        evidence=[
            {
                "id": evidence_id,
                "pattern_id": pattern_id,
                "deterministic_id": "evidence:e-001",
            }
        ],
        mappings=[
            {
                "id": mapping_id,
                "source_id": rule_id,
                "target_id": guide_id,
                "deterministic_id": "mapping:m-001",
            }
        ],
    )

    hvdc = Namespace("http://hvdc.logistics/ontology/")
    assert (shipment_id, RDF.type, hvdc.Shipment) in graph
    assert (shipment_id, hvdc.hasCase, case_id) in graph
    assert (case_id, hvdc.hasCargoItem, cargo_item_id) in graph
    assert (shipment_id, hvdc.hasDocumentRef, document_ref_id) in graph
    assert (shipment_id, hvdc.hasStatusSnapshot, status_snapshot_id) in graph
    assert (shipment_id, hvdc.hasEvent, event_id) in graph
    assert (shipment_id, hvdc.hasInvoice, invoice_id) in graph
    assert (invoice_id, hvdc.hasChargeSummary, charge_summary_id) in graph
    assert (invoice_id, hvdc.hasSettlementRecord, settlement_record_id) in graph
    assert (shipment_id, hvdc.hasReconciliationRecord, reconciliation_record_id) in graph
    assert (shipment_id, hvdc.hasCostAttribution, cost_attribution_id) in graph
    assert (guide_id, hvdc.hasRule, rule_id) in graph
    assert (lesson_id, hvdc.hasAnchor, shipment_id) in graph
    assert (evidence_id, hvdc.supportsPattern, pattern_id) in graph
    assert (mapping_id, hvdc.mapsSource, rule_id) in graph
    assert (mapping_id, hvdc.mapsTarget, guide_id) in graph


def test_build_canonical_graph_uses_each_guides_rule_ids_without_cross_linking():
    guide_a = URIRef("https://hvdc.logistics/resource/guide/g-a")
    guide_b = URIRef("https://hvdc.logistics/resource/guide/g-b")
    rule_a = URIRef("https://hvdc.logistics/resource/rule/r-a")
    rule_b = URIRef("https://hvdc.logistics/resource/rule/r-b")

    graph = build_canonical_graph(
        guides=[
            {
                "id": guide_a,
                "deterministic_id": "guide:g-a",
                "rule_ids": [rule_a],
            },
            {
                "id": guide_b,
                "deterministic_id": "guide:g-b",
                "rule_ids": [rule_b],
            },
        ],
        rules=[
            {
                "id": rule_a,
                "guide_id": guide_a,
                "deterministic_id": "rule:r-a",
            },
            {
                "id": rule_b,
                "guide_id": guide_b,
                "deterministic_id": "rule:r-b",
            },
        ],
    )

    hvdc = Namespace("http://hvdc.logistics/ontology/")
    assert (guide_a, hvdc.hasRule, rule_a) in graph
    assert (guide_b, hvdc.hasRule, rule_b) in graph
    assert (guide_a, hvdc.hasRule, rule_b) not in graph
    assert (guide_b, hvdc.hasRule, rule_a) not in graph


def test_build_canonical_graph_anchors_lessons_via_shipment_and_pattern_ids():
    shipment_id = URIRef("https://hvdc.logistics/resource/shipment/HVDC-010")
    pattern_id = URIRef("https://hvdc.logistics/resource/pattern/P-010")
    shipment_lesson_id = URIRef("https://hvdc.logistics/resource/lesson/L-010")
    pattern_lesson_id = URIRef("https://hvdc.logistics/resource/lesson/L-011")

    graph = build_canonical_graph(
        lessons=[
            {
                "id": shipment_lesson_id,
                "shipment_id": shipment_id,
                "deterministic_id": "lesson:l-010",
            },
            {
                "id": pattern_lesson_id,
                "pattern_id": pattern_id,
                "deterministic_id": "lesson:l-011",
            },
        ]
    )

    hvdc = Namespace("http://hvdc.logistics/ontology/")
    assert (shipment_lesson_id, hvdc.hasAnchor, shipment_id) in graph
    assert (pattern_lesson_id, hvdc.hasAnchor, pattern_id) in graph


def test_build_canonical_graph_links_evidence_to_its_explicit_pattern_id_only():
    pattern_a = URIRef("https://hvdc.logistics/resource/pattern/P-A")
    pattern_b = URIRef("https://hvdc.logistics/resource/pattern/P-B")
    evidence_id = URIRef("https://hvdc.logistics/resource/evidence/E-A")

    graph = build_canonical_graph(
        patterns=[
            {"id": pattern_a, "deterministic_id": "pattern:p-a"},
            {"id": pattern_b, "deterministic_id": "pattern:p-b"},
        ],
        evidence=[
            {
                "id": evidence_id,
                "pattern_id": pattern_a,
                "deterministic_id": "evidence:e-a",
            }
        ],
    )

    hvdc = Namespace("http://hvdc.logistics/ontology/")
    assert (evidence_id, hvdc.supportsPattern, pattern_a) in graph
    assert (evidence_id, hvdc.supportsPattern, pattern_b) not in graph

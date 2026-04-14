import pytest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from app.services.graph_canonical_builder import build_canonical_graph
from app.services.graph_validation import validate_canonical_graph

HVDC = Namespace("http://hvdc.logistics/ontology/")


def test_validate_canonical_graph_rejects_event_without_subject():
    graph = Graph()
    event_id = URIRef("https://hvdc.logistics/resource/event/E-001")
    graph.add((event_id, RDF.type, HVDC.Event))

    with pytest.raises(ValueError, match="event_without_subject"):
        validate_canonical_graph(graph)


def test_validate_canonical_graph_rejects_duplicate_deterministic_ids():
    graph = Graph()
    first = URIRef("https://hvdc.logistics/resource/guide/G-001")
    second = URIRef("https://hvdc.logistics/resource/rule/R-001")
    graph.add((first, HVDC.deterministicId, Literal("dup-001")))
    graph.add((second, HVDC.deterministicId, Literal("dup-001")))

    with pytest.raises(ValueError, match="duplicate_deterministic_ids"):
        validate_canonical_graph(graph)


def test_validate_canonical_graph_rejects_guide_without_rule():
    graph = Graph()
    guide = URIRef("https://hvdc.logistics/resource/guide/G-001")
    graph.add((guide, RDF.type, HVDC.Guide))

    with pytest.raises(ValueError, match="guide_without_rule"):
        validate_canonical_graph(graph)


def test_validate_canonical_graph_rejects_lesson_without_anchor():
    graph = Graph()
    lesson = URIRef("https://hvdc.logistics/resource/lesson/L-001")
    graph.add((lesson, RDF.type, HVDC.Lesson))

    with pytest.raises(ValueError, match="lesson_without_anchor"):
        validate_canonical_graph(graph)


def test_validate_canonical_graph_accepts_distinct_guide_rule_and_anchor_links():
    shipment_id = URIRef("https://hvdc.logistics/resource/shipment/HVDC-020")
    pattern_id = URIRef("https://hvdc.logistics/resource/pattern/P-020")
    guide = URIRef("https://hvdc.logistics/resource/guide/G-020")
    rule = URIRef("https://hvdc.logistics/resource/rule/R-020")
    lesson = URIRef("https://hvdc.logistics/resource/lesson/L-020")
    evidence = URIRef("https://hvdc.logistics/resource/evidence/E-020")

    graph = build_canonical_graph(
        shipments=[{"id": shipment_id, "deterministic_id": "shipment:020"}],
        guides=[{"id": guide, "rule_ids": [rule], "deterministic_id": "guide:020"}],
        rules=[{"id": rule, "guide_id": guide, "deterministic_id": "rule:020"}],
        lessons=[{"id": lesson, "shipment_id": shipment_id, "deterministic_id": "lesson:020"}],
        patterns=[{"id": pattern_id, "deterministic_id": "pattern:020"}],
        evidence=[
            {
                "id": evidence,
                "pattern_id": pattern_id,
                "deterministic_id": "evidence:020",
            }
        ],
    )

    validate_canonical_graph(graph)

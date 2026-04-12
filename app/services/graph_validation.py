from __future__ import annotations

from rdflib import Graph
from rdflib.namespace import RDF

from app.services.graph_canonical_builder import HVDC


def validate_canonical_graph(graph: Graph) -> None:
    deterministic_ids: dict[str, str] = {}

    for subject, _predicate, object_ in graph.triples((None, HVDC.deterministicId, None)):
        value = str(object_)
        existing = deterministic_ids.get(value)
        if existing is not None and existing != str(subject):
            raise ValueError("duplicate_deterministic_ids")
        deterministic_ids[value] = str(subject)

    for subject in graph.subjects(RDF.type, HVDC.Event):
        if not any(graph.objects(subject, HVDC.hasSubject)):
            raise ValueError("event_without_subject")

    for subject in graph.subjects(RDF.type, HVDC.Guide):
        if not any(graph.objects(subject, HVDC.hasRule)):
            raise ValueError("guide_without_rule")

    for subject in graph.subjects(RDF.type, HVDC.Lesson):
        if not any(graph.objects(subject, HVDC.hasAnchor)):
            raise ValueError("lesson_without_anchor")

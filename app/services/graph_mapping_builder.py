from __future__ import annotations

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS

HVDC = Namespace("http://hvdc.logistics/ontology/")
HVDCE = Namespace("http://hvdc.logistics/ontology/event/")
HVDCK = Namespace("http://hvdc.logistics/ontology/knowledge/")
HVDCM = Namespace("http://hvdc.logistics/ontology/mapping/")


def build_compatibility_mappings() -> Graph:
    graph = Graph()
    graph.bind("hvdc", HVDC)
    graph.bind("hvdce", HVDCE)
    graph.bind("hvdck", HVDCK)
    graph.bind("hvdcm", HVDCM)

    operation_carrier = HVDC.OperationCarrier
    consolidated_target = HVDCM["CONSOLIDATED-04"]

    graph.add((operation_carrier, RDF.type, RDFS.Class))
    graph.add((consolidated_target, RDF.type, RDFS.Resource))
    graph.add((consolidated_target, RDFS.label, Literal("CONSOLIDATED-04")))
    graph.add((operation_carrier, HVDCM.compatibleWith, consolidated_target))
    graph.add((operation_carrier, HVDCM.mappingScope, Literal("CONSOLIDATED-04")))

    return graph

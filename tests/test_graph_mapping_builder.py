from rdflib import Namespace
from rdflib.namespace import RDF, RDFS

from app.services.graph_mapping_builder import build_compatibility_mappings


def test_build_compatibility_mappings_exposes_operation_carrier_and_consolidated_04_target():
    graph = build_compatibility_mappings()
    hvdc = Namespace("http://hvdc.logistics/ontology/")
    hvdcm = Namespace("http://hvdc.logistics/ontology/mapping/")

    namespaces = dict(graph.namespaces())

    assert str(namespaces["hvdc"]) == str(hvdc)
    assert str(namespaces["hvdcm"]) == str(hvdcm)
    assert (hvdc.OperationCarrier, RDF.type, RDFS.Class) in graph
    assert (hvdcm["CONSOLIDATED-04"], RDF.type, RDFS.Resource) in graph

from app.services.external_schema_import import (
    ExternalSchemaSnapshot,
    find_mapping_warnings,
    load_external_schema,
    shacl_subset_to_ui_filters,
)
from scripts.build_dashboard_graph_data import _collect_external_ontology_overlay


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_load_external_schema_collects_classes_and_properties(monkeypatch):
    call_count = {"count": 0}

    def _fake_get(*_args, **_kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return _FakeResponse(
                {
                    "results": {
                        "bindings": [
                            {"class": {"value": "http://example.org/ClassA"}},
                            {"class": {"value": "http://example.org/ClassB"}},
                        ]
                    }
                }
            )
        return _FakeResponse(
            {
                "results": {
                    "bindings": [
                        {"property": {"value": "http://example.org/p/name"}},
                        {"property": {"value": "http://example.org/p/date"}},
                    ]
                }
            }
        )

    monkeypatch.setattr("app.services.external_schema_import.requests.get", _fake_get)

    snapshot = load_external_schema("https://example.org/sparql")

    assert snapshot.endpoint == "https://example.org/sparql"
    assert snapshot.classes == ["http://example.org/ClassA", "http://example.org/ClassB"]
    assert snapshot.properties == ["http://example.org/p/date", "http://example.org/p/name"]
    assert len(snapshot.sample_queries) == 2


def test_shacl_subset_to_ui_filters_supports_subset_property_shapes():
    shacl_turtle = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:ShipmentShape a sh:NodeShape ;
  sh:targetClass ex:Shipment ;
  sh:property [
    sh:path ex:departureDate ;
    sh:name "ATD" ;
    sh:datatype xsd:date
  ] ;
  sh:property [
    sh:path ex:shipMode ;
    sh:name "Ship Mode" ;
    sh:in ("SEA" "AIR")
  ] .
"""
    filters = shacl_subset_to_ui_filters(shacl_turtle)
    filter_by_label = {item.label: item for item in filters}

    assert filter_by_label["ATD"].input_type == "date"
    assert filter_by_label["Ship Mode"].input_type == "select"
    assert filter_by_label["Ship Mode"].options == ["SEA", "AIR"]


def test_find_mapping_warnings_respects_stage():
    warnings_poc = find_mapping_warnings(external_properties=set(), stage="poc")
    warning_fields = {item.domain_field for item in warnings_poc}
    assert "coe" in warning_fields
    assert "atd" not in warning_fields

    warnings_beta = find_mapping_warnings(external_properties=set(), stage="beta")
    warning_fields_beta = {item.domain_field for item in warnings_beta}
    assert "atd" in warning_fields_beta


def test_collect_external_ontology_overlay_serializes_mapping_warnings(monkeypatch):
    monkeypatch.setenv("KG_EXTERNAL_ONTOLOGY_STAGE", "poc")
    monkeypatch.setenv("KG_EXTERNAL_SPARQL_ENDPOINT", "https://example.org/sparql")
    monkeypatch.setattr(
        "scripts.build_dashboard_graph_data.load_external_schema",
        lambda endpoint: ExternalSchemaSnapshot(
            endpoint=endpoint,
            classes=["http://example.org/ClassA"],
            properties=[],
            sample_queries=[],
        ),
    )

    overlay, filters = _collect_external_ontology_overlay()

    assert overlay["stage"] == "poc"
    assert overlay["loaded_classes"] == 1
    assert filters == []
    assert overlay["mapping_warnings"][0]["domain_field"] == "coe"

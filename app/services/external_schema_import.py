from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal

import requests

ImportStage = Literal["off", "poc", "beta"]


@dataclass(slots=True)
class ExternalSchemaSnapshot:
    endpoint: str
    classes: list[str]
    properties: list[str]
    sample_queries: list[dict[str, str]]


@dataclass(slots=True)
class UiFilterDefinition:
    id: str
    label: str
    property_uri: str
    input_type: str
    options: list[str]
    source_shape: str


@dataclass(slots=True)
class FieldMappingRule:
    domain_field: str
    external_property_uri: str
    required_stage: ImportStage = "poc"


@dataclass(slots=True)
class SchemaMappingWarning:
    domain_field: str
    external_property_uri: str
    warning: str


DEFAULT_DOMAIN_FIELD_MAPPINGS: tuple[FieldMappingRule, ...] = (
    FieldMappingRule(
        domain_field="coe",
        external_property_uri="http://dbpedia.org/ontology/country",
    ),
    FieldMappingRule(
        domain_field="pol",
        external_property_uri="http://dbpedia.org/ontology/departureAirport",
    ),
    FieldMappingRule(
        domain_field="pod",
        external_property_uri="http://dbpedia.org/ontology/arrivalAirport",
    ),
    FieldMappingRule(
        domain_field="shipMode",
        external_property_uri="http://dbpedia.org/ontology/meansOfTransportation",
    ),
    FieldMappingRule(
        domain_field="atd",
        external_property_uri="http://dbpedia.org/ontology/departureDate",
        required_stage="beta",
    ),
    FieldMappingRule(
        domain_field="ata",
        external_property_uri="http://dbpedia.org/ontology/arrivalDate",
        required_stage="beta",
    ),
)


def _select_input_type(datatype_uri: str | None, has_enumeration: bool) -> str:
    if has_enumeration:
        return "select"
    if datatype_uri and datatype_uri.endswith("dateTime"):
        return "datetime"
    if datatype_uri and datatype_uri.endswith("date"):
        return "date"
    if datatype_uri and datatype_uri.endswith(("integer", "decimal", "float", "double")):
        return "number"
    return "text"


def _run_select(endpoint: str, query: str, timeout_seconds: float) -> list[dict[str, Any]]:
    response = requests.get(
        endpoint,
        params={
            "query": f"PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
            f"PREFIX owl: <http://www.w3.org/2002/07/owl#>\n{query}",
            "format": "application/sparql-results+json",
        },
        timeout=timeout_seconds,
        headers={"Accept": "application/sparql-results+json"},
    )
    response.raise_for_status()
    payload = response.json()
    bindings = payload.get("results", {}).get("bindings", [])
    return bindings if isinstance(bindings, list) else []


def load_external_schema(
    endpoint: str,
    *,
    timeout_seconds: float = 12.0,
) -> ExternalSchemaSnapshot:
    class_query = """
        SELECT DISTINCT ?class WHERE {
          ?class a owl:Class .
          FILTER(isIRI(?class))
        }
        LIMIT 200
    """
    property_query = """
        SELECT DISTINCT ?property WHERE {
          ?property a rdf:Property .
          FILTER(isIRI(?property))
        }
        LIMIT 400
    """
    class_bindings = _run_select(endpoint, class_query, timeout_seconds)
    property_bindings = _run_select(endpoint, property_query, timeout_seconds)

    classes = sorted(
        {
            item.get("class", {}).get("value", "").strip()
            for item in class_bindings
            if item.get("class", {}).get("value")
        }
    )
    properties = sorted(
        {
            item.get("property", {}).get("value", "").strip()
            for item in property_bindings
            if item.get("property", {}).get("value")
        }
    )
    sample_queries = [
        {
            "name": "List classes",
            "query": "SELECT DISTINCT ?class WHERE { ?class a owl:Class } LIMIT 50",
        },
        {
            "name": "List properties",
            "query": "SELECT DISTINCT ?property WHERE { ?property a rdf:Property } LIMIT 50",
        },
    ]
    return ExternalSchemaSnapshot(
        endpoint=endpoint,
        classes=classes,
        properties=properties,
        sample_queries=sample_queries,
    )


def shacl_subset_to_ui_filters(shacl_turtle: str) -> list[UiFilterDefinition]:
    prefix_map: dict[str, str] = {}
    for prefix, uri in re.findall(r"@prefix\s+([A-Za-z][\w-]*):\s*<([^>]+)>\s*\.", shacl_turtle):
        prefix_map[prefix] = uri

    def _expand(term: str) -> str:
        token = term.strip().strip(";").strip()
        if token.startswith("<") and token.endswith(">"):
            return token[1:-1]
        if ":" not in token:
            return token
        prefix, local = token.split(":", maxsplit=1)
        base = prefix_map.get(prefix)
        if base is None:
            return token
        return f"{base}{local}"

    def _label_from_path(path_uri: str) -> str:
        tail = path_uri.rstrip("/").rsplit("/", maxsplit=1)[-1]
        return tail.rsplit("#", maxsplit=1)[-1]

    filters: list[UiFilterDefinition] = []
    shape_pattern = re.compile(
        r"([A-Za-z][\w-]*:[\w-]+)\s+a\s+sh:NodeShape\s*;\s*(.*?)\.\s*",
        flags=re.DOTALL,
    )
    for shape_ref, shape_body in shape_pattern.findall(shacl_turtle):
        shape_id = _expand(shape_ref)
        property_blocks = re.findall(r"sh:property\s*\[(.*?)\]", shape_body, flags=re.DOTALL)
        for block in property_blocks:
            path_match = re.search(r"sh:path\s+([^;\n]+)", block)
            if not path_match:
                continue
            path_uri = _expand(path_match.group(1))
            label_match = re.search(r'sh:name\s+"([^"]+)"', block)
            label = label_match.group(1) if label_match else _label_from_path(path_uri)
            datatype_match = re.search(r"sh:datatype\s+([^;\n]+)", block)
            datatype_uri = _expand(datatype_match.group(1)) if datatype_match else None
            enum_match = re.search(r"sh:in\s*\(([^)]+)\)", block, flags=re.DOTALL)
            options = re.findall(r'"([^"]+)"', enum_match.group(1)) if enum_match else []
            input_type = _select_input_type(datatype_uri, bool(options))
            filters.append(
                UiFilterDefinition(
                    id=f"{shape_id}::{path_uri}",
                    label=label,
                    property_uri=path_uri,
                    input_type=input_type,
                    options=options,
                    source_shape=shape_id,
                )
            )
    return filters


def find_mapping_warnings(
    *,
    external_properties: set[str],
    stage: ImportStage,
    mappings: tuple[FieldMappingRule, ...] = DEFAULT_DOMAIN_FIELD_MAPPINGS,
) -> list[SchemaMappingWarning]:
    stage_order = {"off": 0, "poc": 1, "beta": 2}
    active = [
        rule
        for rule in mappings
        if stage_order[rule.required_stage] <= stage_order[stage]
    ]

    warnings: list[SchemaMappingWarning] = []
    for rule in active:
        if rule.external_property_uri in external_properties:
            continue
        warnings.append(
            SchemaMappingWarning(
                domain_field=rule.domain_field,
                external_property_uri=rule.external_property_uri,
                warning="mapped property missing in external ontology schema",
            )
        )
    return warnings

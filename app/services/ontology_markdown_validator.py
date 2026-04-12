from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph

try:
    from pyshacl import validate as pyshacl_validate
except ImportError:  # pragma: no cover - exercised via runner behavior
    pyshacl_validate = None


FENCED_BLOCK_RE = re.compile(r"```([A-Za-z0-9_+-]+)\r?\n(.*?)```", re.DOTALL)
PREFIX_LINE_RE = re.compile(r"@prefix\s+([A-Za-z_][\w-]*):\s+<([^>]+)>\s+\.")
DEFAULT_PREFIXES = {
    "rdf": "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
    "rdfs": "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
    "owl": "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
    "xsd": "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
    "sh": "@prefix sh: <http://www.w3.org/ns/shacl#> .",
    "hvdc": "@prefix hvdc: <http://samsung.com/project-logistics#> .",
    "debulk": "@prefix debulk: <https://hvdc-project.com/ontology/bulk-cargo/> .",
}


@dataclass
class OntologyValidationReport:
    path: Path
    conforms: bool
    shape_block_count: int
    data_block_count: int
    jsonld_block_count: int
    shape_triples: int
    data_triples: int
    results_text: str


def extract_fenced_code_blocks(markdown: str, language: str) -> list[str]:
    wanted = language.lower()
    blocks: list[str] = []
    for found_language, content in FENCED_BLOCK_RE.findall(markdown):
        if found_language.lower() == wanted:
            blocks.append(content.strip())
    return blocks


def _is_shape_block(block: str) -> bool:
    return "sh:NodeShape" in block or "sh:PropertyShape" in block


def _collect_prefix_lines(blocks: list[str]) -> str:
    seen: set[str] = set()
    seen_prefixes: set[str] = set()
    ordered: list[str] = []
    for block in blocks:
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("@prefix ") and stripped not in seen:
                seen.add(stripped)
                prefix_name = stripped.split()[1].rstrip(":")
                seen_prefixes.add(prefix_name)
                ordered.append(stripped)
    for prefix_name, prefix_line in DEFAULT_PREFIXES.items():
        if prefix_name not in seen_prefixes:
            ordered.append(prefix_line)
    return "\n".join(ordered)


def _prefix_map(prefix_preamble: str) -> dict[str, str]:
    return {name: iri for name, iri in PREFIX_LINE_RE.findall(prefix_preamble)}


def _expand_prefixed_path_names(block: str, prefix_preamble: str) -> str:
    prefix_map = _prefix_map(prefix_preamble)
    normalized = block
    for prefix_name, iri in prefix_map.items():
        pattern = re.compile(rf"\b{re.escape(prefix_name)}:([A-Za-z0-9._-]+/[A-Za-z0-9._/\-]+)")
        normalized = pattern.sub(lambda match: f"<{iri}{match.group(1)}>", normalized)
    return normalized


def _parse_turtle_blocks(blocks: list[str], prefix_preamble: str = "") -> Graph:
    graph = Graph()
    for block in blocks:
        parseable_block = _expand_prefixed_path_names(block, prefix_preamble)
        parseable = f"{prefix_preamble}\n{parseable_block}" if prefix_preamble else parseable_block
        graph.parse(data=parseable, format="turtle")
    return graph


def _parse_jsonld_blocks(blocks: list[str]) -> Graph:
    graph = Graph()
    for block in blocks:
        payload = json.loads(block)
        if "@context" not in payload:
            continue
        graph.parse(data=json.dumps(payload), format="json-ld")
    return graph


def validate_markdown_ontology(paths: list[Path]) -> list[OntologyValidationReport]:
    if pyshacl_validate is None:
        raise RuntimeError("pyshacl is not installed")

    reports: list[OntologyValidationReport] = []

    for path in paths:
        markdown = path.read_text(encoding="utf-8")
        turtle_blocks = extract_fenced_code_blocks(markdown, "turtle")
        jsonld_blocks = extract_fenced_code_blocks(markdown, "json")
        prefix_preamble = _collect_prefix_lines(turtle_blocks)

        shape_blocks = [block for block in turtle_blocks if _is_shape_block(block)]
        data_blocks = [block for block in turtle_blocks if not _is_shape_block(block)]

        try:
            shape_graph = _parse_turtle_blocks(shape_blocks, prefix_preamble=prefix_preamble)
            data_graph = _parse_turtle_blocks(data_blocks, prefix_preamble=prefix_preamble)
            data_graph += _parse_jsonld_blocks(jsonld_blocks)

            conforms, _, results_text = pyshacl_validate(
                data_graph,
                shacl_graph=shape_graph,
                inference="rdfs",
                abort_on_first=False,
                allow_infos=True,
                allow_warnings=True,
                advanced=True,
            )
            report_conforms = bool(conforms)
            report_text = str(results_text).strip()
            shape_triples = len(shape_graph)
            data_triples = len(data_graph)
        except Exception as exc:  # pragma: no cover - exercised by integration test and runner
            report_conforms = False
            report_text = str(exc).strip()
            shape_triples = 0
            data_triples = 0

        reports.append(
            OntologyValidationReport(
                path=path,
                conforms=report_conforms,
                shape_block_count=len(shape_blocks),
                data_block_count=len(data_blocks),
                jsonld_block_count=len(jsonld_blocks),
                shape_triples=shape_triples,
                data_triples=data_triples,
                results_text=report_text,
            )
        )

    return reports

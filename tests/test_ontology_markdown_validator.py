from pathlib import Path

from app.services.ontology_markdown_validator import (
    extract_fenced_code_blocks,
    validate_markdown_ontology,
)


def test_extract_fenced_code_blocks_returns_requested_language():
    markdown = """
```turtle
@prefix ex: <http://example.org/> .
ex:a ex:b ex:c .
```

```json
{"hello": "world"}
```
"""

    assert extract_fenced_code_blocks(markdown, "turtle") == [
        "@prefix ex: <http://example.org/> .\nex:a ex:b ex:c ."
    ]
    assert extract_fenced_code_blocks(markdown, "json") == ['{"hello": "world"}']


def test_validate_markdown_ontology_runs_shacl_for_embedded_turtle(tmp_path: Path):
    markdown = """
```turtle
@prefix ex: <http://example.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:ThingShape a sh:NodeShape ;
  sh:targetClass ex:Thing ;
  sh:property [
    sh:path ex:name ;
    sh:datatype xsd:string ;
    sh:minCount 1 ;
  ] .
```

```turtle
@prefix ex: <http://example.org/> .

ex:item-1 a ex:Thing ;
  ex:name "valid" .
```
"""
    doc = tmp_path / "ontology.md"
    doc.write_text(markdown, encoding="utf-8")

    reports = validate_markdown_ontology([doc])

    assert len(reports) == 1
    assert reports[0].path == doc
    assert reports[0].conforms is True
    assert reports[0].shape_block_count == 1
    assert reports[0].data_block_count == 1


def test_validate_markdown_ontology_accepts_prefixed_paths_with_slashes(tmp_path: Path):
    markdown = """
```turtle
@prefix ex: <http://example.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:ThingShape a sh:NodeShape ;
  sh:targetClass ex:Thing ;
  sh:property [
    sh:path ex:name ;
    sh:datatype xsd:string ;
    sh:minCount 1 ;
  ] .
```

```turtle
ex:item/example-1 a ex:Thing ;
  ex:name "valid" .
```
"""
    doc = tmp_path / "ontology.md"
    doc.write_text(markdown, encoding="utf-8")

    reports = validate_markdown_ontology([doc])

    assert reports[0].conforms is True


def test_validate_markdown_ontology_reports_shacl_runtime_errors(tmp_path: Path):
    markdown = """
```turtle
@prefix ex: <http://example.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .

ex:BrokenShape a sh:NodeShape ;
  sh:targetClass ex:Thing ;
  sh:sparql [
    sh:message "broken query" ;
    sh:select "SELECT WHERE {"
  ] .
```

```turtle
@prefix ex: <http://example.org/> .
ex:item/example-1 a ex:Thing .
```
"""
    doc = tmp_path / "broken-ontology.md"
    doc.write_text(markdown, encoding="utf-8")

    reports = validate_markdown_ontology([doc])

    assert reports[0].conforms is False
    assert "Expected SelectQuery" in reports[0].results_text

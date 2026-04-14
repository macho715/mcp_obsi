---
title: "kg-dashboard Canonical Ontology Redesign"
type: "design-spec"
version: "1.0"
date: "2026-04-12"
author: "Codex brainstorming session"
status: "approved"
source_of_truth:
  - "Excel = shipment and route facts"
  - "wiki analyses = issue and event evidence"
  - "ontology docs = schema and rule registry"
decisions:
  - "Option B selected: canonical ontology core plus dashboard projection"
  - "Entity and event layers are separated"
  - "Dashboard reads projection, not canonical facts directly"
  - "Resolver emits resolved, ambiguous, unresolved states"
---

# kg-dashboard Canonical Ontology Redesign

## Summary

Current graph export logic mixes three concerns in one path:

1. source ingestion from Excel and wiki notes
2. ontology meaning and link resolution
3. dashboard-friendly flat graph generation

That coupling causes three observed failures:

- issue notes are silently dropped or left isolated when tags do not match a small hard-coded alias set
- route columns can disappear without failing the export
- dated route facts are flattened into timeless edges, so chronology is lost

The target design introduces a canonical ontology core with explicit event modeling,
then derives a lightweight dashboard projection from that core.

---

## Problem Statement

### Current state

- `scripts/build_dashboard_graph_data.py` reads Excel and wiki notes directly and emits
  dashboard JSON plus TTL in one pass.
- Route columns such as `MOSB`, `DSV Indoor`, `SHU`, `MIR`, `DAS`, and `AGI` are treated
  as presence flags even though the underlying values are dates.
- Wiki tags are mapped to graph targets through a narrow hard-coded alias list.
- Dashboard contract checks protect flat JSON shape, but they do not verify resolver
  coverage or canonical route semantics.

### Target state

- Canonical ontology facts preserve entity identity, event chronology, source provenance,
  and resolution status.
- Dashboard graph files become projections derived from canonical facts, not the storage
  model itself.
- Validation gates stop silent drift at source, resolver, canonical, and projection stages.
- Audit artifacts make unresolved and ambiguous cases visible.

---

## Options Considered

| Option | Description | Strength | Weakness |
|---|---|---|---|
| A | Keep current exporter shape and harden aliases and tests | Fastest | Still mixes ontology and projection concerns |
| B | Build canonical ontology core and derive dashboard projection from it | Balanced, preserves meaning, limits UI churn | Medium implementation scope |
| C | Rebuild everything as RDF-first triple pipeline with SHACL-first runtime | Strongest formal rigor | Too large for current repository scope |

### Recommendation

Choose **Option B**.

It fixes the semantic problems without forcing the dashboard to consume a new runtime
contract immediately. The ontology becomes the source of meaning, while the dashboard
continues to read flat `nodes.json` and `edges.json` as a read model.

### Rollback

Keep legacy entrypoints as compatibility wrappers until the new canonical pipeline and
projection path have both passed local and CI validation.

---

## Section 1: Architecture

### Target layers

1. **Schema layer**
   - ontology documents define allowed classes, relations, and constraints
   - this layer does not rewrite source facts

2. **Canonical fact layer**
   - Excel becomes shipment and route fact input
   - wiki analyses become issue, issue-event, and evidence input
   - this layer stores semantic truth, not dashboard convenience

3. **Projection layer**
   - dashboard JSON is rebuilt from canonical facts
   - projection can collapse event detail while preserving canonical source history

### Core principles

- model route facts as events before flattening them into graph edges
- preserve dated movement and storage facts in canonical form
- route wiki tags through a resolver instead of direct edge generation
- keep dashboard projection replaceable without reworking ontology core

---

## Section 2: Canonical Data Model

### Core entities

- `Shipment`
- `Order`
- `Vendor`
- `Vessel`
- `Hub`
- `Warehouse`
- `Site`
- `Issue`
- `DocumentEvidence`

### Core events

- `RouteLegEvent`
  - shipment reached or moved through a route node on a known date
- `StorageEvent`
  - shipment was stored at a warehouse on a known date
- `ConsolidationEvent`
  - shipment was consolidated at a hub on a known date
- `IssueEvent`
  - issue described by wiki evidence
- `IssueLink`
  - resolver output that ties issues to entities or events

### Identity rules

- entity IDs stay stable across runs
- event IDs are derived from `subject + predicate + object + date + source`
- repeated visits to the same node become distinct events when the date differs

### Source mapping

- Excel
  - `SCT SHIP NO.` -> `Shipment`
  - `PO No.` -> `Order`
  - `VENDOR` -> `Vendor`
  - `VESSEL NAME/ FLIGHT No.` -> `Vessel`
  - dated location columns -> route, storage, or consolidation events
- wiki analyses
  - `slug`, `title`, `tags`, and body evidence -> `Issue`, `IssueEvent`, `DocumentEvidence`
- ontology docs
  - class, relation, and constraint registry only

### Projection rule

Dashboard files are derived views.

Examples:

- canonical fact: `RouteLegEvent(Shipment A, deliveredTo, AGI, 2025-12-07)`
- projection edge: `Shipment A -> AGI deliveredTo`

- canonical fact: `IssueEvent(Low tide delay)` plus `IssueLink(Issue -> JPT71)`
- projection edge: `Issue -> JPT71 relatedTo`

### Resolver rule

Wiki tags do not create edges directly.

They first go through alias and context resolution:

- `resolved`
- `ambiguous`
- `unresolved`

Resolved items become canonical links.
Ambiguous and unresolved items become audit output and policy-driven gate inputs.

---

## Section 3: Extraction Pipeline and Validation Gate

### Pipeline

1. **Source ingest**
   - read Excel, wiki notes, and ontology docs
   - no graph edges created yet

2. **Source normalization**
   - convert source rows and notes into typed normalized records
   - parse dates here
   - extract alias candidates here

3. **Resolver**
   - entity resolver maps names to canonical IDs
   - issue-link resolver maps wiki signals to canonical targets
   - output state is `resolved`, `ambiguous`, or `unresolved`

4. **Canonical fact build**
   - create entities and events only after normalization and resolution

5. **Projection build**
   - create dashboard graph projection
   - create resolver audit projection

6. **Validation gate**
   - source contract
   - resolver quality
   - canonical integrity
   - projection integrity

### Validation gates

#### Gate A: Source contract

- required Excel columns must exist
- markdown frontmatter keys must exist
- route date cells must parse under a declared policy
- failure stops the build

#### Gate B: Resolver quality

- unresolved issue-link count
- ambiguous alias count
- orphan issue count
- policy starts as warn-capable, then can be tightened to fail

#### Gate C: Canonical integrity

- no dangling relation
- no event without subject
- event date policy must be explicit
- ontology rule violations fail the build

#### Gate D: Projection integrity

- deterministic `nodes.json` and `edges.json`
- required keys exist
- no leaked `Unknown`
- no leaked `rdf-schema#Class`
- dashboard smoke checks pass

### Failure policy

- source contract failures: fail
- canonical integrity failures: fail
- projection integrity failures: fail
- resolver quality failures: warn or fail by threshold

### Audit output

Generate machine-readable artifacts for:

- unresolved aliases
- ambiguous tags
- orphan issues
- dropped source rows
- projection delta summary

These outputs are required for operator review and regression diagnosis.

---

## Section 4: File Plan, Test Strategy, and Rollout

### Planned file structure

| File | Change | Purpose |
|---|---|---|
| `scripts/build_dashboard_graph_data.py` | modify | final orchestration entrypoint |
| `scripts/build_knowledge_graph.py` | modify | legacy compatibility wrapper |
| `scripts/ttl_to_json.py` | modify | legacy renderer only |
| `app/services/graph_source_loader.py` | create | source ingest |
| `app/services/graph_normalizer.py` | create | typed normalization |
| `app/services/graph_resolver.py` | create | alias and issue-link resolution |
| `app/services/graph_canonical_builder.py` | create | entity and event construction |
| `app/services/graph_projection_builder.py` | create | dashboard projection generation |
| `app/services/graph_validation.py` | create | gate checks |
| `tests/test_graph_source_loader.py` | create | source contract tests |
| `tests/test_graph_resolver.py` | create | resolver tests |
| `tests/test_graph_canonical_builder.py` | create | canonical integrity tests |
| `tests/test_dashboard_graph_export.py` | modify | end-to-end projection contract |
| `tests/test_ttl_to_json.py` | keep or reduce | legacy renderer regression |
| `runtime/audits/graph_*.json` | generate | resolver and delta audit output |
| `kg-dashboard/public/data/nodes.json` | regenerate | new projection artifact |
| `kg-dashboard/public/data/edges.json` | regenerate | new projection artifact |

### Test strategy

#### Unit tests

- source loader
- normalizer
- resolver
- canonical builder
- projection builder
- validation gates

#### Contract tests

- node required keys
- edge required keys
- deterministic ordering
- no dangling edges
- no leaked `Unknown`
- no leaked `rdf-schema#Class`

#### Resolver quality tests

- expected alias resolves to expected canonical target
- ambiguous alias is captured in audit output
- unresolved tag is never silently dropped

#### Canonical integrity tests

- event cannot exist without subject
- route and storage facts respect date policy
- issue links have explicit resolution state

#### Smoke tests

- `.venv\\Scripts\\python.exe -m pytest`
- `.venv\\Scripts\\python.exe -m ruff check scripts/build_dashboard_graph_data.py app/services/graph_source_loader.py app/services/graph_normalizer.py app/services/graph_resolver.py app/services/graph_canonical_builder.py app/services/graph_projection_builder.py app/services/graph_validation.py tests/test_graph_source_loader.py tests/test_graph_resolver.py tests/test_graph_canonical_builder.py tests/test_dashboard_graph_export.py tests/test_ttl_to_json.py`
- `.venv\\Scripts\\python.exe -m ruff format --check scripts/build_dashboard_graph_data.py app/services/graph_source_loader.py app/services/graph_normalizer.py app/services/graph_resolver.py app/services/graph_canonical_builder.py app/services/graph_projection_builder.py app/services/graph_validation.py tests/test_graph_source_loader.py tests/test_graph_resolver.py tests/test_graph_canonical_builder.py tests/test_dashboard_graph_export.py tests/test_ttl_to_json.py`
- `npm test`
- `npm run lint`
- `npm run build`

### Rollout plan

#### Phase A: Parallel introduction

- add canonical services beside current scripts
- keep existing entrypoints intact

#### Phase B: Projection switch

- move `scripts/build_dashboard_graph_data.py` onto canonical pipeline
- regenerate dashboard artifacts
- publish delta plus audit summary

#### Phase C: Gate hardening

- start resolver threshold as warn
- raise to fail after stabilization

#### Phase D: Legacy retirement

- keep legacy scripts as wrappers only
- update docs and CI to canonical path

### Approval points

- alias taxonomy
- unresolved and ambiguous fail threshold
- projection delta tolerance
- legacy retirement timing

### Success criteria

- issue isolation rate drops materially from current baseline
- route dates survive in canonical form
- projection remains deterministic
- dashboard remains consumable without schema break
- unresolved and ambiguous reasons are visible in audit artifacts

---

## Open Questions For Implementation Planning

These questions do not block the design itself, but they must be fixed before
implementation details are written:

1. whether `Mirfa`, `Zakum`, and `Anchorage` resolve to existing canonical nodes
   or require new node families
2. whether route events with missing dates should be rejected or stored with
   an explicit `date_unknown` state
3. what threshold should move resolver quality from warning to failure

---

## Out of Scope

- dashboard UI redesign
- switching the dashboard to a new runtime API contract
- replacing flat `nodes.json` and `edges.json` during the first rollout
- full RDF-first runtime migration

# Shipment Route And Port Timing Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `COE`, `POL`, `POD`, `SHIP MODE`, `ATD`, and `ATA` from `HVDC STATUS.xlsx` into the shipment-centric ontology pipeline so the canonical graph models route ports and timing correctly, while the dashboard export gets shipment-level convenience mirrors for inspection.

**Architecture:** The implementation stays inside the existing shipment-centric pipeline. Shared canonical types and the shared normalizer gain route, leg, and milestone structures; the canonical graph builder emits the corresponding triples; and the dashboard export exposes safe shipment-node mirrors for UI inspection without making shipment-level strings the source of truth. `ATD` and `ATA` are owned by milestone events, while `COE`, `POL`, `POD`, and `SHIP MODE` are normalized into shipment and journey-leg semantics.

**Tech Stack:** Python 3.12, openpyxl, rdflib, pytest

---

## File Structure

### Existing files to modify

- `app/services/graph_types.py`
  - extend canonical types for route/port/timing
- `app/services/graph_normalizer.py`
  - normalize `COE`, `POL`, `POD`, `SHIP MODE`, `ATD`, `ATA`
- `app/services/graph_canonical_builder.py`
  - emit shipment, journey-leg, and milestone triples for the new fields
- `app/services/graph_projection_builder.py`
  - preserve shipment-level convenience mirrors in dashboard node payloads
- `scripts/build_dashboard_graph_data.py`
  - use the shared normalizer output and pass shipment mirrors into projection
- `tests/test_graph_normalizer.py`
  - add route/port/timing normalization regression tests
- `tests/test_graph_canonical_builder.py`
  - add canonical graph triple assertions for route/port/timing
- `tests/test_dashboard_graph_export.py`
  - add exporter assertions for shipment node mirrors

### Generated runtime outputs to refresh

- `kg-dashboard/public/data/nodes.json`
- `kg-dashboard/public/data/edges.json`
- `runtime/audits/hvdc_ttl_source_audit.json`
- `runtime/audits/hvdc_ttl_mapping_audit.json`
- `runtime/audits/hvdc_ttl_projection_audit.json`
- `runtime/audits/hvdc_ttl_resolution_audit.json`

---

### Task 1: Extend shared canonical types for shipment route and timing

**Files:**
- Modify: `app/services/graph_types.py`
- Modify: `tests/test_graph_normalizer.py`
- Test: `tests/test_graph_normalizer.py`

- [ ] **Step 1: Write the failing type-shell test**

Append this test to `tests/test_graph_normalizer.py`:

```python
from app.services.graph_types import (
    CanonicalJourneyLeg,
    CanonicalMilestoneEvent,
    CanonicalShipment,
)


def test_graph_types_expose_route_and_timing_fields():
    shipment = CanonicalShipment(
        id="https://hvdc.logistics/resource/shipment/HVDC-001",
        shipment_no="HVDC-001",
        vendor_name="Vendor A",
        country_of_export="FRANCE",
        port_of_loading="Le Havre",
        port_of_discharge="Mina Zayed",
        ship_mode="SEA",
    )
    leg = CanonicalJourneyLeg(
        id="https://hvdc.logistics/resource/journey-leg/HVDC-001/main",
        shipment_id=shipment.id,
        origin_port_id="https://hvdc.logistics/resource/port/le_havre",
        origin_port_label="Le Havre",
        destination_port_id="https://hvdc.logistics/resource/port/mina_zayed",
        destination_port_label="Mina Zayed",
        transport_mode="SEA",
        actual_departure="2023-11-12",
        actual_arrival="2023-12-01",
    )
    atd = CanonicalMilestoneEvent(
        id="https://hvdc.logistics/resource/milestone/HVDC-001/M61",
        shipment_id=shipment.id,
        milestone_code="M61",
        actual_dt="2023-11-12",
        location_id=leg.origin_port_id,
    )
    ata = CanonicalMilestoneEvent(
        id="https://hvdc.logistics/resource/milestone/HVDC-001/M80",
        shipment_id=shipment.id,
        milestone_code="M80",
        actual_dt="2023-12-01",
        location_id=leg.destination_port_id,
    )

    assert shipment.country_of_export == "FRANCE"
    assert shipment.port_of_loading == "Le Havre"
    assert shipment.port_of_discharge == "Mina Zayed"
    assert shipment.ship_mode == "SEA"
    assert leg.transport_mode == "SEA"
    assert atd.milestone_code == "M61"
    assert ata.milestone_code == "M80"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py::test_graph_types_expose_route_and_timing_fields -q
```

Expected:

- FAIL because `CanonicalJourneyLeg` and `CanonicalMilestoneEvent` do not exist yet
- or FAIL because `CanonicalShipment` does not expose the new fields

- [ ] **Step 3: Write the minimal shared types**

Update `app/services/graph_types.py` with these additions:

```python
@dataclass(slots=True)
class CanonicalShipment:
    id: str
    shipment_no: str
    vendor_name: str | None = None
    country_of_export: str | None = None
    port_of_loading: str | None = None
    port_of_discharge: str | None = None
    ship_mode: str | None = None
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalJourneyLeg:
    id: str
    shipment_id: str
    origin_port_id: str | None = None
    origin_port_label: str | None = None
    destination_port_id: str | None = None
    destination_port_label: str | None = None
    transport_mode: str | None = None
    actual_departure: str | None = None
    actual_arrival: str | None = None
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalMilestoneEvent:
    id: str
    shipment_id: str
    milestone_code: str
    actual_dt: str
    location_id: str | None = None
    attributes: dict[str, object] = field(default_factory=dict)
```

- [ ] **Step 4: Re-run the type-shell test and verify it passes**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py::test_graph_types_expose_route_and_timing_fields -q
```

Expected:

- PASS

- [ ] **Step 5: Commit the shared type change**

```powershell
git add -- app/services/graph_types.py tests/test_graph_normalizer.py
git commit -m "feat: add route and milestone canonical types"
```

---

### Task 2: Normalize COE/POL/POD/SHIP MODE/ATD/ATA into shipment, leg, and milestone structures

**Files:**
- Modify: `app/services/graph_normalizer.py`
- Modify: `tests/test_graph_normalizer.py`
- Test: `tests/test_graph_normalizer.py`

- [ ] **Step 1: Write the failing normalization test**

Append this test to `tests/test_graph_normalizer.py`:

```python
def test_normalize_sources_maps_route_ports_mode_and_port_timing():
    sources = {
        "shipment_rows": [
            {
                "SCT SHIP NO.": "HVDC-001",
                "VENDOR": "Vendor A",
                "COE": "FRANCE",
                "POL": "Le Havre",
                "POD": "Mina Zayed",
                "SHIP MODE": "Sea Freight",
                "ATD": pd.Timestamp("2023-11-12 00:00:00"),
                "ATA": pd.Timestamp("2023-12-01 00:00:00"),
            }
        ],
        "warehouse_rows": [],
        "jpt_sheets": {},
        "inland_cost_rows": [],
        "analysis_notes": [],
    }

    normalized = normalize_sources(sources)

    shipment = normalized.shipments[0]
    leg = normalized.journey_legs[0]
    milestone_codes = {item.milestone_code for item in normalized.milestone_events}

    assert shipment.country_of_export == "FRANCE"
    assert shipment.port_of_loading == "Le Havre"
    assert shipment.port_of_discharge == "Mina Zayed"
    assert shipment.ship_mode == "SEA"
    assert leg.origin_port_label == "Le Havre"
    assert leg.destination_port_label == "Mina Zayed"
    assert leg.transport_mode == "SEA"
    assert leg.actual_departure == "2023-11-12"
    assert leg.actual_arrival == "2023-12-01"
    assert milestone_codes == {"M61", "M80"}
```

- [ ] **Step 2: Run the targeted normalizer tests to verify they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py -q
```

Expected:

- FAIL because `NormalizedSources` does not expose `journey_legs` / `milestone_events`
- or FAIL because the new route columns are ignored

- [ ] **Step 3: Implement normalization**

Update `app/services/graph_normalizer.py` imports and dataclass:

```python
from app.services.graph_types import (
    CanonicalCase,
    CanonicalEvent,
    CanonicalJourneyLeg,
    CanonicalMilestoneEvent,
    CanonicalShipment,
)


@dataclass(slots=True)
class NormalizedSources:
    shipments: list[CanonicalShipment]
    cases: list[CanonicalCase]
    route_events: list[CanonicalEvent]
    journey_legs: list[CanonicalJourneyLeg]
    milestone_events: list[CanonicalMilestoneEvent]
    document_refs: list[dict[str, Any]]
    status_snapshots: list[dict[str, Any]]
    charge_candidates: list[dict[str, Any]]
```

Add helpers:

```python
def _slug(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _port_id(port_name: str) -> str:
    return f"https://hvdc.logistics/resource/port/{_slug(port_name)}"


def _normalize_transport_mode(value: Any) -> str | None:
    text = _clean_text(value)
    if text is None:
        return None
    normalized = text.strip().upper()
    aliases = {
        "SEA FREIGHT": "SEA",
        "OCEAN": "SEA",
        "OCEAN FREIGHT": "SEA",
        "AIR FREIGHT": "AIR",
        "FLIGHT": "AIR",
        "ROAD": "LAND",
        "TRUCK": "LAND",
        "MULTI": "MULTIMODAL",
    }
    return aliases.get(normalized, normalized)
```

Inside `normalize_sources`, add leg and milestone construction:

```python
    journey_legs: list[CanonicalJourneyLeg] = []
    milestone_events: list[CanonicalMilestoneEvent] = []

    for row in sources.get("shipment_rows", []):
        shipment_no = _clean_text(row.get("SCT SHIP NO."))
        if not shipment_no:
            continue

        country_of_export = _clean_text(row.get("COE"))
        port_of_loading = _clean_text(row.get("POL"))
        port_of_discharge = _clean_text(row.get("POD"))
        ship_mode = _normalize_transport_mode(row.get("SHIP MODE"))
        atd = _clean_text(row.get("ATD"))
        ata = _clean_text(row.get("ATA"))

        shipment_id = _shipment_id(shipment_no)
        shipments.append(
            CanonicalShipment(
                id=shipment_id,
                shipment_no=shipment_no,
                vendor_name=_clean_text(row.get("VENDOR")),
                country_of_export=country_of_export,
                port_of_loading=port_of_loading,
                port_of_discharge=port_of_discharge,
                ship_mode=ship_mode,
            )
        )

        if port_of_loading or port_of_discharge or ship_mode or atd or ata:
            leg_id = f"https://hvdc.logistics/resource/journey-leg/{shipment_no}/main"
            journey_legs.append(
                CanonicalJourneyLeg(
                    id=leg_id,
                    shipment_id=shipment_id,
                    origin_port_id=_port_id(port_of_loading) if port_of_loading else None,
                    origin_port_label=port_of_loading,
                    destination_port_id=_port_id(port_of_discharge) if port_of_discharge else None,
                    destination_port_label=port_of_discharge,
                    transport_mode=ship_mode,
                    actual_departure=atd,
                    actual_arrival=ata,
                )
            )
            if atd:
                milestone_events.append(
                    CanonicalMilestoneEvent(
                        id=f"https://hvdc.logistics/resource/milestone/{shipment_no}/M61",
                        shipment_id=shipment_id,
                        milestone_code="M61",
                        actual_dt=atd,
                        location_id=_port_id(port_of_loading) if port_of_loading else None,
                    )
                )
            if ata:
                milestone_events.append(
                    CanonicalMilestoneEvent(
                        id=f"https://hvdc.logistics/resource/milestone/{shipment_no}/M80",
                        shipment_id=shipment_id,
                        milestone_code="M80",
                        actual_dt=ata,
                        location_id=_port_id(port_of_discharge) if port_of_discharge else None,
                    )
                )
```

Return the new lists:

```python
    return NormalizedSources(
        shipments=shipments,
        cases=cases,
        route_events=route_events,
        journey_legs=journey_legs,
        milestone_events=milestone_events,
        document_refs=document_refs,
        status_snapshots=status_snapshots,
        charge_candidates=charge_candidates,
    )
```

- [ ] **Step 4: Re-run the normalizer tests and verify they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py -q
```

Expected:

- PASS for the new route/port/timing test
- existing normalizer tests still PASS

- [ ] **Step 5: Commit the normalization change**

```powershell
git add -- app/services/graph_normalizer.py tests/test_graph_normalizer.py
git commit -m "feat: normalize shipment route and port timing fields"
```

---

### Task 3: Emit canonical graph triples for shipment route, journey legs, and milestone timing

**Files:**
- Modify: `app/services/graph_canonical_builder.py`
- Modify: `tests/test_graph_canonical_builder.py`
- Test: `tests/test_graph_canonical_builder.py`

- [ ] **Step 1: Write the failing canonical graph test**

Append this test to `tests/test_graph_canonical_builder.py`:

```python
from rdflib import Literal, Namespace, URIRef


def test_build_canonical_graph_emits_route_leg_and_milestone_triples():
    shipment_id = URIRef("https://hvdc.logistics/resource/shipment/HVDC-001")
    leg_id = URIRef("https://hvdc.logistics/resource/journey-leg/HVDC-001/main")
    pol_id = URIRef("https://hvdc.logistics/resource/port/le_havre")
    pod_id = URIRef("https://hvdc.logistics/resource/port/mina_zayed")
    atd_id = URIRef("https://hvdc.logistics/resource/milestone/HVDC-001/M61")
    ata_id = URIRef("https://hvdc.logistics/resource/milestone/HVDC-001/M80")

    graph = build_canonical_graph(
        shipments=[
            {
                "id": shipment_id,
                "country_of_export": "FRANCE",
                "port_of_loading": "Le Havre",
                "port_of_discharge": "Mina Zayed",
                "ship_mode": "SEA",
                "deterministic_id": "shipment:HVDC-001",
            }
        ],
        journey_legs=[
            {
                "id": leg_id,
                "shipment_id": shipment_id,
                "origin_port_id": pol_id,
                "origin_port_label": "Le Havre",
                "destination_port_id": pod_id,
                "destination_port_label": "Mina Zayed",
                "transport_mode": "SEA",
                "actual_departure": "2023-11-12",
                "actual_arrival": "2023-12-01",
                "deterministic_id": "leg:HVDC-001:main",
            }
        ],
        milestone_events=[
            {
                "id": atd_id,
                "shipment_id": shipment_id,
                "milestone_code": "M61",
                "actual_dt": "2023-11-12",
                "location_id": pol_id,
                "deterministic_id": "milestone:HVDC-001:M61",
            },
            {
                "id": ata_id,
                "shipment_id": shipment_id,
                "milestone_code": "M80",
                "actual_dt": "2023-12-01",
                "location_id": pod_id,
                "deterministic_id": "milestone:HVDC-001:M80",
            },
        ],
    )

    hvdc = Namespace("http://hvdc.logistics/ontology/")
    assert (shipment_id, hvdc.countryOfExport, Literal("FRANCE")) in graph
    assert (shipment_id, hvdc.portOfLoading, Literal("Le Havre")) in graph
    assert (shipment_id, hvdc.portOfDischarge, Literal("Mina Zayed")) in graph
    assert (shipment_id, hvdc.shipMode, Literal("SEA")) in graph
    assert (shipment_id, hvdc.hasJourneyLeg, leg_id) in graph
    assert (leg_id, hvdc.originPort, pol_id) in graph
    assert (leg_id, hvdc.destinationPort, pod_id) in graph
    assert (leg_id, hvdc.transportMode, Literal("SEA")) in graph
    assert (shipment_id, hvdc.hasMilestone, atd_id) in graph
    assert (shipment_id, hvdc.hasMilestone, ata_id) in graph
    assert (atd_id, hvdc.milestoneCode, Literal("M61")) in graph
    assert (ata_id, hvdc.milestoneCode, Literal("M80")) in graph
```

- [ ] **Step 2: Run the canonical builder tests and verify they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_graph_canonical_builder.py -q
```

Expected:

- FAIL because `journey_legs` and `milestone_events` buckets are not supported yet
- or FAIL because shipment route literals are not emitted

- [ ] **Step 3: Implement canonical graph support**

Update `_TYPE_BY_BUCKET` in `app/services/graph_canonical_builder.py`:

```python
    "journey_legs": HVDC.JourneyLeg,
    "milestone_events": HVDC.MilestoneEvent,
```

Add a helper:

```python
def _add_literal_if_present(graph: Graph, subject: URIRef, predicate: URIRef, value: Any) -> None:
    if value is None:
        return
    text = str(value).strip()
    if not text:
        return
    graph.add((subject, predicate, Literal(text)))
```

Extend the shipment bucket:

```python
            if bucket == "shipments":
                _add_literal_if_present(
                    graph, subject, HVDC.countryOfExport, _item_value(item, "country_of_export")
                )
                _add_literal_if_present(
                    graph, subject, HVDC.portOfLoading, _item_value(item, "port_of_loading")
                )
                _add_literal_if_present(
                    graph, subject, HVDC.portOfDischarge, _item_value(item, "port_of_discharge")
                )
                _add_literal_if_present(
                    graph, subject, HVDC.shipMode, _item_value(item, "ship_mode")
                )
```

Add new bucket handling:

```python
            elif bucket == "journey_legs":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasJourneyLeg, subject))
                origin_port_id = _as_uri(_item_value(item, "origin_port_id", "originPortId"))
                destination_port_id = _as_uri(_item_value(item, "destination_port_id", "destinationPortId"))
                if origin_port_id is not None:
                    graph.add((origin_port_id, RDF.type, HVDC.Port))
                    graph.add((subject, HVDC.originPort, origin_port_id))
                    _add_literal_if_present(
                        graph, origin_port_id, RDFS.label, _item_value(item, "origin_port_label", "originPortLabel")
                    )
                if destination_port_id is not None:
                    graph.add((destination_port_id, RDF.type, HVDC.Port))
                    graph.add((subject, HVDC.destinationPort, destination_port_id))
                    _add_literal_if_present(
                        graph, destination_port_id, RDFS.label, _item_value(item, "destination_port_label", "destinationPortLabel")
                    )
                _add_literal_if_present(graph, subject, HVDC.transportMode, _item_value(item, "transport_mode", "transportMode"))
                _add_literal_if_present(graph, subject, HVDC.actualDeparture, _item_value(item, "actual_departure", "actualDeparture"))
                _add_literal_if_present(graph, subject, HVDC.actualArrival, _item_value(item, "actual_arrival", "actualArrival"))
            elif bucket == "milestone_events":
                shipment_id = _as_uri(_item_value(item, "shipment_id", "shipmentId"))
                if shipment_id is not None:
                    graph.add((shipment_id, HVDC.hasMilestone, subject))
                _add_literal_if_present(graph, subject, HVDC.milestoneCode, _item_value(item, "milestone_code", "milestoneCode"))
                _add_literal_if_present(graph, subject, HVDC.actualDt, _item_value(item, "actual_dt", "actualDt"))
                location_id = _as_uri(_item_value(item, "location_id", "locationId"))
                if location_id is not None:
                    graph.add((subject, HVDC.location, location_id))
```

- [ ] **Step 4: Re-run the canonical builder tests and verify they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_graph_canonical_builder.py -q
```

Expected:

- PASS for the new route/leg/milestone test
- existing canonical builder tests still PASS

- [ ] **Step 5: Commit the canonical graph change**

```powershell
git add -- app/services/graph_canonical_builder.py tests/test_graph_canonical_builder.py
git commit -m "feat: emit route and milestone triples in canonical graph"
```

---

### Task 4: Wire canonical route and milestone export, then expose shipment-level convenience mirrors

**Files:**
- Modify: `app/services/graph_projection_builder.py`
- Modify: `scripts/build_dashboard_graph_data.py`
- Modify: `tests/test_dashboard_graph_export.py`
- Test: `tests/test_dashboard_graph_export.py`

- [ ] **Step 1: Write the failing exporter integration tests**

Append these tests to `tests/test_dashboard_graph_export.py`:

```python
from rdflib import Graph, Literal, Namespace, URIRef
from openpyxl import Workbook


def test_export_dashboard_graph_data_wires_route_leg_and_milestone_data_into_ttl(
    tmp_path: Path,
):
    excel_path = tmp_path / "hvdc_status.xlsx"
    output_dir = tmp_path / "out"
    ttl_path = tmp_path / "knowledge_graph.ttl"

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(
        [
            "SCT SHIP NO.",
            "PO No.",
            "VENDOR",
            "VESSEL NAME/ FLIGHT No.",
            "COE",
            "POL",
            "POD",
            "SHIP MODE",
            "ATD",
            "ATA",
        ]
    )
    worksheet.append(
        [
            "SHIP-001",
            "PO-001",
            "Vendor A",
            "Vessel A",
            "FRANCE",
            "Le Havre",
            "Mina Zayed",
            "SEA",
            "2023-11-12",
            "2023-12-01",
        ]
    )
    workbook.save(excel_path)

    export_dashboard_graph_data(
        excel_path=excel_path,
        wiki_dir=tmp_path / "missing-analyses",
        output_dir=output_dir,
        ttl_path=ttl_path,
    )

    graph = Graph()
    graph.parse(ttl_path, format="turtle")
    hvdc = Namespace("http://hvdc.logistics/ontology/")

    shipment_id = URIRef("https://hvdc.logistics/resource/shipment/SHIP-001")
    leg_id = URIRef("https://hvdc.logistics/resource/journey-leg/SHIP-001/main")
    pol_id = URIRef("https://hvdc.logistics/resource/port/le_havre")
    pod_id = URIRef("https://hvdc.logistics/resource/port/mina_zayed")
    atd_id = URIRef("https://hvdc.logistics/resource/milestone/SHIP-001/M61")
    ata_id = URIRef("https://hvdc.logistics/resource/milestone/SHIP-001/M80")

    assert (shipment_id, hvdc.countryOfExport, Literal("FRANCE")) in graph
    assert (shipment_id, hvdc.portOfLoading, Literal("Le Havre")) in graph
    assert (shipment_id, hvdc.portOfDischarge, Literal("Mina Zayed")) in graph
    assert (shipment_id, hvdc.shipMode, Literal("SEA")) in graph
    assert (shipment_id, hvdc.hasJourneyLeg, leg_id) in graph
    assert (leg_id, hvdc.originPort, pol_id) in graph
    assert (leg_id, hvdc.destinationPort, pod_id) in graph
    assert (shipment_id, hvdc.hasMilestone, atd_id) in graph
    assert (shipment_id, hvdc.hasMilestone, ata_id) in graph
```

```python
def test_export_dashboard_graph_data_exposes_route_and_timing_mirrors_on_shipment_node(
    tmp_path: Path,
):
    excel_path = tmp_path / "hvdc_status.xlsx"
    output_dir = tmp_path / "out"

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(
        [
            "SCT SHIP NO.",
            "PO No.",
            "VENDOR",
            "VESSEL NAME/ FLIGHT No.",
            "COE",
            "POL",
            "POD",
            "SHIP MODE",
            "ATD",
            "ATA",
        ]
    )
    worksheet.append(
        [
            "SHIP-001",
            "PO-001",
            "Vendor A",
            "Vessel A",
            "FRANCE",
            "Le Havre",
            "Mina Zayed",
            "SEA",
            "2023-11-12",
            "2023-12-01",
        ]
    )
    workbook.save(excel_path)

    export_dashboard_graph_data(
        excel_path=excel_path,
        wiki_dir=tmp_path / "missing-analyses",
        output_dir=output_dir,
        ttl_path=None,
    )

    nodes = json.loads((output_dir / "nodes.json").read_text(encoding="utf-8"))
    shipment = next(node["data"] for node in nodes if node["data"]["type"] == "Shipment")

    assert shipment["countryOfExport"] == "FRANCE"
    assert shipment["portOfLoading"] == "Le Havre"
    assert shipment["portOfDischarge"] == "Mina Zayed"
    assert shipment["shipMode"] == "SEA"
    assert shipment["actualDeparture"] == "2023-11-12"
    assert shipment["actualArrival"] == "2023-12-01"
```

- [ ] **Step 2: Run the exporter tests and verify they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py -q
```

Expected:

- FAIL because the canonical TTL export does not yet receive `journey_legs` / `milestone_events`
- or FAIL because shipment nodes do not yet expose the new mirror fields

- [ ] **Step 3: Implement canonical export wiring and projection mirrors**

In `scripts/build_dashboard_graph_data.py`, first wire the new route and timing
fields into the canonical graph call:

```python
    canonical_graph = build_canonical_graph(
        shipments=[
            {
                "id": _safe_uri(shipment.id),
                "shipment_no": shipment.shipment_no,
                "vendor_name": shipment.vendor_name,
                "country_of_export": shipment.country_of_export,
                "port_of_loading": shipment.port_of_loading,
                "port_of_discharge": shipment.port_of_discharge,
                "ship_mode": shipment.ship_mode,
            }
            for shipment in normalized.shipments
        ],
        cases=[
            {
                "id": _safe_uri(case.id),
                "shipment_id": _safe_uri(case.shipment_id),
                "case_no": case.case_no,
            }
            for case in normalized.cases
        ],
        journey_legs=[
            {
                "id": _safe_uri(leg.id),
                "shipment_id": _safe_uri(leg.shipment_id),
                "origin_port_id": _safe_uri(leg.origin_port_id),
                "origin_port_label": leg.origin_port_label,
                "destination_port_id": _safe_uri(leg.destination_port_id),
                "destination_port_label": leg.destination_port_label,
                "transport_mode": leg.transport_mode,
                "actual_departure": leg.actual_departure,
                "actual_arrival": leg.actual_arrival,
            }
            for leg in normalized.journey_legs
        ],
        milestone_events=[
            {
                "id": _safe_uri(event.id),
                "shipment_id": _safe_uri(event.shipment_id),
                "milestone_code": event.milestone_code,
                "actual_dt": event.actual_dt,
                "location_id": _safe_uri(event.location_id),
            }
            for event in normalized.milestone_events
        ],
        events=[
            {
                "id": _safe_uri(event.id),
                "event_type": event.event_type,
                "subject_id": _safe_uri(event.subject_id),
                "location_id": _safe_uri(event.location_id),
                "event_date": event.event_date,
            }
            for event in normalized.route_events
        ],
        lessons=[
            {
                **lesson,
                "id": _safe_uri(lesson.get("id")),
                "shipment_id": _safe_uri(lesson.get("shipment_id")),
                "location_id": _safe_uri(lesson.get("location_id")),
                "carrier_id": _safe_uri(lesson.get("carrier_id")),
                "pattern_id": _safe_uri(lesson.get("pattern_id")),
            }
            for lesson in canonical_lessons
        ],
    )
```

In `app/services/graph_projection_builder.py`, pass shipment extras through:

```python
        _upsert_node(
            nodes,
            shipment_id,
            shipment_label,
            shipment_type,
            countryOfExport=_coerce_text(shipment, "country_of_export", "countryOfExport"),
            portOfLoading=_coerce_text(shipment, "port_of_loading", "portOfLoading"),
            portOfDischarge=_coerce_text(shipment, "port_of_discharge", "portOfDischarge"),
            shipMode=_coerce_text(shipment, "ship_mode", "shipMode"),
            actualDeparture=_coerce_text(shipment, "actual_departure", "actualDeparture"),
            actualArrival=_coerce_text(shipment, "actual_arrival", "actualArrival"),
        )
```

In `scripts/build_dashboard_graph_data.py`, import and use the shared normalizer:

```python
from app.services.graph_normalizer import normalize_sources
```

Replace the current normalization call so the script uses the shared service:

```python
    normalized = normalize_sources(
        {
            "shipment_rows": sources.shipment_rows,
            "warehouse_rows": sources.warehouse_rows,
            "jpt_sheets": sources.jpt_sheets,
            "inland_cost_rows": sources.inland_cost_rows,
            "analysis_notes": sources.analysis_notes,
        }
    )
```

Update shipment projection input:

```python
    shipments = [
        {
            "id": _legacy_dashboard_id(shipment.id),
            "label": shipment.shipment_no,
            "type": "Shipment",
            "country_of_export": shipment.country_of_export,
            "port_of_loading": shipment.port_of_loading,
            "port_of_discharge": shipment.port_of_discharge,
            "ship_mode": shipment.ship_mode,
            "actual_departure": (
                next(
                    (
                        event.actual_dt
                        for event in normalized.milestone_events
                        if event.shipment_id == shipment.id and event.milestone_code == "M61"
                    ),
                    None,
                )
            ),
            "actual_arrival": (
                next(
                    (
                        event.actual_dt
                        for event in normalized.milestone_events
                        if event.shipment_id == shipment.id and event.milestone_code == "M80"
                    ),
                    None,
                )
            ),
        }
        for shipment in normalized.shipments
    ]
```

- [ ] **Step 4: Re-run exporter tests and verify they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py -q
```

Expected:

- PASS for the new canonical TTL wiring test
- PASS for the new shipment-node mirror test
- existing dashboard export tests still PASS

- [ ] **Step 5: Regenerate artifacts, run final checks, and commit**

Run:

```powershell
.venv\Scripts\python.exe scripts/build_dashboard_graph_data.py
.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py tests/test_graph_canonical_builder.py tests/test_dashboard_graph_export.py -q
```

Expected:

- `kg-dashboard/public/data/nodes.json` updated
- `kg-dashboard/public/data/edges.json` updated
- all targeted tests PASS

Commit:

```powershell
git add -- app/services/graph_types.py app/services/graph_normalizer.py app/services/graph_canonical_builder.py app/services/graph_projection_builder.py scripts/build_dashboard_graph_data.py tests/test_graph_normalizer.py tests/test_graph_canonical_builder.py tests/test_dashboard_graph_export.py kg-dashboard/public/data/nodes.json kg-dashboard/public/data/edges.json runtime/audits/hvdc_ttl_source_audit.json runtime/audits/hvdc_ttl_mapping_audit.json runtime/audits/hvdc_ttl_projection_audit.json runtime/audits/hvdc_ttl_resolution_audit.json
git commit -m "feat: align shipment route and port timing fields"
```

---

## Self-Review

### Spec coverage

- `COE` shipment ownership: Task 2 and Task 3
- `POL` / `POD` leg ownership: Task 2 and Task 3
- `SHIP MODE` leg ownership: Task 2 and Task 3
- `SHIP MODE` controlled vocabulary normalization: Task 2
- `ATD` / `ATA` milestone ownership: Task 2 and Task 3
- canonical exporter wiring for `journey_legs` and `milestone_events`: Task 4
- shipment-level mirrors only as convenience fields: Task 4
- no canonical `POD` shortcut property collision: Task 3

### Placeholder scan

- No `TODO`
- No `TBD`
- No “write tests for the above” placeholders
- Every code-changing step includes concrete code

### Type consistency

- `CanonicalJourneyLeg`
- `CanonicalMilestoneEvent`
- shipment mirror keys in dashboard export:
  - `countryOfExport`
  - `portOfLoading`
  - `portOfDischarge`
  - `shipMode`
  - `actualDeparture`
  - `actualArrival`
- canonical graph predicates:
  - `countryOfExport`
  - `portOfLoading`
  - `portOfDischarge`
  - `hasJourneyLeg`
  - `originPort`
  - `destinationPort`
  - `transportMode`
  - `hasMilestone`
  - `milestoneCode`
  - `actualDt`

---

Plan complete and saved to `docs/superpowers/plans/2026-04-12-shipment-route-and-port-timing-alignment-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

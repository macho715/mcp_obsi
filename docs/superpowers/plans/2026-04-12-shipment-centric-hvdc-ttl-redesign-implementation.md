# Shipment-Centric HVDC TTL Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new shipment-centric TTL generation pipeline from the approved spec, using four Excel workbooks plus `wiki/analyses` knowledge inputs, and regenerate dashboard graph artifacts from the canonical model.

**Architecture:** The implementation replaces the current ad hoc exporter with a staged pipeline: source loading -> normalization -> resolver -> canonical graph build -> projection build -> validation and audit output. `scripts/build_dashboard_graph_data.py` remains the single entrypoint, while legacy scripts stay as wrappers. The dashboard keeps reading `kg-dashboard/public/data/nodes.json` and `edges.json`.

**Tech Stack:** Python 3.12, pandas, PyYAML, rdflib, pytest, ruff, Vite dashboard smoke checks

**Spec:** `docs/superpowers/specs/2026-04-12-shipment-centric-hvdc-ttl-redesign-design.md`

---

## File Map

### New files

- `app/services/graph_types.py`
- `app/services/graph_source_loader.py`
- `app/services/graph_normalizer.py`
- `app/services/graph_resolver.py`
- `app/services/graph_knowledge_builder.py`
- `app/services/graph_canonical_builder.py`
- `app/services/graph_mapping_builder.py`
- `app/services/graph_projection_builder.py`
- `app/services/graph_validation.py`
- `tests/test_graph_source_loader.py`
- `tests/test_graph_normalizer.py`
- `tests/test_graph_resolver.py`
- `tests/test_graph_knowledge_builder.py`
- `tests/test_graph_canonical_builder.py`
- `tests/test_graph_mapping_builder.py`
- `tests/test_graph_projection_builder.py`
- `tests/test_graph_validation.py`
- `docs/superpowers/plans/2026-04-12-shipment-centric-hvdc-ttl-redesign-implementation.md`

### Existing files to modify

- `scripts/build_dashboard_graph_data.py`
- `scripts/build_knowledge_graph.py`
- `scripts/ttl_to_json.py`
- `README.md`
- `tests/test_dashboard_graph_export.py`
- `tests/test_ttl_to_json.py`
- `kg-dashboard/public/data/nodes.json`
- `kg-dashboard/public/data/edges.json`

### Generated runtime outputs

- `runtime/audits/hvdc_ttl_source_audit.json`
- `runtime/audits/hvdc_ttl_resolution_audit.json`
- `runtime/audits/hvdc_ttl_projection_audit.json`
- `runtime/audits/hvdc_ttl_mapping_audit.json`
- `vault/knowledge_graph.ttl`

---

## Task 1: Create Shared Graph Types

**Files:**
- Create: `app/services/graph_types.py`
- Test: `tests/test_graph_normalizer.py`

- [ ] **Step 1: Write the failing test for canonical type shells**

```python
from app.services.graph_types import (
    CanonicalShipment,
    CanonicalCase,
    CanonicalCargoItem,
    CanonicalDocumentRef,
    CanonicalStatusSnapshot,
    CanonicalInvoice,
    CanonicalChargeSummary,
    CanonicalSettlementRecord,
    CanonicalReconciliationRecord,
    CanonicalCostAttribution,
    CanonicalEvent,
    ResolutionDecision,
)


def test_graph_types_expose_expected_core_fields():
    shipment = CanonicalShipment(
        id="https://hvdc.logistics/resource/shipment/HVDC-001",
        shipment_no="HVDC-001",
        vendor_name="Vendor A",
    )
    case = CanonicalCase(
        id="https://hvdc.logistics/resource/case/HVDC-001/CASE-01",
        shipment_id=shipment.id,
        case_no="CASE-01",
    )
    cargo_item = CanonicalCargoItem(
        id="https://hvdc.logistics/resource/cargo/HVDC-001/CASE-01/PKG-01",
        shipment_id=shipment.id,
        case_id=case.id,
        item_ref="PKG-01",
    )
    document_ref = CanonicalDocumentRef(
        id="https://hvdc.logistics/resource/doc/bl/BL-001",
        shipment_id=shipment.id,
        document_type="BL",
        document_ref="BL-001",
    )
    snapshot = CanonicalStatusSnapshot(
        id="https://hvdc.logistics/resource/status/HVDC-001/current",
        shipment_id=shipment.id,
        status="InTransit",
    )
    invoice = CanonicalInvoice(
        id="https://hvdc.logistics/resource/invoice/INV-001",
        invoice_no="INV-001",
        shipment_id=shipment.id,
    )
    charge = CanonicalChargeSummary(
        id="https://hvdc.logistics/resource/charge/INV-001/storage",
        invoice_id=invoice.id,
        charge_type="Storage",
        amount=120.0,
    )
    settlement = CanonicalSettlementRecord(
        id="https://hvdc.logistics/resource/settlement/INV-001",
        invoice_id=invoice.id,
        status="matched",
    )
    reconciliation = CanonicalReconciliationRecord(
        id="https://hvdc.logistics/resource/recon/V001",
        normalized_voyage_id="V001",
        status="matched",
    )
    cost = CanonicalCostAttribution(
        id="https://hvdc.logistics/resource/cost/INV-001/storage",
        invoice_id=invoice.id,
        shipment_id=shipment.id,
        event_id="https://hvdc.logistics/resource/storage/HVDC-001/dsv_indoor/2025-01-02",
    )
    decision = ResolutionDecision(
        status="resolved",
        source_value="Jopetwil 71",
        target_id="https://hvdc.logistics/resource/carrier/jopetwil_71",
        target_type="OperationCarrier",
    )
    event = CanonicalEvent(
        id="https://hvdc.logistics/resource/arrival/HVDC-001/agi/2025-01-01",
        event_type="ArrivalEvent",
        subject_id=shipment.id,
        location_id="https://hvdc.logistics/resource/site/agi",
        event_date="2025-01-01",
    )

    assert shipment.shipment_no == "HVDC-001"
    assert case.shipment_id == shipment.id
    assert cargo_item.case_id == case.id
    assert document_ref.document_type == "BL"
    assert snapshot.status == "InTransit"
    assert charge.charge_type == "Storage"
    assert settlement.invoice_id == invoice.id
    assert reconciliation.normalized_voyage_id == "V001"
    assert cost.shipment_id == shipment.id
    assert decision.status == "resolved"
    assert event.event_type == "ArrivalEvent"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py::test_graph_types_expose_expected_core_fields -q`

Expected: `ModuleNotFoundError` or import failure for `app.services.graph_types`

- [ ] **Step 3: Write minimal shared types**

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class CanonicalShipment:
    id: str
    shipment_no: str
    vendor_name: str | None = None
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalCase:
    id: str
    shipment_id: str
    case_no: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalCargoItem:
    id: str
    shipment_id: str
    case_id: str
    item_ref: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalDocumentRef:
    id: str
    shipment_id: str
    document_type: str
    document_ref: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalStatusSnapshot:
    id: str
    shipment_id: str
    status: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalInvoice:
    id: str
    invoice_no: str
    shipment_id: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalChargeSummary:
    id: str
    invoice_id: str
    charge_type: str
    amount: float
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalSettlementRecord:
    id: str
    invoice_id: str
    status: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalReconciliationRecord:
    id: str
    normalized_voyage_id: str
    status: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalCostAttribution:
    id: str
    invoice_id: str
    shipment_id: str
    event_id: str | None = None
    location_id: str | None = None
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalEvent:
    id: str
    event_type: str
    subject_id: str
    location_id: str | None
    event_date: str
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ResolutionDecision:
    status: str
    source_value: str
    target_id: str | None
    target_type: str | None
    reason: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py::test_graph_types_expose_expected_core_fields -q`

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add app/services/graph_types.py tests/test_graph_normalizer.py
git commit -m "feat: add shared canonical graph types"
```

---

## Task 2: Load Four Excel Sources and Analyses Notes

**Files:**
- Create: `app/services/graph_source_loader.py`
- Create: `tests/test_graph_source_loader.py`
- Modify: `app/services/graph_types.py`

- [ ] **Step 1: Write the failing tests for source loading**

```python
from pathlib import Path

import pandas as pd

from app.services.graph_source_loader import load_graph_sources


def test_load_graph_sources_reads_required_tabs_and_markdown(tmp_path: Path):
    hvdc_status = tmp_path / "HVDC STATUS.xlsx"
    warehouse_status = tmp_path / "HVDC WAREHOUSE STATUS.xlsx"
    jpt = tmp_path / "JPT-reconciled_v6.0.xlsx"
    inland = tmp_path / "HVDC Logistics cost(inland,domestic).xlsx"
    analyses = tmp_path / "analyses"
    analyses.mkdir()

    pd.DataFrame([{"SCT SHIP NO.": "HVDC-001"}]).to_excel(hvdc_status, index=False)
    pd.DataFrame([{"SCT SHIP NO.": "HVDC-001", "Case No.": "CASE-01"}]).to_excel(warehouse_status, index=False)
    with pd.ExcelWriter(jpt) as writer:
        pd.DataFrame([{"Vessel": "JOPETWIL 71"}]).to_excel(writer, sheet_name="1_Decklog", index=False)
        pd.DataFrame([{"Voyage No": "V001"}]).to_excel(writer, sheet_name="3_Voyage_Master", index=False)
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(writer, sheet_name="4_Voyage_Rollup", index=False)
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(writer, sheet_name="6_Reconciliation", index=False)
        pd.DataFrame([{"Normalized Voyage ID": "V001"}]).to_excel(writer, sheet_name="7_Exceptions", index=False)
        pd.DataFrame([{"Normalized Invoice Number": "INV-1"}]).to_excel(writer, sheet_name="8_Decklog_Context", index=False)
    pd.DataFrame([{"Invoice No": "INV-001", "Shipment No": "HVDC-001"}]).to_excel(inland, index=False)
    (analyses / "guideline_jopetwil_71_group.md").write_text(
        "---\ntitle: Guide\nslug: guideline_jopetwil_71_group\n---\ncontent",
        encoding="utf-8",
    )

    sources = load_graph_sources(
        hvdc_status_path=hvdc_status,
        warehouse_status_path=warehouse_status,
        jpt_reconciled_path=jpt,
        inland_cost_path=inland,
        analyses_dir=analyses,
    )

    assert len(sources.shipment_rows) == 1
    assert len(sources.warehouse_rows) == 1
    assert "1_Decklog" in sources.jpt_sheets
    assert len(sources.analysis_notes) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_source_loader.py::test_load_graph_sources_reads_required_tabs_and_markdown -q`

Expected: import failure for `app.services.graph_source_loader`

- [ ] **Step 3: Implement source loader**

```python
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml


REQUIRED_JPT_SHEETS = [
    "1_Decklog",
    "3_Voyage_Master",
    "4_Voyage_Rollup",
    "6_Reconciliation",
    "7_Exceptions",
    "8_Decklog_Context",
]


@dataclass(slots=True)
class LoadedGraphSources:
    shipment_rows: list[dict[str, object]]
    warehouse_rows: list[dict[str, object]]
    jpt_sheets: dict[str, list[dict[str, object]]]
    inland_cost_rows: list[dict[str, object]]
    analysis_notes: list[dict[str, object]]


def _read_markdown_note(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    frontmatter = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
    return {"path": str(path), "frontmatter": frontmatter, "body": text}


def load_graph_sources(
    hvdc_status_path: Path,
    warehouse_status_path: Path,
    jpt_reconciled_path: Path,
    inland_cost_path: Path,
    analyses_dir: Path,
) -> LoadedGraphSources:
    shipment_rows = pd.read_excel(hvdc_status_path).to_dict("records")
    warehouse_rows = pd.read_excel(warehouse_status_path).to_dict("records")
    jpt_excel = pd.ExcelFile(jpt_reconciled_path)
    missing = [sheet for sheet in REQUIRED_JPT_SHEETS if sheet not in jpt_excel.sheet_names]
    if missing:
        raise ValueError(f"Missing required JPT sheets: {', '.join(missing)}")
    jpt_sheets = {
        sheet: pd.read_excel(jpt_reconciled_path, sheet_name=sheet).to_dict("records")
        for sheet in REQUIRED_JPT_SHEETS
    }
    inland_cost_rows = pd.read_excel(inland_cost_path).to_dict("records")
    analysis_notes = [_read_markdown_note(path) for path in sorted(analyses_dir.glob("*.md"))]
    return LoadedGraphSources(
        shipment_rows=shipment_rows,
        warehouse_rows=warehouse_rows,
        jpt_sheets=jpt_sheets,
        inland_cost_rows=inland_cost_rows,
        analysis_notes=analysis_notes,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_source_loader.py -q`

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add app/services/graph_source_loader.py tests/test_graph_source_loader.py app/services/graph_types.py
git commit -m "feat: add graph source loader for excel and analyses inputs"
```

---

## Task 3: Normalize Rows into Canonical Shipment, Case, and Cost Candidates

**Files:**
- Create: `app/services/graph_normalizer.py`
- Modify: `app/services/graph_types.py`
- Create: `tests/test_graph_normalizer.py`

- [ ] **Step 1: Write the failing tests for normalization**

```python
from app.services.graph_normalizer import normalize_sources


def test_normalize_sources_creates_shipment_case_and_cost_candidates():
    sources = {
        "shipment_rows": [{
            "SCT SHIP NO.": "HVDC-001",
            "COMMERCIAL INVOICE No.": "CI-001",
            "VENDOR": "Vendor A",
            "MOSB": "2025-01-01",
            "AGI": "2025-01-03",
        }],
        "warehouse_rows": [{
            "SCT SHIP NO.": "HVDC-001",
            "Case No.": "CASE-01",
            "Storage": "DSV Indoor",
            "ETA/ATA": "2025-01-02",
        }],
        "jpt_sheets": {"1_Decklog": [], "3_Voyage_Master": [], "4_Voyage_Rollup": [], "6_Reconciliation": [], "7_Exceptions": [], "8_Decklog_Context": []},
        "inland_cost_rows": [{
            "Invoice No": "INV-001",
            "Shipment No": "HVDC-001",
            "Storage": 120.0,
        }],
        "analysis_notes": [],
    }

    normalized = normalize_sources(sources)

    assert normalized.shipments[0].shipment_no == "HVDC-001"
    assert normalized.cases[0].case_no == "CASE-01"
    assert normalized.route_events[0].event_type == "ArrivalEvent"
    assert normalized.document_refs[0]["document_ref"] == "CI-001"
    assert normalized.status_snapshots[0]["shipment_id"].endswith("/shipment/HVDC-001")
    assert normalized.charge_candidates[0]["invoice_no"] == "INV-001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py::test_normalize_sources_creates_shipment_case_and_cost_candidates -q`

Expected: import failure for `app.services.graph_normalizer`

- [ ] **Step 3: Implement normalizer**

```python
def normalize_sources(sources):
    shipments = []
    cases = []
    route_events = []
    document_refs = []
    status_snapshots = []
    charge_candidates = []

    for row in sources["shipment_rows"]:
        shipment_no = str(row.get("SCT SHIP NO.", "")).strip()
        if not shipment_no:
            continue
        shipment_id = f"https://hvdc.logistics/resource/shipment/{shipment_no}"
        shipments.append(
            CanonicalShipment(
                id=shipment_id,
                shipment_no=shipment_no,
                vendor_name=str(row.get("VENDOR", "")).strip() or None,
            )
        )
        for location_field, location_slug in (("MOSB", "mosb"), ("AGI", "agi"), ("DAS", "das"), ("MIR", "mir"), ("SHU", "shu")):
            value = str(row.get(location_field, "")).strip()
            if value:
                route_events.append(
                    CanonicalEvent(
                        id=f"https://hvdc.logistics/resource/arrival/{shipment_no}/{location_slug}/{value}",
                        event_type="ArrivalEvent",
                        subject_id=shipment_id,
                        location_id=f"https://hvdc.logistics/resource/site/{location_slug}",
                        event_date=value,
                    )
                )
        commercial_invoice = str(row.get("COMMERCIAL INVOICE No.", "")).strip()
        if commercial_invoice:
            document_refs.append(
                {
                    "id": f"https://hvdc.logistics/resource/doc/ci/{commercial_invoice}",
                    "shipment_id": shipment_id,
                    "document_type": "COMMERCIAL_INVOICE",
                    "document_ref": commercial_invoice,
                }
            )
        status_snapshots.append(
            {
                "id": f"https://hvdc.logistics/resource/status/{shipment_no}/current",
                "shipment_id": shipment_id,
                "status": "loaded",
            }
        )

    for row in sources["warehouse_rows"]:
        shipment_no = str(row.get("SCT SHIP NO.", "")).strip()
        case_no = str(row.get("Case No.", "")).strip()
        if shipment_no and case_no:
            cases.append(
                CanonicalCase(
                    id=f"https://hvdc.logistics/resource/case/{shipment_no}/{case_no}",
                    shipment_id=f"https://hvdc.logistics/resource/shipment/{shipment_no}",
                    case_no=case_no,
                )
            )

    for row in sources["inland_cost_rows"]:
        invoice_no = str(row.get("Invoice No", "")).strip()
        shipment_no = str(row.get("Shipment No", "")).strip()
        if invoice_no and shipment_no:
            charge_candidates.append(
                {"invoice_no": invoice_no, "shipment_no": shipment_no, "row": row}
            )

    return type(
        "NormalizedSources",
        (),
        {
            "shipments": shipments,
            "cases": cases,
            "route_events": route_events,
            "document_refs": document_refs,
            "status_snapshots": status_snapshots,
            "charge_candidates": charge_candidates,
        },
    )()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_normalizer.py -q`

Expected: `2 passed` after adding one more ID determinism assertion test in the same file

- [ ] **Step 5: Commit**

```bash
git add app/services/graph_normalizer.py tests/test_graph_normalizer.py app/services/graph_types.py
git commit -m "feat: normalize shipment, case, and charge source rows"
```

---

## Task 4: Resolve Locations, Carriers, Guides, and Lessons

**Files:**
- Create: `app/services/graph_resolver.py`
- Create: `tests/test_graph_resolver.py`

- [ ] **Step 1: Write the failing tests for resolution**

```python
from app.services.graph_resolver import resolve_location, resolve_carrier, resolve_analysis_note


def test_resolve_location_maps_known_operational_aliases():
    decision = resolve_location("West Harbor Jetty #3")
    assert decision.status == "resolved"
    assert decision.target_type == "Jetty"


def test_resolve_location_covers_anchorage_yard_and_gate():
    anchorage = resolve_location("AGI Anchorage")
    yard = resolve_location("VP24 yard")
    gate = resolve_location("CICPA gate")
    assert anchorage.target_type == "AnchorageArea"
    assert yard.target_type == "YardArea"
    assert gate.target_type == "GateArea"


def test_resolve_carrier_maps_jopetwil_to_operation_carrier():
    decision = resolve_carrier("JOPETWIL 71")
    assert decision.status == "resolved"
    assert decision.target_id.endswith("/carrier/jopetwil_71")


def test_resolve_analysis_note_maps_guides_and_incidents():
    guide = resolve_analysis_note(
        {
            "path": "guideline_jopetwil_71_group.md",
            "frontmatter": {"slug": "guideline_jopetwil_71_group"},
            "body": "guide body",
        }
    )
    incident = resolve_analysis_note(
        {
            "path": "logistics_issue_jpt71_2024-12-23_3.md",
            "frontmatter": {"slug": "logistics_issue_jpt71_2024-12-23_3"},
            "body": "incident body",
        }
    )
    assert guide["class_name"] == "GroupGuide"
    assert incident["class_name"] == "IncidentLesson"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_resolver.py -q`

Expected: import failure for `app.services.graph_resolver`

- [ ] **Step 3: Implement resolver**

```python
LOCATION_ALIASES = {
    "west harbor jetty #3": ("Jetty", "https://hvdc.logistics/resource/oploc/agi/west_harbor_jetty_3"),
    "mosb": ("HubLocation", "https://hvdc.logistics/resource/hub/mosb"),
    "mw4 jetty": ("Jetty", "https://hvdc.logistics/resource/oploc/mw4/mw4_jetty"),
    "agi anchorage": ("AnchorageArea", "https://hvdc.logistics/resource/oploc/agi/anchorage"),
    "vp24 yard": ("YardArea", "https://hvdc.logistics/resource/oploc/abu_dhabi/vp24_yard"),
    "cicpa gate": ("GateArea", "https://hvdc.logistics/resource/oploc/mir/cicpa_gate"),
}

CARRIER_ALIASES = {
    "jopetwil 71": "https://hvdc.logistics/resource/carrier/jopetwil_71",
    "jpt71": "https://hvdc.logistics/resource/carrier/jopetwil_71",
}


def resolve_location(value: str) -> ResolutionDecision:
    key = value.strip().lower()
    target = LOCATION_ALIASES.get(key)
    if target:
        target_type, target_id = target
        return ResolutionDecision("resolved", value, target_id, target_type)
    return ResolutionDecision("unresolved", value, None, None, "location alias missing")


def resolve_carrier(value: str) -> ResolutionDecision:
    key = value.strip().lower()
    target_id = CARRIER_ALIASES.get(key)
    if target_id:
        return ResolutionDecision("resolved", value, target_id, "OperationCarrier")
    return ResolutionDecision("unresolved", value, None, None, "carrier alias missing")


def resolve_analysis_note(note: dict[str, object]) -> dict[str, object]:
    path = str(note["path"]).lower()
    if "guideline_" in path:
        return {"class_name": "GroupGuide", "slug": note["frontmatter"].get("slug")}
    return {"class_name": "IncidentLesson", "slug": note["frontmatter"].get("slug")}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_resolver.py -q`

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add app/services/graph_resolver.py tests/test_graph_resolver.py
git commit -m "feat: resolve locations, carriers, guides, and incident notes"
```

---

## Task 5: Build Knowledge Layer Objects from Analyses Notes

**Files:**
- Create: `app/services/graph_knowledge_builder.py`
- Create: `tests/test_graph_knowledge_builder.py`

- [ ] **Step 1: Write the failing tests for guides, lessons, rules, and recurring patterns**

```python
from app.services.graph_knowledge_builder import build_knowledge_objects


def test_build_knowledge_objects_creates_guide_rule_lesson_and_pattern():
    notes = [
        {
            "path": "guideline_jopetwil_71_group.md",
            "frontmatter": {"slug": "guideline_jopetwil_71_group", "title": "Guide"},
            "body": "07:30 / 16:00 SITREP\nemail SSOT\nhigh tide risk escalation",
        },
        {
            "path": "logistics_issue_jpt71_2024-12-23_3.md",
            "frontmatter": {"slug": "logistics_issue_jpt71_2024-12-23_3", "title": "Delay"},
            "body": "high tide delayed offloading at AGI",
        },
    ]

    knowledge = build_knowledge_objects(notes)

    assert knowledge.guides[0]["class_name"] == "GroupGuide"
    assert knowledge.rules[0]["base_class"] == "OperatingRule"
    assert knowledge.rules[0]["class_name"] == "ReportingRule"
    assert knowledge.lessons[0]["class_name"] == "IncidentLesson"
    assert knowledge.evidence[0]["class_name"] == "CommunicationEvidence"
    assert knowledge.patterns[0]["class_name"] == "RecurringPattern"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_knowledge_builder.py -q`

Expected: import failure for `app.services.graph_knowledge_builder`

- [ ] **Step 3: Implement knowledge builder**

```python
from dataclasses import dataclass


@dataclass(slots=True)
class BuiltKnowledge:
    guides: list[dict[str, object]]
    rules: list[dict[str, object]]
    lessons: list[dict[str, object]]
    evidence: list[dict[str, object]]
    patterns: list[dict[str, object]]


def build_knowledge_objects(notes: list[dict[str, object]]) -> BuiltKnowledge:
    guides = []
    rules = []
    lessons = []
    evidence = []
    patterns = []

    for note in notes:
        slug = str(note["frontmatter"].get("slug", ""))
        body = str(note.get("body", ""))
        if slug.startswith("guideline_"):
            guides.append({"class_name": "GroupGuide", "slug": slug})
            if "07:30 / 16:00 SITREP" in body:
                rules.append({"base_class": "OperatingRule", "class_name": "ReportingRule", "guide_slug": slug, "rule_key": "sitrep_window"})
            if "email SSOT" in body:
                rules.append({"base_class": "OperatingRule", "class_name": "DocumentAuthorityRule", "guide_slug": slug, "rule_key": "email_ssot"})
            if "high tide" in body.lower():
                rules.append({"base_class": "OperatingRule", "class_name": "EscalationRule", "guide_slug": slug, "rule_key": "high_tide_escalation"})
        else:
            lessons.append({"class_name": "IncidentLesson", "slug": slug})
            evidence.append({"class_name": "CommunicationEvidence", "slug": slug})
            if "high tide" in body.lower():
                patterns.append({"class_name": "RecurringPattern", "pattern_key": "HighTideDelay"})

    return BuiltKnowledge(
        guides=guides,
        rules=rules,
        lessons=lessons,
        evidence=evidence,
        patterns=patterns,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_knowledge_builder.py -q`

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add app/services/graph_knowledge_builder.py tests/test_graph_knowledge_builder.py
git commit -m "feat: build guides, lessons, rules, and recurring patterns from analyses notes"
```

---

## Task 6: Build Compatibility Mapping, Canonical Graph, and Validation Gates

**Files:**
- Create: `app/services/graph_canonical_builder.py`
- Create: `app/services/graph_mapping_builder.py`
- Create: `app/services/graph_validation.py`
- Create: `tests/test_graph_canonical_builder.py`
- Create: `tests/test_graph_mapping_builder.py`
- Create: `tests/test_graph_validation.py`

- [ ] **Step 1: Write the failing tests for mappings, canonical graph, and audits**

```python
from app.services.graph_canonical_builder import build_canonical_graph
from app.services.graph_mapping_builder import build_compatibility_mappings
from app.services.graph_validation import validate_canonical_graph


def test_build_compatibility_mappings_exposes_consolidated_targets():
    mappings = build_compatibility_mappings()
    assert any(item["new_class"] == "OperationCarrier" for item in mappings)
    assert any(item["legacy_target"].endswith("CONSOLIDATED-04-barge-bulk-cargo.md") for item in mappings)


def test_build_canonical_graph_links_shipments_cases_events_and_lessons():
    graph, audit = build_canonical_graph(
        shipments=[{"id": "https://hvdc.logistics/resource/shipment/HVDC-001", "shipment_no": "HVDC-001"}],
        cases=[{"id": "https://hvdc.logistics/resource/case/HVDC-001/CASE-01", "shipment_id": "https://hvdc.logistics/resource/shipment/HVDC-001"}],
        cargo_items=[{"id": "https://hvdc.logistics/resource/cargo/HVDC-001/CASE-01/PKG-01", "case_id": "https://hvdc.logistics/resource/case/HVDC-001/CASE-01"}],
        document_refs=[{"id": "https://hvdc.logistics/resource/doc/ci/CI-001", "shipment_id": "https://hvdc.logistics/resource/shipment/HVDC-001", "document_ref": "CI-001"}],
        status_snapshots=[{"id": "https://hvdc.logistics/resource/status/HVDC-001/current", "shipment_id": "https://hvdc.logistics/resource/shipment/HVDC-001", "status": "InTransit"}],
        events=[{"id": "https://hvdc.logistics/resource/arrival/HVDC-001/agi/2025-01-01", "event_type": "ArrivalEvent", "subject_id": "https://hvdc.logistics/resource/shipment/HVDC-001", "location_id": "https://hvdc.logistics/resource/site/agi", "event_date": "2025-01-01"}],
        invoices=[{"id": "https://hvdc.logistics/resource/invoice/INV-001", "invoice_no": "INV-001", "shipment_id": "https://hvdc.logistics/resource/shipment/HVDC-001"}],
        charge_summaries=[{"id": "https://hvdc.logistics/resource/charge/INV-001/storage", "invoice_id": "https://hvdc.logistics/resource/invoice/INV-001", "charge_type": "Storage"}],
        settlement_records=[{"id": "https://hvdc.logistics/resource/settlement/INV-001", "invoice_id": "https://hvdc.logistics/resource/invoice/INV-001"}],
        reconciliation_records=[{"id": "https://hvdc.logistics/resource/recon/V001", "normalized_voyage_id": "V001"}],
        cost_attributions=[{"id": "https://hvdc.logistics/resource/cost/INV-001/storage", "invoice_id": "https://hvdc.logistics/resource/invoice/INV-001", "shipment_id": "https://hvdc.logistics/resource/shipment/HVDC-001"}],
        guides=[{"id": "https://hvdc.logistics/resource/guide/guideline_jopetwil_71_group", "rule_ids": ["rule-1"]}],
        rules=[{"id": "rule-1", "rule_type": "ReportingRule"}],
        lessons=[{"id": "https://hvdc.logistics/resource/lesson/project_lightning/2025-01-01/1", "shipment_id": "https://hvdc.logistics/resource/shipment/HVDC-001"}],
        patterns=[{"id": "pattern-1", "pattern_key": "HighTideDelay"}],
        evidence=[{"id": "evidence-1"}],
        mappings=build_compatibility_mappings(),
    )
    assert len(graph) > 0
    assert audit["unresolved_items"] == []
    assert audit["mapping"]["unresolved_compatibility_mappings"] == []


def test_validate_canonical_graph_rejects_event_without_subject():
    result = validate_canonical_graph(
        [{"id": "broken-event", "event_type": "ArrivalEvent", "subject_id": "", "location_id": None, "event_date": "2025-01-01"}]
    )
    assert result["status"] == "fail"
    assert "event_without_subject" in result["errors"][0]


def test_validate_canonical_graph_rejects_duplicate_ids_and_broken_knowledge_links():
    result = validate_canonical_graph(
        events=[{"id": "dup-event", "event_type": "ArrivalEvent", "subject_id": "shipment-1", "location_id": "site-1", "event_date": "2025-01-01"}],
        guides=[{"id": "guide-1", "rules": []}],
        lessons=[{"id": "lesson-1", "shipment_id": "", "location_id": "", "carrier_id": "", "pattern_id": ""}],
        all_ids=["dup-event", "dup-event"],
    )
    assert result["status"] == "fail"
    assert "duplicate_deterministic_ids" in result["errors"]
    assert "guide_without_rule" in result["errors"]
    assert "lesson_without_anchor" in result["errors"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_mapping_builder.py tests/test_graph_canonical_builder.py tests/test_graph_validation.py -q`

Expected: import failure for canonical builder and validation modules

- [ ] **Step 3: Implement mapping builder, canonical builder, and validation**

```python
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

HVDC = Namespace("https://hvdc.logistics/ontology/core/")
HVDCE = Namespace("https://hvdc.logistics/ontology/event/")
HVDCK = Namespace("https://hvdc.logistics/ontology/knowledge/")
HVDCM = Namespace("https://hvdc.logistics/ontology/mapping/")


def build_compatibility_mappings():
    return [
        {
            "new_class": "OperationCarrier",
            "legacy_target": "Logi ontol core doc/CONSOLIDATED-04-barge-bulk-cargo.md#debulk:Vessel",
        },
        {
            "new_class": "IncidentLesson",
            "legacy_target": "Logi ontol core doc/CONSOLIDATED-08-communication.md#AuditRecord",
        },
    ]


def build_canonical_graph(*, shipments, cases, cargo_items, document_refs, status_snapshots, events, invoices, charge_summaries, settlement_records, reconciliation_records, cost_attributions, guides, rules, lessons, patterns, evidence, mappings):
    graph = Graph()
    graph.bind("hvdc", HVDC)
    graph.bind("hvdce", HVDCE)
    graph.bind("hvdck", HVDCK)
    graph.bind("hvdcm", HVDCM)
    audit = {
        "unresolved_items": [],
        "mapping": {"unresolved_compatibility_mappings": []},
    }

    for shipment in shipments:
        shipment_ref = URIRef(shipment["id"])
        graph.add((shipment_ref, RDF.type, HVDC.Shipment))
        graph.add((shipment_ref, HVDC.shipmentNo, Literal(shipment["shipment_no"])))

    for case in cases:
        case_ref = URIRef(case["id"])
        shipment_ref = URIRef(case["shipment_id"])
        graph.add((case_ref, RDF.type, HVDC.Case))
        graph.add((shipment_ref, HVDC.hasCase, case_ref))

    for cargo_item in cargo_items:
        cargo_ref = URIRef(cargo_item["id"])
        case_ref = URIRef(cargo_item["case_id"])
        graph.add((cargo_ref, RDF.type, HVDC.CargoItem))
        graph.add((case_ref, HVDC.containsCargoItem, cargo_ref))

    for document in document_refs:
        document_ref = URIRef(document["id"])
        shipment_ref = URIRef(document["shipment_id"])
        graph.add((document_ref, RDF.type, HVDC.DocumentRef))
        graph.add((shipment_ref, HVDC.hasDocumentRef, document_ref))

    for snapshot in status_snapshots:
        snapshot_ref = URIRef(snapshot["id"])
        shipment_ref = URIRef(snapshot["shipment_id"])
        graph.add((snapshot_ref, RDF.type, HVDC.StatusSnapshot))
        graph.add((shipment_ref, HVDC.hasStatusSnapshot, snapshot_ref))

    for event in events:
        event_ref = URIRef(event["id"])
        subject_ref = URIRef(event["subject_id"])
        graph.add((event_ref, RDF.type, HVDCE[event["event_type"]]))
        graph.add((subject_ref, HVDCE.hasEvent, event_ref))

    for guide in guides:
        guide_ref = URIRef(guide["id"])
        graph.add((guide_ref, RDF.type, HVDCK.GroupGuide))

    for rule in rules:
        rule_ref = URIRef(rule["id"])
        graph.add((rule_ref, RDF.type, HVDCK[rule["rule_type"]]))

    for lesson in lessons:
        lesson_ref = URIRef(lesson["id"])
        shipment_ref = URIRef(lesson["shipment_id"])
        graph.add((lesson_ref, RDF.type, HVDCK.IncidentLesson))
        graph.add((lesson_ref, HVDCK.relatedToShipment, shipment_ref))

    for invoice in invoices:
        invoice_ref = URIRef(invoice["id"])
        shipment_ref = URIRef(invoice["shipment_id"])
        graph.add((invoice_ref, RDF.type, HVDC.Invoice))
        graph.add((shipment_ref, HVDC.invoicedAs, invoice_ref))

    for charge in charge_summaries:
        charge_ref = URIRef(charge["id"])
        invoice_ref = URIRef(charge["invoice_id"])
        graph.add((charge_ref, RDF.type, HVDC.ChargeSummary))
        graph.add((invoice_ref, HVDC.hasChargeSummary, charge_ref))

    for settlement in settlement_records:
        settlement_ref = URIRef(settlement["id"])
        invoice_ref = URIRef(settlement["invoice_id"])
        graph.add((settlement_ref, RDF.type, HVDC.SettlementRecord))
        graph.add((invoice_ref, HVDC.settledBy, settlement_ref))

    for record in reconciliation_records:
        recon_ref = URIRef(record["id"])
        graph.add((recon_ref, RDF.type, HVDC.ReconciliationRecord))

    for attribution in cost_attributions:
        attribution_ref = URIRef(attribution["id"])
        invoice_ref = URIRef(attribution["invoice_id"])
        shipment_ref = URIRef(attribution["shipment_id"])
        graph.add((attribution_ref, RDF.type, HVDC.CostAttribution))
        graph.add((invoice_ref, HVDC.attributedToShipment, shipment_ref))

    for pattern in patterns:
        pattern_ref = URIRef(pattern["id"])
        graph.add((pattern_ref, RDF.type, HVDCK.RecurringPattern))

    for item in evidence:
        evidence_ref = URIRef(item["id"])
        graph.add((evidence_ref, RDF.type, HVDCK.CommunicationEvidence))

    for mapping in mappings:
        mapping_ref = URIRef(f'https://hvdc.logistics/resource/mapping/{mapping["new_class"].lower()}')
        graph.add((mapping_ref, RDF.type, HVDCM.ConceptMapping))
        graph.add((mapping_ref, HVDCM.mapsClassTo, Literal(mapping["legacy_target"])))

    return graph, audit


def validate_canonical_graph(events, guides=None, lessons=None, all_ids=None):
    errors = []
    for event in events:
        if not event.get("subject_id"):
            errors.append("event_without_subject")
    seen = set()
    for value in all_ids or []:
        if value in seen:
            errors.append("duplicate_deterministic_ids")
            break
        seen.add(value)
    for guide in guides or []:
        if not guide.get("rules"):
            errors.append("guide_without_rule")
    for lesson in lessons or []:
        if not any(lesson.get(key) for key in ("shipment_id", "location_id", "carrier_id", "pattern_id")):
            errors.append("lesson_without_anchor")
    return {"status": "fail" if errors else "pass", "errors": errors}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_graph_mapping_builder.py tests/test_graph_canonical_builder.py tests/test_graph_validation.py -q`

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add app/services/graph_mapping_builder.py app/services/graph_canonical_builder.py app/services/graph_validation.py tests/test_graph_mapping_builder.py tests/test_graph_canonical_builder.py tests/test_graph_validation.py
git commit -m "feat: build compatibility mappings and canonical graph validation"
```

---

## Task 7: Build Dashboard Projection and Rewrite Export Entry Point

**Files:**
- Create: `app/services/graph_projection_builder.py`
- Modify: `scripts/build_dashboard_graph_data.py`
- Modify: `tests/test_dashboard_graph_export.py`
- Modify: `tests/test_ttl_to_json.py`

- [ ] **Step 1: Write the failing test for projection output**

```python
from app.services.graph_projection_builder import build_dashboard_projection


def test_build_dashboard_projection_emits_flat_consumer_contract():
    nodes, edges, audits = build_dashboard_projection(
        shipments=[{"id": "https://hvdc.logistics/resource/shipment/HVDC-001", "label": "HVDC-001", "type": "Shipment"}],
        events=[{"id": "event-1", "label": "AGI", "type": "ArrivalEvent", "subject_id": "https://hvdc.logistics/resource/shipment/HVDC-001", "location_id": "https://hvdc.logistics/resource/site/agi"}],
        lessons=[{"id": "lesson-1", "label": "Delay at AGI", "type": "IncidentLesson", "shipment_id": "https://hvdc.logistics/resource/shipment/HVDC-001"}],
    )
    assert nodes[0]["data"]["id"] == "https://hvdc.logistics/resource/shipment/HVDC-001"
    assert any(edge["data"]["target"] == "https://hvdc.logistics/resource/site/agi" for edge in edges)
    assert audits["projection"]["unknown_nodes"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py::test_build_dashboard_projection_emits_flat_consumer_contract -q`

Expected: import failure or missing function

- [ ] **Step 3: Implement projection builder and rewrite exporter**

```python
def build_dashboard_projection(*, shipments, events, lessons):
    node_payload = []
    edge_payload = []

    for shipment in shipments:
        node_payload.append(
            {"data": {"id": shipment["id"], "label": shipment["label"], "type": shipment["type"], "rdf-schema#label": shipment["label"]}}
        )

    for event in events:
        location_id = event["location_id"]
        node_payload.append(
            {"data": {"id": location_id, "label": event["label"], "type": "SiteLocation", "rdf-schema#label": event["label"]}}
        )
        edge_payload.append(
            {"data": {"id": f'{event["subject_id"]}|occurredAt|{location_id}', "source": event["subject_id"], "target": location_id, "label": "occurredAt"}}
        )

    for lesson in lessons:
        node_payload.append(
            {"data": {"id": lesson["id"], "label": lesson["label"], "type": lesson["type"], "rdf-schema#label": lesson["label"]}}
        )
        edge_payload.append(
            {"data": {"id": f'{lesson["shipment_id"]}|relatedToLesson|{lesson["id"]}', "source": lesson["shipment_id"], "target": lesson["id"], "label": "relatedToLesson"}}
        )

    return (
        sorted(node_payload, key=lambda item: (item["data"]["type"], item["data"]["label"], item["data"]["id"])),
        sorted(edge_payload, key=lambda item: (item["data"]["source"], item["data"]["target"], item["data"]["label"])),
        {"projection": {"unknown_nodes": 0}},
    )
```

Update `scripts/build_dashboard_graph_data.py` so its `export_dashboard_graph_data()` function:

1. calls `load_graph_sources()`
2. calls `normalize_sources()`
3. calls `build_knowledge_objects()` for guides, rules, lessons, evidence, and recurring patterns
4. resolves aliases and operational locations
5. builds canonical graph
6. writes `vault/knowledge_graph.ttl`
7. writes `kg-dashboard/public/data/nodes.json`
8. writes `kg-dashboard/public/data/edges.json`
9. writes four audit JSON files under `runtime/audits/`

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_dashboard_graph_export.py tests/test_ttl_to_json.py -q`

Expected: `all passed`

- [ ] **Step 5: Commit**

```bash
git add app/services/graph_projection_builder.py scripts/build_dashboard_graph_data.py tests/test_dashboard_graph_export.py tests/test_ttl_to_json.py
git commit -m "feat: project canonical graph into dashboard ttl and json outputs"
```

---

## Task 8: Keep Legacy Wrappers and Regenerate Artifacts

**Files:**
- Modify: `scripts/build_knowledge_graph.py`
- Modify: `scripts/ttl_to_json.py`
- Modify: `README.md`
- Modify: `kg-dashboard/public/data/nodes.json`
- Modify: `kg-dashboard/public/data/edges.json`

- [ ] **Step 1: Add failing wrapper smoke test**

```python
from pathlib import Path
import subprocess


def test_legacy_build_script_prints_deprecated_entrypoint(tmp_path: Path):
    result = subprocess.run(
        ["python", "scripts/build_knowledge_graph.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Deprecated entrypoint" in result.stdout
```

- [ ] **Step 2: Run smoke and expected-export commands**

Run:

- `python -m py_compile scripts/build_knowledge_graph.py scripts/ttl_to_json.py`
- `.venv\Scripts\python.exe scripts/build_dashboard_graph_data.py`

Expected:

- py_compile succeeds
- exporter writes `vault/knowledge_graph.ttl`
- exporter writes `kg-dashboard/public/data/nodes.json`
- exporter writes `kg-dashboard/public/data/edges.json`
- exporter writes four `runtime/audits/hvdc_ttl_*.json` files
- each audit file contains the required keys from the spec:
  - source audit: `dropped_rows`
  - resolution audit: `unresolved_attribution`, `weak_cost_attribution_confidence`
  - projection audit: `unknown_nodes`
  - mapping audit: `unmapped_lessons`, `unresolved_compatibility_mappings`

- [ ] **Step 3: Update legacy wrappers and README**

```python
print("Deprecated entrypoint: use scripts/build_dashboard_graph_data.py for shipment-centric TTL exports.")
```

Update `README.md` to document:

- four source workbooks
- `wiki/analyses` knowledge role
- legacy wrapper status
- audit output paths

```markdown
## Shipment-Centric TTL Export

- Source workbooks:
  - `Logi ontol core doc/HVDC STATUS.xlsx`
  - `Logi ontol core doc/HVDC WAREHOUSE STATUS.xlsx`
  - `Logi ontol core doc/JPT-reconciled_v6.0.xlsx`
  - `Logi ontol core doc/HVDC Logistics cost(inland,domestic).xlsx`
- Knowledge source:
  - `C:/Users/jichu/Downloads/valut/wiki/analyses`
- Canonical entrypoint:
  - `scripts/build_dashboard_graph_data.py`
- Audit outputs:
  - `runtime/audits/hvdc_ttl_source_audit.json`
  - `runtime/audits/hvdc_ttl_resolution_audit.json`
  - `runtime/audits/hvdc_ttl_projection_audit.json`
  - `runtime/audits/hvdc_ttl_mapping_audit.json`
```

- [ ] **Step 4: Run verification suite**

Run:

- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m ruff check app/services/graph_types.py app/services/graph_source_loader.py app/services/graph_normalizer.py app/services/graph_resolver.py app/services/graph_mapping_builder.py app/services/graph_canonical_builder.py app/services/graph_projection_builder.py app/services/graph_validation.py scripts/build_dashboard_graph_data.py scripts/build_knowledge_graph.py scripts/ttl_to_json.py tests/test_graph_source_loader.py tests/test_graph_normalizer.py tests/test_graph_resolver.py tests/test_graph_mapping_builder.py tests/test_graph_canonical_builder.py tests/test_graph_projection_builder.py tests/test_graph_validation.py tests/test_dashboard_graph_export.py tests/test_ttl_to_json.py`
- `.venv\Scripts\python.exe -m ruff format --check app/services/graph_types.py app/services/graph_source_loader.py app/services/graph_normalizer.py app/services/graph_resolver.py app/services/graph_mapping_builder.py app/services/graph_canonical_builder.py app/services/graph_projection_builder.py app/services/graph_validation.py scripts/build_dashboard_graph_data.py scripts/build_knowledge_graph.py scripts/ttl_to_json.py tests/test_graph_source_loader.py tests/test_graph_normalizer.py tests/test_graph_resolver.py tests/test_graph_mapping_builder.py tests/test_graph_canonical_builder.py tests/test_graph_projection_builder.py tests/test_graph_validation.py tests/test_dashboard_graph_export.py tests/test_ttl_to_json.py`
- `npm test`
- `npm run lint`
- `npm run build`

Expected:

- root pytest passes
- ruff check passes
- ruff format --check passes
- dashboard tests pass
- dashboard build passes

- [ ] **Step 5: Commit**

```bash
git add scripts/build_knowledge_graph.py scripts/ttl_to_json.py scripts/build_dashboard_graph_data.py README.md kg-dashboard/public/data/nodes.json kg-dashboard/public/data/edges.json runtime/audits/hvdc_ttl_source_audit.json runtime/audits/hvdc_ttl_resolution_audit.json runtime/audits/hvdc_ttl_projection_audit.json runtime/audits/hvdc_ttl_mapping_audit.json vault/knowledge_graph.ttl
git commit -m "feat: ship shipment-centric ttl pipeline and regenerated graph artifacts"
```

---

## Spec Coverage Check

- Shipment spine: covered by Tasks 1, 3, 6
- Case layer: covered by Tasks 2, 3, 6
- Event model: covered by Tasks 3, 4, 6, 7
- LCT operation carrier model: covered by Tasks 2, 4, 6
- Cost and settlement layer: covered by Tasks 1, 3, 6
- WhatsApp and analyses lesson layer: covered by Tasks 2, 4, 5, 6
- Compatibility mapping layer: covered by Task 6 and Task 8 runtime mapping audit output
- Validation and audit gates: covered by Task 6 and Task 8 verification

## Self-Review

- Spec coverage checked against shipment, case, event, LCT, cost, knowledge, and mapping layers
- All file paths in commands are explicit
- Each code-changing step includes code or exact content
- Validation commands are listed with exact paths

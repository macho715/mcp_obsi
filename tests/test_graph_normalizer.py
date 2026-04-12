import pandas as pd

from app.services.graph_normalizer import normalize_sources
from app.services.graph_types import (
    CanonicalCargoItem,
    CanonicalCase,
    CanonicalChargeSummary,
    CanonicalCostAttribution,
    CanonicalDocumentRef,
    CanonicalEvent,
    CanonicalInvoice,
    CanonicalJourneyLeg,
    CanonicalMilestoneEvent,
    CanonicalReconciliationRecord,
    CanonicalSettlementRecord,
    CanonicalShipment,
    CanonicalStatusSnapshot,
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


def _make_sources():
    return {
        "shipment_rows": [
            {
                "SCT SHIP NO.": "HVDC-001",
                "COMMERCIAL INVOICE No.": "CI-001",
                "VENDOR": "Vendor A",
                "MOSB": "2025-01-01",
                "AGI": "2025-01-03",
            }
        ],
        "warehouse_rows": [
            {
                "SCT SHIP NO.": "HVDC-001",
                "Case No.": "CASE-01",
                "Storage": "DSV Indoor",
                "ETA/ATA": "2025-01-02",
            }
        ],
        "jpt_sheets": {
            "1_Decklog": [],
            "3_Voyage_Master": [],
            "4_Voyage_Rollup": [],
            "6_Reconciliation": [],
            "7_Exceptions": [],
            "8_Decklog_Context": [],
        },
        "inland_cost_rows": [
            {
                "Invoice No": "INV-001",
                "Shipment No": "HVDC-001",
                "Storage": 120.0,
            }
        ],
        "analysis_notes": [],
    }


def test_normalize_sources_creates_shipment_case_and_cost_candidates():
    normalized = normalize_sources(_make_sources())

    assert normalized.shipments[0].shipment_no == "HVDC-001"
    assert normalized.cases[0].case_no == "CASE-01"
    assert normalized.route_events[0].event_type == "ArrivalEvent"
    assert normalized.document_refs[0]["document_ref"] == "CI-001"
    assert normalized.status_snapshots[0]["shipment_id"].endswith("/shipment/HVDC-001")
    assert normalized.charge_candidates[0]["invoice_no"] == "INV-001"


def test_normalize_sources_keeps_ids_deterministic_for_same_rows():
    first = normalize_sources(_make_sources())
    second = normalize_sources(_make_sources())

    assert first.shipments[0].id == second.shipments[0].id
    assert first.cases[0].id == second.cases[0].id
    assert first.route_events[0].id == second.route_events[0].id
    assert first.document_refs[0]["id"] == second.document_refs[0]["id"]
    assert first.status_snapshots[0]["id"] == second.status_snapshots[0]["id"]


def test_normalize_sources_normalizes_timestamp_dates_and_skips_blank_values():
    sources = {
        "shipment_rows": [
            {
                "SCT SHIP NO.": "HVDC-002",
                "COMMERCIAL INVOICE No.": "",
                "VENDOR": pd.NA,
                "MOSB": pd.Timestamp("2025-01-01 00:00:00"),
                "AGI": pd.Timestamp("2025-01-03 14:15:16"),
                "DAS": pd.NA,
            }
        ],
        "warehouse_rows": [],
        "jpt_sheets": {},
        "inland_cost_rows": [],
        "analysis_notes": [],
    }

    normalized = normalize_sources(sources)

    assert normalized.shipments[0].vendor_name is None
    assert normalized.route_events[0].event_date == "2025-01-01"
    assert normalized.route_events[0].id.endswith("/mosb/2025-01-01")
    assert normalized.route_events[1].event_date == "2025-01-03T14:15:16"
    assert normalized.route_events[1].id.endswith("/agi/2025-01-03T14:15:16")
    assert len(normalized.route_events) == 2
    assert normalized.document_refs == []


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

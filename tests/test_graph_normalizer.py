from app.services.graph_types import (
    CanonicalCargoItem,
    CanonicalCase,
    CanonicalChargeSummary,
    CanonicalCostAttribution,
    CanonicalDocumentRef,
    CanonicalEvent,
    CanonicalInvoice,
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

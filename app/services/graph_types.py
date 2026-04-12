from dataclasses import dataclass, field


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
    actual_dt: str | None = None
    location_id: str | None = None
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

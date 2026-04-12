from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pandas as pd

from app.services.graph_types import CanonicalCase, CanonicalEvent, CanonicalShipment

_ROUTE_FIELDS = (
    ("MOSB", "mosb"),
    ("AGI", "agi"),
    ("DAS", "das"),
    ("MIR", "mir"),
    ("SHU", "shu"),
)


@dataclass(slots=True)
class NormalizedSources:
    shipments: list[CanonicalShipment]
    cases: list[CanonicalCase]
    route_events: list[CanonicalEvent]
    document_refs: list[dict[str, Any]]
    status_snapshots: list[dict[str, Any]]
    charge_candidates: list[dict[str, Any]]


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        if value.hour == 0 and value.minute == 0 and value.second == 0 and value.microsecond == 0:
            return value.date().isoformat()
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat"}:
        return None
    return text


def _shipment_id(shipment_no: str) -> str:
    return f"https://hvdc.logistics/resource/shipment/{shipment_no}"


def normalize_sources(sources: dict[str, Any]) -> NormalizedSources:
    shipments: list[CanonicalShipment] = []
    cases: list[CanonicalCase] = []
    route_events: list[CanonicalEvent] = []
    document_refs: list[dict[str, Any]] = []
    status_snapshots: list[dict[str, Any]] = []
    charge_candidates: list[dict[str, Any]] = []

    for row in sources.get("shipment_rows", []):
        shipment_no = _clean_text(row.get("SCT SHIP NO."))
        if not shipment_no:
            continue

        shipment_id = _shipment_id(shipment_no)
        shipments.append(
            CanonicalShipment(
                id=shipment_id,
                shipment_no=shipment_no,
                vendor_name=_clean_text(row.get("VENDOR")),
            )
        )

        for location_field, location_slug in _ROUTE_FIELDS:
            event_date = _clean_text(row.get(location_field))
            if not event_date:
                continue
            route_events.append(
                CanonicalEvent(
                    id=(
                        "https://hvdc.logistics/resource/arrival/"
                        f"{shipment_no}/{location_slug}/{event_date}"
                    ),
                    event_type="ArrivalEvent",
                    subject_id=shipment_id,
                    location_id=f"https://hvdc.logistics/resource/site/{location_slug}",
                    event_date=event_date,
                )
            )

        commercial_invoice = _clean_text(row.get("COMMERCIAL INVOICE No."))
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

    for row in sources.get("warehouse_rows", []):
        shipment_no = _clean_text(row.get("SCT SHIP NO."))
        case_no = _clean_text(row.get("Case No."))
        if not shipment_no or not case_no:
            continue

        cases.append(
            CanonicalCase(
                id=f"https://hvdc.logistics/resource/case/{shipment_no}/{case_no}",
                shipment_id=_shipment_id(shipment_no),
                case_no=case_no,
            )
        )

    for row in sources.get("inland_cost_rows", []):
        invoice_no = _clean_text(row.get("Invoice No"))
        shipment_no = _clean_text(row.get("Shipment No"))
        if not invoice_no or not shipment_no:
            continue

        charge_candidates.append(
            {
                "invoice_no": invoice_no,
                "shipment_no": shipment_no,
                "row": row,
            }
        )

    return NormalizedSources(
        shipments=shipments,
        cases=cases,
        route_events=route_events,
        document_refs=document_refs,
        status_snapshots=status_snapshots,
        charge_candidates=charge_candidates,
    )

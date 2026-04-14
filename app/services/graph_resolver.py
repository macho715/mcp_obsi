from __future__ import annotations

from typing import Any

from app.services.graph_types import ResolutionDecision

LOCATION_ALIASES: dict[str, tuple[str, str]] = {
    "west harbor jetty #3": (
        "Jetty",
        "https://hvdc.logistics/resource/oploc/agi/west_harbor_jetty_3",
    ),
    "mosb": ("HubLocation", "https://hvdc.logistics/resource/hub/mosb"),
    "mw4 jetty": ("Jetty", "https://hvdc.logistics/resource/oploc/mw4/mw4_jetty"),
    "agi anchorage": (
        "AnchorageArea",
        "https://hvdc.logistics/resource/oploc/agi/anchorage",
    ),
    "vp24 yard": (
        "YardArea",
        "https://hvdc.logistics/resource/oploc/abu_dhabi/vp24_yard",
    ),
    "cicpa gate": (
        "GateArea",
        "https://hvdc.logistics/resource/oploc/mir/cicpa_gate",
    ),
}

CARRIER_ALIASES: dict[str, str] = {
    "jopetwil 71": "https://hvdc.logistics/resource/carrier/jopetwil_71",
    "jpt71": "https://hvdc.logistics/resource/carrier/jopetwil_71",
}


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def resolve_location(value: str) -> ResolutionDecision:
    target = LOCATION_ALIASES.get(_normalize(value))
    if target is None:
        return ResolutionDecision(
            status="unresolved",
            source_value=value,
            target_id=None,
            target_type=None,
            reason="location alias missing",
        )

    target_type, target_id = target
    return ResolutionDecision(
        status="resolved",
        source_value=value,
        target_id=target_id,
        target_type=target_type,
    )


def resolve_carrier(value: str) -> ResolutionDecision:
    target_id = CARRIER_ALIASES.get(_normalize(value))
    if target_id is None:
        return ResolutionDecision(
            status="unresolved",
            source_value=value,
            target_id=None,
            target_type=None,
            reason="carrier alias missing",
        )

    return ResolutionDecision(
        status="resolved",
        source_value=value,
        target_id=target_id,
        target_type="OperationCarrier",
    )


def resolve_analysis_note(note: dict[str, Any]) -> dict[str, Any]:
    path = str(note.get("path", "")).lower()
    frontmatter = note.get("frontmatter")
    slug = frontmatter.get("slug") if isinstance(frontmatter, dict) else None

    if path.startswith("guideline_") or "guideline_" in path:
        return {"class_name": "GroupGuide", "slug": slug}

    if path.startswith("logistics_issue_") or "logistics_issue_" in path:
        return {"class_name": "IncidentLesson", "slug": slug}

    return {"class_name": "UnresolvedAnalysisNote", "slug": slug}

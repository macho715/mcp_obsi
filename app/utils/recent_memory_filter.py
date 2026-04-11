from typing import Any

_VERIFICATION_TITLE_PATTERNS = (
    "write check",
    "write-check",
    "verification",
    "qa save check",
    "test save",
    "smoke",
    "probe",
    "kb lint",
    "lint ",
)

_VERIFICATION_TAGS = {
    "verification",
    "rollback-archived",
    "specialist-write",
    "write-check",
    "probe",
    "smoke",
    "qa",
    "test",
}

_VERIFICATION_PROJECTS = {
    "local-verification",
}


def classify_recent_memory(item: dict[str, Any]) -> tuple[str, list[str]]:
    title = str(item.get("title") or "").casefold()
    project = str(item.get("project") or "").strip().casefold()
    tags = {str(tag).strip().casefold() for tag in item.get("tags", []) or [] if str(tag).strip()}

    reasons: list[str] = []

    matched_title_terms = [term for term in _VERIFICATION_TITLE_PATTERNS if term in title]
    if matched_title_terms:
        reasons.append(f"title:{', '.join(matched_title_terms)}")

    matched_tags = sorted(tag for tag in tags if tag in _VERIFICATION_TAGS)
    if matched_tags:
        reasons.append(f"tags:{', '.join(matched_tags)}")

    if project in _VERIFICATION_PROJECTS:
        reasons.append(f"project:{project}")

    return ("verification", reasons) if reasons else ("business", [])


def annotate_recent_memory(item: dict[str, Any]) -> dict[str, Any]:
    classification, reasons = classify_recent_memory(item)
    annotated = dict(item)
    annotated["classification"] = classification
    annotated["classification_reasons"] = reasons
    return annotated


def prioritize_recent_memories(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotated = [annotate_recent_memory(item) for item in items]
    business = [item for item in annotated if item["classification"] == "business"]
    verification = [item for item in annotated if item["classification"] == "verification"]
    return [*business, *verification]

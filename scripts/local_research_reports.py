from __future__ import annotations

from copy import deepcopy
from typing import Any


def build_research_report(result: dict[str, Any]) -> dict[str, Any]:
    mode = str(result.get("mode") or "ask")
    title = _title(result)
    sections = _bundle_sections(result) if mode == "find-bundle" else _ask_sections(result)
    if str(result.get("analysis_mode") or "") == "invoice-audit" or result.get("structured_data"):
        sections = [*_invoice_sections(result), *sections]
    return {
        "title": title,
        "ai_status": _ai_status(result),
        "sections": [section for section in sections if section["items"]],
        "debug_json": deepcopy(result),
    }


def _ask_sections(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"title": "Answer", "items": _string_items(result.get("short_answer"))},
        {"title": "Key Findings", "items": _items(result.get("findings"))},
        {"title": "Evidence", "items": _items(result.get("findings"))},
        {"title": "Gaps", "items": _string_items(result.get("gaps"))},
        {"title": "Next Actions", "items": _string_items(result.get("next_actions"))},
        {"title": "Sources", "items": _items(result.get("sources"))},
    ]


def _bundle_sections(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"title": "Core Files", "items": _items(result.get("core_files"))},
        {"title": "Supporting Files", "items": _items(result.get("supporting_files"))},
        {"title": "Duplicates / Versions", "items": _items(result.get("duplicates_or_versions"))},
        {"title": "Missing / Gap Hints", "items": _items(result.get("missing_or_gap_hints"))},
        {"title": "Next Actions", "items": _string_items(result.get("next_actions"))},
        {"title": "Sources", "items": _items(result.get("sources"))},
    ]


def _invoice_sections(result: dict[str, Any]) -> list[dict[str, Any]]:
    data = result.get("structured_data")
    if not isinstance(data, dict):
        return []
    expected = [
        "invoice_number",
        "issue_date",
        "supplier",
        "buyer",
        "amount",
        "vat",
        "total",
        "currency",
    ]
    missing = [field for field in expected if not str(data.get(field) or "").strip()]
    return [
        {"title": "Invoice Fields", "items": [dict(data)]},
        {"title": "Missing Fields", "items": missing},
    ]


def _title(result: dict[str, Any]) -> str:
    if str(result.get("mode") or "") == "find-bundle" and result.get("bundle_title"):
        return str(result["bundle_title"])
    return str(
        result.get("question")
        or result.get("topic")
        or result.get("bundle_title")
        or "Local Research Result"
    )


def _ai_status(result: dict[str, Any]) -> str:
    provider = str(result.get("provider") or "unknown")
    model = str(result.get("model") or "")
    if result.get("ai_applied") is False or str(result.get("provider_status") or "") == "fallback":
        return "AI not applied; showing deterministic evidence only"
    return f"AI applied via {provider}{f' / {model}' if model else ''}"


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    return [value]


def _string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]

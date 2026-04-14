from __future__ import annotations

import re

_TOKEN_PATTERNS = [
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{8,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"https?://[^/\s:@]+:[^/\s@]+@"),
]

_TOKEN_REPLACEMENTS: list[tuple[re.Pattern[str], str | re.Callable[[re.Match[str]], str]]] = [
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"), "Bearer [REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9]{8,}\b"), "[REDACTED_API_KEY]"),
    (
        re.compile(r"(?i)\b(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
        lambda match: f"{match.group(1)}=[REDACTED]",
    ),
    (
        re.compile(r"https?://([^/\s:@]+):([^/\s@]+)@"),
        lambda match: match.group(0).replace(f"{match.group(1)}:{match.group(2)}@", "[REDACTED]@"),
    ),
]

_PURE_SECRET_PATTERNS = [
    re.compile(r"(?i)^Bearer\s+[A-Za-z0-9._~+/=-]{8,}$"),
    re.compile(r"^sk-[A-Za-z0-9]{8,}$"),
    re.compile(r"(?i)^(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+$"),
    re.compile(r"^https?://[^/\s:@]+:[^/\s@]+@[^/\s]+$"),
]

_STRICT_SENSITIVITY_LEVEL_FLOOR = 2


def clean_text(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def clean_tag(tag: str) -> str:
    return re.sub(r"\s+", "-", tag.strip().lower())


def contains_sensitive_pattern(value: str) -> bool:
    return any(pattern.search(value) for pattern in _TOKEN_PATTERNS)


def is_pure_secret(value: str) -> bool:
    cleaned = clean_text(value)
    return any(pattern.fullmatch(cleaned) for pattern in _PURE_SECRET_PATTERNS)


def mask_sensitive_text(value: str) -> str:
    masked = value
    for pattern, replacement in _TOKEN_REPLACEMENTS:
        masked = pattern.sub(replacement, masked)
    return masked


def sanitize_free_text(field_name: str, value: str) -> str:
    return sanitize_free_text_for_sensitivity(field_name, value, sensitivity=None)


def is_high_sensitivity(sensitivity: str | None) -> bool:
    if sensitivity is None:
        return False
    normalized = clean_text(sensitivity).lower()
    if not normalized.startswith("p"):
        return False
    try:
        level = int(normalized[1:])
    except ValueError:
        return False
    return level >= _STRICT_SENSITIVITY_LEVEL_FLOOR


def sanitize_free_text_for_sensitivity(
    field_name: str,
    value: str,
    sensitivity: str | None,
) -> str:
    normalized = clean_text(value)
    if not normalized:
        return normalized

    if is_pure_secret(normalized):
        raise ValueError(f"{field_name} contains only sensitive material")

    if contains_sensitive_pattern(normalized):
        if is_high_sensitivity(sensitivity):
            raise ValueError(
                f"{field_name} contains sensitive fragments disallowed for sensitivity"
                f" {sensitivity}"
            )
        return clean_text(mask_sensitive_text(normalized))

    return normalized


def reject_sensitive_label(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None
    normalized = clean_text(value)
    if not normalized:
        return None
    if contains_sensitive_pattern(normalized) or is_pure_secret(normalized):
        raise ValueError(f"{field_name} contains sensitive token-like data")
    return normalized


def sanitize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    for tag in tags:
        raw = reject_sensitive_label("tags", tag)
        if raw is None:
            continue
        cleaned = clean_tag(raw)
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized

import re
from datetime import date

from app.models import MemoryRole, SearchPlan

TOKEN_RE = re.compile(
    r'(?P<kv>[A-Za-z_][A-Za-z0-9_-]*:"[^"]*"|[A-Za-z_][A-Za-z0-9_-]*:\S+)|(?P<quoted>"[^"]*")|(?P<bare>\S+)'
)


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _normalize_text(value)
        if not cleaned:
            continue
        marker = cleaned.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        normalized.append(cleaned)
    return normalized


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_search_query(query: str, default_limit: int | None = None) -> SearchPlan:
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return SearchPlan(raw_query="", limit=default_limit)

    text_terms: list[str] = []
    roles: list[str] = []
    topics: list[str] = []
    entities: list[str] = []
    projects: list[str] = []
    tags: list[str] = []
    status: str | None = None
    after: date | None = None
    before: date | None = None
    limit = default_limit

    for match in TOKEN_RE.finditer(normalized_query):
        token = match.group(0)

        if match.group("kv"):
            key, raw_value = token.split(":", 1)
            key = key.strip().lower()
            value = raw_value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            value = _normalize_text(value)

            if not value:
                continue

            if key == "text":
                text_terms.append(value)
                continue
            if key == "role":
                try:
                    roles.append(MemoryRole(value.lower()).value)
                except ValueError:
                    text_terms.append(f"{key}:{value}")
                continue
            if key == "topic":
                topics.append(value)
                continue
            if key == "entity":
                entities.append(value)
                continue
            if key == "project":
                projects.append(value)
                continue
            if key == "tag":
                tags.append(value)
                continue
            if key == "status":
                status = value.lower()
                continue
            if key == "after":
                parsed = _parse_date(value)
                if parsed is not None:
                    after = parsed
                else:
                    text_terms.append(f"{key}:{value}")
                continue
            if key == "before":
                parsed = _parse_date(value)
                if parsed is not None:
                    before = parsed
                else:
                    text_terms.append(f"{key}:{value}")
                continue
            if key == "limit":
                try:
                    limit = max(1, min(20, int(value)))
                except ValueError:
                    text_terms.append(f"{key}:{value}")
                continue

            text_terms.append(f"{key}:{value}")
            continue

        if match.group("quoted"):
            value = _normalize_text(token[1:-1])
            if value:
                text_terms.append(value)
            continue

        value = _normalize_text(token)
        if value:
            text_terms.append(value)

    return SearchPlan(
        raw_query=normalized_query,
        text_terms=_normalize_list(text_terms),
        roles=[MemoryRole(role) for role in _normalize_list(roles)],
        topics=_normalize_list(topics),
        entities=_normalize_list(entities),
        projects=_normalize_list(projects),
        tags=_normalize_list(tags),
        status=status,
        after=after,
        before=before,
        limit=limit,
    )

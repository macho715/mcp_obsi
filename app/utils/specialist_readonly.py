import re

from app.services.memory_store import MemoryStore

_GENERIC_NOTE_TOKENS = {
    "memory",
    "memories",
    "memo",
    "memos",
    "note",
    "notes",
    "item",
    "items",
    "entry",
    "entries",
    "document",
    "documents",
    "doc",
    "docs",
    "메모",
    "노트",
    "문서",
    "기록",
}

_RECENT_HINT_TOKENS = {
    "recent",
    "latest",
    "new",
    "newest",
    "last",
    "recently",
    "browse",
    "list",
    "show",
    "saved",
    "최근",
    "최신",
    "요즘",
    "목록",
    "리스트",
    "보여줘",
}


def _query_tokens(query: str) -> list[str]:
    return re.findall(r"[0-9A-Za-z가-힣_-]+", query.casefold())


def _is_dateish_token(token: str) -> bool:
    digits = token.replace("-", "").replace("_", "")
    return digits.isdigit() and len(digits) in {1, 2, 4, 6, 8}


def looks_like_recent_listing_query(query: str) -> bool:
    tokens = _query_tokens(query)
    if not tokens:
        return False

    has_recent_hint = any(token in _RECENT_HINT_TOKENS for token in tokens)
    meaningful_tokens = [
        token
        for token in tokens
        if token not in _GENERIC_NOTE_TOKENS
        and token not in _RECENT_HINT_TOKENS
        and not _is_dateish_token(token)
    ]
    return has_recent_hint and not meaningful_tokens


def specialist_search_hits(store: MemoryStore, query: str, limit: int = 5) -> list[dict]:
    if looks_like_recent_listing_query(query):
        return store.recent(limit=limit)["results"]
    return store.search(query=query, limit=limit)["results"]

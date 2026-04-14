from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("local_rag.retrieval")

DEFAULT_DOCS_DIR = Path(r"C:\Users\jichu\Downloads\valut\wiki")
DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent / ".cache" / "retrieval-cache.json"


def resolve_cache_path() -> Path:
    configured = os.getenv("LOCAL_RAG_CACHE_PATH", "").strip()
    if configured:
        return Path(configured)
    return DEFAULT_CACHE_PATH


def resolve_query_cache_ttl_sec() -> float:
    raw = os.getenv("LOCAL_RAG_QUERY_CACHE_TTL_SEC", "45").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 45.0


def resolve_docs_dir() -> Path:
    configured = os.getenv("LOCAL_RAG_DOCS_DIR", "").strip()
    if configured:
        return Path(configured)
    return DEFAULT_DOCS_DIR


def _query_terms(query: str) -> list[str]:
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9가-힣]+", query)]
    return [term for term in terms if len(term) >= 2]


def _snippet(text: str, terms: list[str], limit: int = 220) -> str:
    lowered = text.lower()
    for term in terms:
        index = lowered.find(term)
        if index >= 0:
            start = max(0, index - 80)
            end = min(len(text), index + limit)
            return " ".join(text[start:end].split())
    return " ".join(text[:limit].split())


def _normalize_search_text(text: str) -> str:
    return " ".join(text.lower().split())


class RetrievalCache:
    def __init__(self, docs_dir: Path, sidecar_path: Path) -> None:
        self.docs_dir = docs_dir
        self.sidecar_path = sidecar_path
        self._loaded = False
        self._version = 0
        self._entries: dict[str, dict[str, Any]] = {}
        self._query_cache: dict[str, dict[str, Any]] = {}

    def _load_sidecar(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self.sidecar_path.exists():
            return
        try:
            payload = json.loads(self.sidecar_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict):
            return
        sidecar_docs_dir = payload.get("docs_dir")
        if not isinstance(sidecar_docs_dir, str) or sidecar_docs_dir != str(self.docs_dir):
            return
        entries = payload.get("entries", [])
        if not isinstance(entries, list):
            return
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            rel = entry.get("relative_path")
            if isinstance(rel, str) and rel.strip():
                self._entries[rel] = entry

    def _save_sidecar(self) -> None:
        payload = {
            "version": self._version,
            "docs_dir": str(self.docs_dir),
            "entries": list(self._entries.values()),
        }
        try:
            self.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
            self.sidecar_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            return

    def refresh(self) -> int:
        self._load_sidecar()
        if not self.docs_dir.exists():
            self._entries = {}
            self._query_cache = {}
            self._version += 1
            return 0

        changed = False
        current_paths: set[str] = set()
        for path in self.docs_dir.rglob("*.md"):
            if path.name in {"index.md", "log.md"}:
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            relative_path = path.relative_to(self.docs_dir).as_posix()
            current_paths.add(relative_path)
            cached = self._entries.get(relative_path)
            mtime_ns = int(stat.st_mtime_ns)
            size = int(stat.st_size)
            if cached and cached.get("mtime_ns") == mtime_ns and cached.get("size") == size:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                if relative_path in self._entries:
                    del self._entries[relative_path]
                    changed = True
                continue
            self._entries[relative_path] = {
                "relative_path": relative_path,
                "file": path.name,
                "mtime_ns": mtime_ns,
                "size": size,
                "search_text": _normalize_search_text(text),
                "snippet_seed": " ".join(text.split()),
            }
            changed = True

        deleted_paths = [relative_path for relative_path in self._entries if relative_path not in current_paths]
        for relative_path in deleted_paths:
            del self._entries[relative_path]
            changed = True

        if changed:
            self._version += 1
            self._query_cache = {}
            self._save_sidecar()

        return len(self._entries)

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        self.refresh()
        terms = _query_terms(query)
        if not terms:
            return []

        cache_key = " ".join(terms)
        cached = self._query_cache.get(cache_key)
        now = time.time()
        if (
            cached
            and isinstance(cached.get("expires_at"), (int, float))
            and cached.get("version") == self._version
            and float(cached["expires_at"]) >= now
        ):
            cached_result = cached.get("results", [])[:limit]
            logger.info(
                "[RETRIEVAL] cache=HIT terms=%s results=%d",
                cache_key,
                len(cached_result),
            )
            return list(cached_result)

        logger.info("[RETRIEVAL] cache=MISS terms=%s", cache_key)

        matches: list[dict[str, Any]] = []
        for entry in self._entries.values():
            search_text = entry.get("search_text", "")
            if not isinstance(search_text, str):
                continue
            score = sum(search_text.count(term) for term in terms)
            if score <= 0:
                continue
            snippet_seed = entry.get("snippet_seed", "")
            matches.append(
                {
                    "file": entry.get("file", entry.get("relative_path", "")),
                    "score": float(score),
                    "source_path": entry.get("relative_path", ""),
                    "snippet": _snippet(
                        snippet_seed if isinstance(snippet_seed, str) else "", terms
                    ),
                }
            )

        matches.sort(key=lambda item: item["score"], reverse=True)
        results = matches
        self._query_cache[cache_key] = {
            "version": self._version,
            "expires_at": now + resolve_query_cache_ttl_sec(),
            "results": results,
        }
        return results[:limit]


_runtime_cache: RetrievalCache | None = None


def get_retrieval_cache() -> RetrievalCache:
    global _runtime_cache
    docs_dir = resolve_docs_dir()
    cache_path = resolve_cache_path()
    if (
        _runtime_cache is None
        or _runtime_cache.docs_dir != docs_dir
        or _runtime_cache.sidecar_path != cache_path
    ):
        _runtime_cache = RetrievalCache(docs_dir=docs_dir, sidecar_path=cache_path)
    return _runtime_cache


def clear_runtime_cache() -> None:
    global _runtime_cache
    _runtime_cache = None


def search_documents(query: str, limit: int = 3) -> list[dict[str, Any]]:
    return get_retrieval_cache().search(query=query, limit=limit)


def count_documents() -> int:
    return get_retrieval_cache().refresh()

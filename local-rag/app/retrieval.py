from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

_DEFAULT_DOCS_DIR = r"C:\Users\jichu\Downloads\valut\wiki"
_DEFAULT_CACHE_PATH = ".cache/retrieval-cache.json"
_MAX_RESULTS = 5
_SCORE_THRESHOLD = 0.1

_runtime_cache: dict[str, Any] | None = None


def _docs_dir() -> Path:
    return Path(os.getenv("LOCAL_RAG_DOCS_DIR", _DEFAULT_DOCS_DIR)).resolve()


def _cache_path() -> Path:
    return Path(os.getenv("LOCAL_RAG_CACHE_PATH", _DEFAULT_CACHE_PATH)).resolve()


def _scan_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    )


def _tokenize(text: str) -> list[str]:
    return list(set(re.findall(r"[가-힣\w]{2,}", text.lower())))


def _score_text(query_words: set[str], text_words: list[str] | set[str]) -> float:
    if not query_words:
        return 0.0
    text_set = set(text_words) if not isinstance(text_words, set) else text_words
    matched = len(query_words & text_set)
    return matched / math.sqrt(len(text_words)) if text_words else 0.0


def _extract_snippet(text: str, query_words: set[str], context_chars: int = 200) -> str:
    text_lower = text.lower()
    best_pos = -1
    best_hit = 0
    for index in range(len(text)):
        window = text_lower[index : index + context_chars]
        hits = sum(1 for word in query_words if word in window)
        if hits > best_hit:
            best_hit = hits
            best_pos = index
    if best_pos == -1:
        return text[:context_chars].strip()
    start = max(0, best_pos - 30)
    end = min(len(text), best_pos + context_chars)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def _load_file_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def _read_sidecar() -> dict[str, Any]:
    path = _cache_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def _write_sidecar(cache: dict[str, Any]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    try:
        temp_path.write_text(
            json.dumps(cache, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temp_path, path)
    except OSError:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _build_entry(path: Path, docs_root: Path) -> dict[str, Any]:
    stat = path.stat()
    text = _load_file_text(path)
    relative_path = path.relative_to(docs_root).as_posix()
    return {
        "relative_path": relative_path,
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
        "text": text,
        "words": _tokenize(text),
    }


def clear_runtime_cache() -> None:
    global _runtime_cache
    _runtime_cache = None


def get_retrieval_cache() -> dict[str, Any]:
    global _runtime_cache

    docs_root = _docs_dir()
    runtime_cache = _runtime_cache
    if runtime_cache is None or runtime_cache.get("docs_dir") != str(docs_root):
        sidecar = _read_sidecar()
        if sidecar.get("docs_dir") == str(docs_root):
            runtime_cache = {
                "docs_dir": str(docs_root),
                "files": dict(sidecar.get("files", {})),
            }
        else:
            runtime_cache = {"docs_dir": str(docs_root), "files": {}}

    current_files = _scan_files(docs_root)
    previous_files = runtime_cache.get("files", {})
    next_files: dict[str, dict[str, Any]] = {}
    changed = False

    for path in current_files:
        relative_path = path.relative_to(docs_root).as_posix()
        stat = path.stat()
        previous = previous_files.get(relative_path)
        if (
            previous
            and previous.get("mtime_ns") == stat.st_mtime_ns
            and previous.get("size") == stat.st_size
        ):
            next_files[relative_path] = previous
            continue

        next_files[relative_path] = _build_entry(path, docs_root)
        changed = True

    if set(previous_files) != set(next_files):
        changed = True

    runtime_cache = {"docs_dir": str(docs_root), "files": next_files}
    _runtime_cache = runtime_cache
    if changed:
        _write_sidecar(runtime_cache)
    return runtime_cache


def count_documents() -> int:
    return len(_scan_files(_docs_dir()))


def search_documents(
    query: str,
    limit: int = _MAX_RESULTS,
    *,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    effective_limit = max(1, top_k if top_k is not None else limit)
    normalized_query = query.strip()
    if not normalized_query:
        return []

    query_words = set(_tokenize(normalized_query))
    if not query_words:
        return []

    cache = get_retrieval_cache()
    scored: list[tuple[float, dict[str, Any]]] = []
    for relative_path, entry in cache.get("files", {}).items():
        text_words = list(entry.get("words", []))
        score = _score_text(query_words, text_words)
        if score < _SCORE_THRESHOLD:
            continue
        text = str(entry.get("text", ""))
        scored.append(
            (
                score,
                {
                    "file": relative_path,
                    "score": round(score, 4),
                    "doc_type": Path(relative_path).suffix.lstrip("."),
                    "source_path": relative_path,
                    "snippet": _extract_snippet(text, query_words),
                },
            )
        )

    scored.sort(key=lambda item: (item[0], item[1]["file"]), reverse=True)
    return [item for _, item in scored[:effective_limit]]

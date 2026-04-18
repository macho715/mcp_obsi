from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from typing import Any

import requests

from app.utils.sanitize import contains_sensitive_pattern
from scripts.local_research_providers import CopilotProvider, ProviderRouter
from scripts.local_wiki_copilot import DEFAULT_COPILOT_ENDPOINT, DEFAULT_COPILOT_MODEL
from scripts.local_wiki_everything import (
    DEFAULT_EVERYTHING_HTTP_BASE_URL,
    ensure_loopback_base_url,
    search_everything,
)
from scripts.local_wiki_extract import extract_document

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xlsm", ".md", ".txt", ".csv", ".json", ".log"}
EXTENSION_PRIORITY = {
    ".md": 0,
    ".txt": 0,
    ".csv": 1,
    ".json": 1,
    ".log": 1,
    ".docx": 2,
    ".xlsx": 3,
    ".xlsm": 3,
    ".pdf": 4,
}
LOW_VALUE_PATH_MARKERS = (
    "\\.codex\\",
    "\\.cursor\\",
    "\\$recycle.bin\\",
    "\\node_modules\\",
    "\\.venv\\",
    "\\.cache\\",
    "\\dist\\",
    "\\build\\",
)
EXCLUDED_PATH_MARKERS = (
    "\\appdata\\local\\temp\\pytest-of-",
    "\\pytest-of-",
    "\\test_preview_candidates_",
    "\\test_find_bundle_",
)
SECRET_NAME_MARKERS = ("password", "secret", "token", "apikey", "api-key", "private-key")
MAX_QUERIES = 12
MAX_EXTRACTED_SOURCES = 10
MAX_PACKET_CHARS = 3_000
REQUEST_TIMEOUT_SECONDS = 120

SearchFn = Callable[[str, int], list[dict[str, Any]]]
ExtractFn = Callable[[Path], dict[str, Any]]
CopilotFn = Callable[[dict[str, Any]], dict[str, Any]]
ProviderRouterFn = Any
TimestampFn = Callable[[], str]
ProgressFn = Callable[[str, int, str], None]
CancelFn = Callable[[], bool]


class ResearchCancelled(RuntimeError):
    """Raised when a queued local research job is cancelled before provider work."""


def generate_search_queries(text: str) -> list[str]:
    tokens = [
        token.strip("._-")
        for token in re.findall(r"[A-Za-z0-9가-힣._-]+", text)
        if len(token.strip("._-")) >= 2
    ]
    queries: list[str] = []
    for index, token in enumerate(tokens):
        _append_query(queries, token)
        if index + 1 < len(tokens):
            _append_query(queries, f"{token} {tokens[index + 1]}")
        if len(queries) >= MAX_QUERIES:
            break
    return queries or [text.strip()]


def _append_query(queries: list[str], value: str) -> None:
    if value and value not in queries and len(queries) < MAX_QUERIES:
        queries.append(value)


def dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for candidate in candidates:
        if _is_excluded_candidate(candidate):
            continue
        path = str(candidate.get("path") or "").strip()
        if not path:
            continue
        key = path.replace("/", "\\").lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def rank_candidates(
    candidates: list[dict[str, Any]],
    query_tokens: list[str],
) -> list[dict[str, Any]]:
    enriched = [_ranked_candidate(candidate, query_tokens) for candidate in candidates]
    enriched = _annotate_duplicate_groups(enriched)
    return sorted(
        enriched,
        key=lambda candidate: (
            -int(candidate.get("score") or 0),
            _path_penalty(candidate),
            EXTENSION_PRIORITY.get(str(candidate.get("extension") or "").lower(), 99),
            str(candidate.get("path") or "").lower(),
        ),
    )


class ResearchService:
    def __init__(
        self,
        *,
        output_root: str | Path = Path("runtime/research"),
        search: SearchFn | None = None,
        extract: ExtractFn | None = None,
        copilot: CopilotFn | None = None,
        timestamp: TimestampFn | None = None,
        everything_base_url: str = DEFAULT_EVERYTHING_HTTP_BASE_URL,
        copilot_endpoint: str = DEFAULT_COPILOT_ENDPOINT,
        provider_router: ProviderRouterFn | None = None,
    ) -> None:
        self.output_root = Path(output_root)
        self.search = search or _default_search
        self.extract = extract or extract_document
        self.copilot = copilot or _default_copilot
        self.timestamp = timestamp or _timestamp
        self.everything_base_url = ensure_loopback_base_url(everything_base_url)
        self.copilot_endpoint = ensure_loopback_base_url(copilot_endpoint)
        self.provider_router = provider_router or ProviderRouter(
            copilot=CopilotProvider(copilot=self.copilot, endpoint=self.copilot_endpoint)
        )

    def health(self) -> dict[str, Any]:
        everything = _probe_search(self.search, self.everything_base_url)
        provider_health = self.provider_router.health()
        copilot = provider_health.get("copilot")
        if not isinstance(copilot, dict):
            copilot = _probe_copilot(self.copilot_endpoint)
        minimax = provider_health.get("minimax")
        if not isinstance(minimax, dict):
            minimax = {"status": "unknown"}
        active_provider = str(provider_health.get("active_provider") or "fallback")
        active_health = provider_health.get(active_provider)
        active_provider_ok = isinstance(active_health, dict) and active_health.get("status") == "ok"
        route_ready = everything["status"] == "ok" and active_provider_ok
        route_status = "ready" if route_ready else "blocked"
        return {
            "status": route_status,
            "route_status": route_status,
            "route_ready": route_ready,
            "everything": everything,
            "copilot": copilot,
            "minimax": minimax,
            "active_provider": active_provider,
            "output_root": str(self.output_root),
        }

    def ask_research(
        self,
        question: str,
        *,
        scope: str = "all",
        max_candidates: int = 10,
        save: bool = True,
        provider: str = "copilot",
        analysis_mode: str = "ask",
        tool_use: bool = False,
        progress: ProgressFn | None = None,
        is_cancelled: CancelFn | None = None,
    ) -> dict[str, Any]:
        _emit_progress(progress, "searching", 10, "Searching Everything")
        _raise_if_cancelled(is_cancelled)
        candidates = self._search_rank_extract(question, max_candidates=max_candidates)
        _raise_if_cancelled(is_cancelled)
        return self._ask_with_candidates(
            question,
            candidates,
            scope=scope,
            save=save,
            provider=provider,
            analysis_mode=analysis_mode,
            tool_use=tool_use,
            progress=progress,
            is_cancelled=is_cancelled,
        )

    def ask_selected(
        self,
        question: str,
        *,
        selected_candidates: list[dict[str, Any]],
        scope: str = "all",
        save: bool = True,
        provider: str = "copilot",
        analysis_mode: str = "ask",
        tool_use: bool = False,
        progress: ProgressFn | None = None,
        is_cancelled: CancelFn | None = None,
    ) -> dict[str, Any]:
        _emit_progress(progress, "extracting", 30, "Extracting selected files")
        _raise_if_cancelled(is_cancelled)
        candidates = self._extract_selected_candidates(selected_candidates)
        _raise_if_cancelled(is_cancelled)
        return self._ask_with_candidates(
            question,
            candidates,
            scope=scope,
            save=save,
            provider=provider,
            analysis_mode=analysis_mode,
            tool_use=tool_use,
            progress=progress,
            is_cancelled=is_cancelled,
        )

    def _ask_with_candidates(
        self,
        question: str,
        candidates: list[dict[str, Any]],
        *,
        scope: str,
        save: bool,
        provider: str,
        analysis_mode: str,
        tool_use: bool,
        progress: ProgressFn | None = None,
        is_cancelled: CancelFn | None = None,
    ) -> dict[str, Any]:
        _emit_progress(progress, "building_packet", 55, "Building evidence packet")
        _raise_if_cancelled(is_cancelled)
        packet = _build_research_packet(
            "ask", question, candidates, scope, analysis_mode=analysis_mode
        )
        warnings: list[str] = []
        try:
            _emit_progress(progress, "calling_provider", 65, "Calling provider")
            answer = self.provider_router.analyze(
                packet,
                provider=provider,
                analysis_mode=analysis_mode,
                tool_use=tool_use,
            )
            _emit_progress(progress, "validating_response", 80, "Validating provider response")
        except Exception as exc:
            warnings.append(f"{provider} failed: {exc}")
            answer = {
                "short_answer": (
                    "AI provider unavailable. Showing extracted evidence for manual review."
                ),
                "findings": _fallback_findings(candidates),
                "gaps": [
                    "Provider analysis is unavailable, so final judgment needs manual review."
                ],
                "next_actions": ["Open the listed source paths and verify the original files."],
            }

        answer_provider = str(answer.get("provider") or provider)
        result = {
            "mode": "ask",
            "question": question,
            "provider": answer_provider,
            "model": str(answer.get("model") or ""),
            "ai_applied": _ai_applied(answer_provider),
            "provider_status": _provider_status(answer_provider),
            "analysis_mode": analysis_mode,
            "tool_use": tool_use,
            "short_answer": str(answer.get("short_answer") or ""),
            "findings": _list_of_dicts(answer.get("findings")),
            "sources": [_source_payload(candidate) for candidate in candidates],
            "gaps": _string_list(answer.get("gaps")),
            "next_actions": _string_list(answer.get("next_actions")),
            "saved_markdown": "",
            "saved_json": "",
            "warnings": warnings
            + _string_list(answer.get("provider_warnings"))
            + _string_list(answer.get("warnings")),
        }
        result.update(_analysis_extras(answer))
        if save:
            _emit_progress(progress, "saving", 85, "Saving result")
            paths = self._save_result("answers", "answer", result)
            result.update(paths)
        return result

    def find_bundle(
        self,
        topic: str,
        *,
        scope: str = "all",
        max_candidates: int = 20,
        save: bool = True,
        provider: str = "copilot",
        analysis_mode: str = "find-bundle",
        tool_use: bool = False,
        progress: ProgressFn | None = None,
        is_cancelled: CancelFn | None = None,
    ) -> dict[str, Any]:
        _emit_progress(progress, "searching", 10, "Searching Everything")
        _raise_if_cancelled(is_cancelled)
        candidates = self._search_rank_extract(topic, max_candidates=max_candidates)
        _raise_if_cancelled(is_cancelled)
        return self._bundle_with_candidates(
            topic,
            candidates,
            scope=scope,
            save=save,
            provider=provider,
            analysis_mode=analysis_mode,
            tool_use=tool_use,
            progress=progress,
            is_cancelled=is_cancelled,
        )

    def find_bundle_selected(
        self,
        topic: str,
        *,
        selected_candidates: list[dict[str, Any]],
        scope: str = "all",
        save: bool = True,
        provider: str = "copilot",
        analysis_mode: str = "find-bundle",
        tool_use: bool = False,
        progress: ProgressFn | None = None,
        is_cancelled: CancelFn | None = None,
    ) -> dict[str, Any]:
        _emit_progress(progress, "extracting", 30, "Extracting selected files")
        _raise_if_cancelled(is_cancelled)
        candidates = self._extract_selected_candidates(selected_candidates)
        _raise_if_cancelled(is_cancelled)
        return self._bundle_with_candidates(
            topic,
            candidates,
            scope=scope,
            save=save,
            provider=provider,
            analysis_mode=analysis_mode,
            tool_use=tool_use,
            progress=progress,
            is_cancelled=is_cancelled,
        )

    def _bundle_with_candidates(
        self,
        topic: str,
        candidates: list[dict[str, Any]],
        *,
        scope: str,
        save: bool,
        provider: str,
        analysis_mode: str,
        tool_use: bool,
        progress: ProgressFn | None = None,
        is_cancelled: CancelFn | None = None,
    ) -> dict[str, Any]:
        _emit_progress(progress, "building_packet", 55, "Building evidence packet")
        _raise_if_cancelled(is_cancelled)
        packet = _build_research_packet(
            "find-bundle", topic, candidates, scope, analysis_mode=analysis_mode
        )
        warnings: list[str] = []
        try:
            _emit_progress(progress, "calling_provider", 65, "Calling provider")
            bundle = self.provider_router.analyze(
                packet,
                provider=provider,
                analysis_mode=analysis_mode,
                tool_use=tool_use,
            )
            _emit_progress(progress, "validating_response", 80, "Validating provider response")
        except Exception as exc:
            warnings.append(f"{provider} failed: {exc}")
            bundle = _fallback_bundle(topic, candidates)

        bundle_provider = str(bundle.get("provider") or provider)
        result = {
            "mode": "find-bundle",
            "topic": topic,
            "provider": bundle_provider,
            "model": str(bundle.get("model") or ""),
            "ai_applied": _ai_applied(bundle_provider),
            "provider_status": _provider_status(bundle_provider),
            "analysis_mode": analysis_mode,
            "tool_use": tool_use,
            "bundle_title": str(bundle.get("bundle_title") or topic),
            "core_files": _list_of_dicts(bundle.get("core_files")),
            "supporting_files": _list_of_dicts(bundle.get("supporting_files")),
            "duplicates_or_versions": _list_of_dicts(bundle.get("duplicates_or_versions")),
            "missing_or_gap_hints": _list_of_dicts(bundle.get("missing_or_gap_hints")),
            "next_actions": _string_list(bundle.get("next_actions")),
            "sources": [_source_payload(candidate) for candidate in candidates],
            "saved_markdown": "",
            "saved_json": "",
            "warnings": warnings
            + _string_list(bundle.get("provider_warnings"))
            + _string_list(bundle.get("warnings")),
        }
        result.update(_analysis_extras(bundle))
        if save:
            _emit_progress(progress, "saving", 85, "Saving result")
            paths = self._save_result("bundles", "bundle", result)
            result.update(paths)
        return result

    def preview_candidates(
        self,
        prompt: str,
        *,
        mode: str = "ask",
        scope: str = "all",
        max_candidates: int = 10,
    ) -> dict[str, Any]:
        _ = scope
        queries = generate_search_queries(prompt)
        raw: list[dict[str, Any]] = []
        warnings: list[str] = []
        for query in queries:
            try:
                raw.extend(self.search(query, 50))
            except Exception as exc:
                warnings.append(f"search failed for {query}: {exc}")
        ranked = rank_candidates(dedupe_candidates(raw), queries)
        candidates = []
        for candidate in ranked[: max(1, max_candidates)]:
            payload = _candidate_payload(candidate, mode=mode, prompt=prompt)
            candidates.append(payload)
        return {
            "mode": mode,
            "prompt": prompt,
            "candidates": candidates,
            "warnings": warnings,
        }

    def _search_rank_extract(self, text: str, *, max_candidates: int) -> list[dict[str, Any]]:
        queries = generate_search_queries(text)
        raw: list[dict[str, Any]] = []
        for query in queries:
            raw.extend(self.search(query, 50))
        ranked = rank_candidates(dedupe_candidates(raw), queries)
        return self._extract_selected_candidates(
            ranked[: min(max_candidates, MAX_EXTRACTED_SOURCES)],
            allow_empty=True,
        )

    def _extract_selected_candidates(
        self,
        selected_candidates: list[dict[str, Any]],
        *,
        allow_empty: bool = False,
    ) -> list[dict[str, Any]]:
        if not selected_candidates and not allow_empty:
            raise ValueError("selected_candidates must not be empty")
        extracted: list[dict[str, Any]] = []
        for candidate in selected_candidates:
            if _should_skip_candidate(candidate):
                continue
            path = Path(str(candidate.get("path") or ""))
            try:
                extraction = self.extract(path)
            except Exception as exc:
                enriched = dict(candidate)
                enriched["extraction_status"] = "limited"
                enriched["extraction_reason"] = f"{type(exc).__name__}: {exc}"
                enriched["text"] = ""
                extracted.append(enriched)
                continue
            text_value = str(extraction.get("text") or "")
            text_value = _clean_extracted_text(text_value)
            if contains_sensitive_pattern(text_value):
                skipped = dict(candidate)
                skipped["extraction_status"] = "skipped"
                skipped["reason"] = "credential pattern"
                extracted.append(skipped)
                continue
            enriched = dict(candidate)
            enriched["extraction_status"] = str(extraction.get("status") or "ok")
            enriched["extraction_reason"] = str(extraction.get("reason") or "")
            enriched["text"] = text_value
            extracted.append(enriched)
        return extracted

    def _save_result(self, folder: str, suffix: str, result: dict[str, Any]) -> dict[str, str]:
        target = self.output_root / folder
        target.mkdir(parents=True, exist_ok=True)
        stem = f"{self.timestamp()}-{suffix}"
        json_path = target / f"{stem}.json"
        markdown_path = target / f"{stem}.md"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        markdown_path.write_text(_render_markdown(result), encoding="utf-8")
        return {"saved_markdown": str(markdown_path), "saved_json": str(json_path)}


def _default_search(query: str, limit: int = 50) -> list[dict[str, Any]]:
    return search_everything(query, limit=limit)


def _default_copilot(packet: dict[str, Any]) -> dict[str, Any]:
    endpoint = os.getenv("LOCAL_RESEARCH_COPILOT_ENDPOINT") or DEFAULT_COPILOT_ENDPOINT
    token = os.getenv("LOCAL_WIKI_COPILOT_TOKEN") or ""
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["x-ai-proxy-token"] = token
    body = {
        "model": DEFAULT_COPILOT_MODEL,
        "sensitivity": "internal",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a local document research assistant. Answer only from the "
                    "provided file packets. Separate confirmed findings from assumptions. "
                    "Always cite source_path. Return one JSON object only."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(packet, ensure_ascii=False, separators=(",", ":")),
            },
        ],
    }
    response = requests.post(endpoint, json=body, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    envelope = response.json()
    text = envelope.get("result", {}).get("text", "")
    if not isinstance(text, str):
        raise ValueError("Copilot response missing result.text")
    return _parse_json_object(text)


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.I)
    if match:
        stripped = match.group(1).strip()
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("Copilot response was not a JSON object")
    return parsed


def _probe_everything(base_url: str) -> dict[str, str]:
    try:
        search_everything("*.md", limit=1, base_url=base_url, timeout_sec=3)
    except Exception as exc:
        return {"status": "unavailable", "base_url": base_url, "error": str(exc)}
    return {"status": "ok", "base_url": base_url}


def _probe_search(search: SearchFn, base_url: str) -> dict[str, str]:
    try:
        search("*.md", 1)
    except Exception as exc:
        return {"status": "unavailable", "base_url": base_url, "error": str(exc)}
    return {"status": "ok", "base_url": base_url}


def _probe_copilot(endpoint: str) -> dict[str, str]:
    health_url = endpoint.rsplit("/", 1)[0] + "/health"
    try:
        response = requests.get(health_url, timeout=3)
        response.raise_for_status()
    except Exception as exc:
        return {"status": "unavailable", "base_url": endpoint, "error": str(exc)}
    return {"status": "ok", "base_url": endpoint.rsplit("/api/ai/chat", 1)[0]}


def _build_research_packet(
    mode: str,
    prompt: str,
    candidates: list[dict[str, Any]],
    scope: str,
    *,
    analysis_mode: str = "",
) -> dict[str, Any]:
    source_packets = []
    for candidate in candidates:
        path = str(candidate.get("path") or "")
        extension = str(candidate.get("extension") or Path(path).suffix)
        extraction_reason = str(candidate.get("extraction_reason") or candidate.get("reason") or "")
        source_packets.append(
            {
                "source_path": path,
                "name": str(candidate.get("name") or Path(path).name),
                "extension": extension,
                "modified_at": str(
                    candidate.get("modifiedAt")
                    or candidate.get("modified_at")
                    or candidate.get("date_modified")
                    or ""
                ),
                "extraction_status": str(candidate.get("extraction_status") or ""),
                "extraction_reason": extraction_reason,
                "excerpt": str(candidate.get("text") or "")[:MAX_PACKET_CHARS],
            }
        )
    return {
        "job": f"local_research_{mode}",
        "mode": mode,
        "analysis_mode": analysis_mode or mode,
        "prompt": prompt,
        "scope": scope,
        "rules": {
            "return_json_only": True,
            "language": "ko",
            "cite_source_path": True,
            "do_not_invent_facts": True,
        },
        "sources": source_packets,
    }


def _candidate_score(candidate: dict[str, Any], query_tokens: list[str]) -> int:
    path = str(candidate.get("path") or "")
    name = str(candidate.get("name") or Path(path).name)
    haystack_name = name.lower()
    haystack_path = path.lower()
    score = 0
    for token in query_tokens:
        normalized = token.lower()
        if normalized in haystack_name:
            score += 10
        if normalized in haystack_path:
            score += 4
        score += _exact_entity_match_score(token, name, path)
    ext = str(candidate.get("extension") or Path(path).suffix).lower()
    if ext in SUPPORTED_EXTENSIONS:
        score += 3
    score += _recency_score(candidate)
    return score


def _exact_entity_match_score(token: str, name: str, path: str) -> int:
    normalized_token = _entity_key(token)
    if len(normalized_token) < 6:
        return 0
    stem_key = _entity_key(Path(name).stem)
    name_key = _entity_key(name)
    path_key = _entity_key(path)
    if normalized_token == stem_key:
        return 80
    if normalized_token in name_key:
        return 65
    if normalized_token in path_key:
        return 45
    return 0


def _entity_key(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", "", str(value).lower())


def _recency_score(candidate: dict[str, Any]) -> int:
    timestamp = _modified_timestamp(candidate)
    if timestamp is None:
        return 0
    age_days = (datetime.now().timestamp() - timestamp) / 86_400
    if age_days <= 7:
        return 6
    if age_days <= 30:
        return 4
    if age_days <= 365:
        return 2
    return 1


def _modified_timestamp(candidate: dict[str, Any]) -> float | None:
    raw = str(
        candidate.get("modifiedAt")
        or candidate.get("modified_at")
        or candidate.get("date_modified")
        or ""
    ).strip()
    if not raw:
        return None
    try:
        numeric = float(raw)
    except ValueError:
        numeric = 0.0
    if numeric > 0:
        if numeric > 10_000_000_000_000_000:
            return (numeric - 116_444_736_000_000_000) / 10_000_000
        return numeric
    normalized = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt).timestamp()
        except ValueError:
            continue
    return None


def _ranked_candidate(candidate: dict[str, Any], query_tokens: list[str]) -> dict[str, Any]:
    ranked = dict(candidate)
    base_score = _candidate_score(candidate, query_tokens)
    penalty = _path_penalty(candidate)
    status = _candidate_status(candidate)
    status_penalty = 25 if status == "missing" else 0
    score = base_score - penalty - status_penalty
    reasons = _rank_reasons(candidate, query_tokens, status=status, penalty=penalty)
    ranked["score"] = score
    ranked["rank_reason"] = "; ".join(reasons) if reasons else "metadata match"
    ranked["status"] = status
    ranked["selected_by_default"] = status == "available" and penalty == 0 and score > 0
    return ranked


def _annotate_duplicate_groups(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        key = _duplicate_group_key(candidate)
        if key:
            groups.setdefault(key, []).append(candidate)
    duplicate_keys = {key for key, items in groups.items() if len(items) > 1}
    if not duplicate_keys:
        return candidates
    annotated: list[dict[str, Any]] = []
    for candidate in candidates:
        key = _duplicate_group_key(candidate)
        if key in duplicate_keys:
            updated = dict(candidate)
            updated["duplicate_group"] = key
            reason = str(updated.get("rank_reason") or "")
            if "duplicate/version group" not in reason:
                updated["rank_reason"] = (
                    f"{reason}; duplicate/version group" if reason else "duplicate/version group"
                )
            annotated.append(updated)
        else:
            annotated.append(candidate)
    return annotated


def _duplicate_group_key(candidate: dict[str, Any]) -> str:
    path = str(candidate.get("path") or "")
    name = str(candidate.get("name") or Path(path).name)
    stem = Path(name).stem.lower()
    stem = re.sub(r"[\s._-]+", " ", stem)
    stem = re.sub(r"\b(v|ver|version)\s*\d+[a-z]?\b", "", stem)
    stem = re.sub(r"\b\d{4}[-_ ]?\d{2}[-_ ]?\d{2}\b", "", stem)
    stem = re.sub(r"\b\d{8}\b", "", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem if len(stem) >= 4 else ""


def _candidate_status(candidate: dict[str, Any]) -> str:
    path = str(candidate.get("path") or "")
    if not path:
        return "missing"
    try:
        return "available" if Path(path).exists() else "missing"
    except OSError:
        return "limited"


def _rank_reasons(
    candidate: dict[str, Any],
    query_tokens: list[str],
    *,
    status: str,
    penalty: int,
) -> list[str]:
    path = str(candidate.get("path") or "")
    name = str(candidate.get("name") or Path(path).name)
    lower_name = name.lower()
    lower_path = path.lower()
    reasons: list[str] = []
    if any(token.lower() in lower_name for token in query_tokens):
        reasons.append("filename match")
    if any(token.lower() in lower_path for token in query_tokens):
        reasons.append("path match")
    if any(_exact_entity_match_score(token, name, path) >= 45 for token in query_tokens):
        reasons.append("exact filename/entity match")
    extension = str(candidate.get("extension") or Path(path).suffix).lower()
    if extension in SUPPORTED_EXTENSIONS:
        reasons.append(f"supported extension {extension}")
    if str(candidate.get("modifiedAt") or candidate.get("modified_at") or ""):
        reasons.append("has modified time")
    if candidate.get("size") not in {None, ""}:
        reasons.append("has size")
    if _recency_score(candidate) >= 2:
        reasons.append("recent modification")
    if penalty:
        reasons.append("low-value path penalty")
    if status == "missing":
        reasons.append("missing file")
    return reasons


def _path_penalty(candidate: dict[str, Any]) -> int:
    normalized = str(candidate.get("path") or "").replace("/", "\\").lower()
    penalty = sum(10 for marker in LOW_VALUE_PATH_MARKERS if marker in normalized)
    penalty += sum(20 for marker in SECRET_NAME_MARKERS if marker in normalized)
    return penalty


def _is_excluded_candidate(candidate: dict[str, Any]) -> bool:
    if str(candidate.get("source") or "") != "everything-http":
        return False
    normalized = str(candidate.get("path") or "").replace("/", "\\").lower()
    return any(marker in normalized for marker in EXCLUDED_PATH_MARKERS)


def _should_skip_candidate(candidate: dict[str, Any]) -> bool:
    path = str(candidate.get("path") or "")
    normalized = path.lower()
    if _is_excluded_candidate(candidate):
        return True
    if any(marker in normalized for marker in SECRET_NAME_MARKERS):
        return True
    extension = str(candidate.get("extension") or Path(path).suffix).lower()
    return extension not in SUPPORTED_EXTENSIONS


def _candidate_payload(candidate: dict[str, Any], *, mode: str, prompt: str) -> dict[str, Any]:
    path = str(candidate.get("path") or "")
    return {
        "candidate_id": _candidate_id(candidate, mode=mode, prompt=prompt),
        "path": path,
        "name": str(candidate.get("name") or Path(path).name),
        "extension": str(candidate.get("extension") or Path(path).suffix).lower(),
        "size": candidate.get("size"),
        "modified_at": str(
            candidate.get("modifiedAt")
            or candidate.get("modified_at")
            or candidate.get("date_modified")
            or ""
        ),
        "score": int(candidate.get("score") or 0),
        "rank_reason": str(candidate.get("rank_reason") or ""),
        "selected_by_default": bool(candidate.get("selected_by_default")),
        "status": str(candidate.get("status") or _candidate_status(candidate)),
    }


def _candidate_id(candidate: dict[str, Any], *, mode: str, prompt: str) -> str:
    normalized_path = str(candidate.get("path") or "").replace("/", "\\").lower()
    source = f"{mode}\n{prompt.strip().lower()}\n{normalized_path}"
    return sha1(source.encode("utf-8")).hexdigest()[:16]


def _source_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    path = str(candidate.get("path") or "")
    return {
        "path": path,
        "name": str(candidate.get("name") or Path(path).name),
        "extension": str(candidate.get("extension") or Path(path).suffix).lower(),
        "size": candidate.get("size"),
        "modified_at": str(
            candidate.get("modifiedAt")
            or candidate.get("modified_at")
            or candidate.get("date_modified")
            or ""
        ),
        "extraction_status": str(candidate.get("extraction_status") or ""),
        "reason": str(candidate.get("reason") or candidate.get("extraction_reason") or ""),
        "snippet": str(candidate.get("text") or "")[:500],
    }


def _clean_extracted_text(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    leading_window = "\n".join(lines[:30]).lower()
    if not any(
        marker in leading_window
        for marker in ("uvx", "markitdown", "nativecommanderror", "categoryinfo", "ps-script")
    ):
        return text
    noise_end = 0
    for index, line in enumerate(lines[:50]):
        if _is_leading_conversion_noise_line(line):
            noise_end = index + 1
            continue
        break
    if noise_end == 0 or noise_end >= len(lines):
        return text
    return "\n".join(lines[noise_end:]).lstrip()


def _is_leading_conversion_noise_line(line: str) -> bool:
    stripped = line.strip()
    lower = stripped.lower()
    if not stripped:
        return True
    markers = (
        "uvx",
        "markitdown",
        "nativecommanderror",
        "categoryinfo",
        "fullyqualifiederrorid",
        "remoteexception",
        "ps-script",
        "appdata\\local\\temp",
    )
    if any(marker in lower for marker in markers):
        return True
    return stripped.startswith(("+", "~")) or lower.startswith(("at line", "위치 "))


def _fallback_findings(candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for candidate in candidates[:5]:
        path = str(candidate.get("path") or "")
        if not path:
            continue
        findings.append({"text": "관련 후보 파일입니다.", "source_path": path})
    return findings


def _fallback_bundle(topic: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    sources = [
        {"path": str(candidate.get("path") or ""), "role": "candidate"} for candidate in candidates
    ]
    return {
        "bundle_title": topic,
        "core_files": sources[:5],
        "supporting_files": sources[5:],
        "duplicates_or_versions": [],
        "missing_or_gap_hints": [{"hint": "Copilot 분석 실패로 누락 판단은 수동 확인 필요"}],
        "next_actions": ["core_files 후보부터 원본을 확인하세요."],
    }


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Local Research Result",
        "",
        "## Request",
        str(result.get("question") or result.get("topic") or ""),
        "",
        "## Short Answer",
        str(result.get("short_answer") or result.get("bundle_title") or ""),
        "",
        "## Findings",
    ]
    lines.extend(f"- {_compact_item(item)}" for item in result.get("findings", []) or [])
    lines.extend(f"- core: {_compact_item(item)}" for item in result.get("core_files", []) or [])
    lines.extend(
        f"- supporting: {_compact_item(item)}" for item in result.get("supporting_files", []) or []
    )
    lines.extend(["", "## Sources"])
    for source in result.get("sources", []) or []:
        lines.append(f"- {source.get('path', '')}")
    lines.extend(["", "## Gaps"])
    lines.extend(f"- {_compact_item(item)}" for item in result.get("gaps", []) or [])
    lines.extend(
        f"- {_compact_item(item)}" for item in result.get("missing_or_gap_hints", []) or []
    )
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in result.get("next_actions", []) or [])
    lines.extend(["", "## Warnings"])
    lines.extend(f"- {item}" for item in result.get("warnings", []) or [])
    lines.append("")
    return "\n".join(lines)


def _ai_applied(provider: str) -> bool:
    return provider.lower() not in {"", "fallback", "deterministic"}


def _provider_status(provider: str) -> str:
    return "ai" if _ai_applied(provider) else "fallback"


def _analysis_extras(payload: dict[str, Any]) -> dict[str, Any]:
    reserved = {
        "mode",
        "question",
        "topic",
        "provider",
        "model",
        "analysis_mode",
        "tool_use",
        "short_answer",
        "findings",
        "sources",
        "gaps",
        "next_actions",
        "saved_markdown",
        "saved_json",
        "warnings",
        "provider_warnings",
        "bundle_title",
        "core_files",
        "supporting_files",
        "duplicates_or_versions",
        "missing_or_gap_hints",
    }
    return {key: value for key, value in payload.items() if key not in reserved}


def _compact_item(item: Any) -> str:
    if isinstance(item, dict):
        if "text" in item and "source_path" in item:
            return f"{item['text']} ({item['source_path']})"
        if "path" in item and "role" in item:
            return f"{item['path']} - {item['role']}"
        return json.dumps(item, ensure_ascii=False)
    return str(item)


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _emit_progress(progress: ProgressFn | None, stage: str, percent: int, message: str) -> None:
    if progress is not None:
        progress(stage, percent, message)


def _raise_if_cancelled(is_cancelled: CancelFn | None) -> None:
    if is_cancelled is not None and is_cancelled():
        raise ResearchCancelled("research job was cancelled")


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")

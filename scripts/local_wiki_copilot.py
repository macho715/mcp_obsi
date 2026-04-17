from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests

DEFAULT_COPILOT_ENDPOINT = "http://127.0.0.1:3010/api/ai/chat"
DEFAULT_COPILOT_MODEL = "github-copilot/gpt-5-mini"
DEFAULT_SENSITIVITY = "internal"
DEFAULT_TAGS = ("local-wiki", "auto-ingest")
MAX_EXCERPT_CHARS = 4_000
MAX_STRUCTURE_HINTS = 10
REQUEST_TIMEOUT_SECONDS = 120


class CopilotNormalizationError(RuntimeError):
    """Raised when standalone Copilot normalization cannot produce valid JSON."""


def build_copilot_packet(
    *,
    source_path: str | Path,
    source_ext: str,
    extraction: dict[str, Any],
    max_excerpt_chars: int = MAX_EXCERPT_CHARS,
) -> dict[str, Any]:
    text = str(extraction.get("text") or "")
    excerpt = text[: max(0, max_excerpt_chars)]
    return {
        "job": "local_file_wiki_normalization",
        "source_path": str(source_path),
        "source_ext": source_ext,
        "extraction_status": str(extraction.get("status") or "ok"),
        "extraction_reason": str(extraction.get("reason") or ""),
        "text_length": len(text),
        "excerpt": excerpt,
        "structure_hints": _structure_hints(text),
        "rules": {
            "return_json_only": True,
            "language": "ko",
            "note_status": "draft",
            "required_keys": [
                "title",
                "summary",
                "key_facts",
                "extracted_structure",
                "topics",
                "entities",
                "projects",
                "tags",
                "confidence",
            ],
        },
    }


def build_copilot_request(
    packet: dict[str, Any],
    *,
    model: str = DEFAULT_COPILOT_MODEL,
    sensitivity: str = DEFAULT_SENSITIVITY,
) -> dict[str, Any]:
    normalized_sensitivity = sensitivity.strip().lower()
    if normalized_sensitivity == "secret":
        raise ValueError("secret sensitivity requires local-only inference and is not supported")
    return {
        "model": model,
        "sensitivity": normalized_sensitivity,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You normalize local file extraction packets into concise Obsidian wiki "
                    "draft metadata. Return one JSON object only. Do not include Markdown, "
                    "code fences, or commentary."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(packet, ensure_ascii=False, separators=(",", ":")),
            },
        ],
    }


def parse_copilot_normalization(text: str) -> dict[str, Any]:
    candidate = _strip_json_fence(text)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise CopilotNormalizationError("Copilot response was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise CopilotNormalizationError("Copilot response must be a JSON object")

    title = _clean_string(payload.get("title"))
    summary = _clean_string(payload.get("summary"))
    if not title:
        raise CopilotNormalizationError("Copilot response missing title")
    if not summary:
        raise CopilotNormalizationError("Copilot response missing summary")

    tags = _string_list(payload.get("tags"))
    for tag in DEFAULT_TAGS:
        if tag not in tags:
            tags.append(tag)

    return {
        "title": title,
        "summary": summary,
        "key_facts": _string_list(payload.get("key_facts")),
        "extracted_structure": _string_list(payload.get("extracted_structure")),
        "topics": _string_list(payload.get("topics")),
        "entities": _string_list(payload.get("entities")),
        "projects": _string_list(payload.get("projects")),
        "tags": tags,
        "confidence": _clean_string(payload.get("confidence")) or "medium",
    }


def normalize_with_copilot_proxy(
    packet: dict[str, Any],
    *,
    endpoint: str | None = None,
    auth_token: str | None = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
    model: str = DEFAULT_COPILOT_MODEL,
) -> dict[str, Any]:
    target = endpoint or os.getenv("LOCAL_WIKI_COPILOT_ENDPOINT") or DEFAULT_COPILOT_ENDPOINT
    token = auth_token or os.getenv("LOCAL_WIKI_COPILOT_TOKEN") or ""
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["x-ai-proxy-token"] = token

    request_body = build_copilot_request(packet, model=model)
    try:
        response = requests.post(target, json=request_body, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CopilotNormalizationError(f"standalone proxy request failed: {exc}") from exc

    try:
        envelope = response.json()
    except ValueError as exc:
        raise CopilotNormalizationError("standalone proxy response was not JSON") from exc
    if not isinstance(envelope, dict):
        raise CopilotNormalizationError("standalone proxy response must be a JSON object")

    result = envelope.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("text"), str):
        raise CopilotNormalizationError("standalone proxy response missing result.text")

    normalized = parse_copilot_normalization(result["text"])
    normalized["normalizer"] = "copilot"
    normalized["copilot_metadata"] = {
        "route": envelope.get("route"),
        "model": result.get("model"),
        "provider": result.get("provider"),
        "guard": envelope.get("guard"),
        "usage": result.get("usage"),
    }
    return normalized


def _structure_hints(text: str) -> list[str]:
    hints: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#") or stripped.lower().startswith("sheet:"):
            hints.append(stripped[:240])
        if len(hints) >= MAX_STRUCTURE_HINTS:
            break
    return hints


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.I)
    return match.group(1).strip() if match else stripped


def _clean_string(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        return []

    cleaned: list[str] = []
    for item in items:
        text = _clean_string(item)
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned

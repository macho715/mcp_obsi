"""
Shared Ollama adapter for KB skills.

All three KB skills (obsidian-ingest, obsidian-query, obsidian-lint) call this
module so that model names, endpoint, timeout, and error handling stay identical.

Usage
-----
    from scripts.ollama_kb import generate, MODELS

    response = generate(messages=[{"role": "user", "content": "..."}])
    response = generate(messages=[...], model=MODELS["light"])
"""

from __future__ import annotations

import os
import re
from typing import Any

import requests

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))

MODELS: dict[str, str] = {
    "primary": "gemma4:e4b",
    "light": "gemma4:e2b",
}

DEFAULT_MODEL: str = MODELS["primary"]


def normalize_ascii_slug(value: str, *, fallback: str = "untitled") -> str:
    """Normalize free-form or model-produced slugs to safe ASCII path segments."""
    cleaned = value.strip().lower().replace(" ", "-").replace("#", "").replace("/", "-")
    cleaned = "".join(c if c.isascii() and (c.isalnum() or c in "-_") else "-" for c in cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-_")
    return cleaned[:48] or fallback


def generate(
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    base_url: str = OLLAMA_BASE_URL,
    timeout: int = OLLAMA_TIMEOUT,
    options: dict[str, Any] | None = None,
) -> str:
    """Call Ollama /api/chat and return the assistant message content.

    Raises
    ------
    requests.HTTPError
        When Ollama returns a non-2xx status.
    requests.ConnectionError
        When Ollama is not reachable (server not running).
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if options:
        payload["options"] = options

    resp = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def health_check(base_url: str = OLLAMA_BASE_URL) -> bool:
    """Return True if Ollama is reachable."""
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def available_models(base_url: str = OLLAMA_BASE_URL) -> list[str]:
    """Return list of model names currently available in Ollama."""
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except requests.RequestException:
        return []

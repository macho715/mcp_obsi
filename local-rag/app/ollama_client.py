from __future__ import annotations

import os
from typing import Any

import requests


def resolve_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def resolve_default_model() -> str:
    return os.getenv("LOCAL_RAG_MODEL", "gemma4:e4b").strip() or "gemma4:e4b"


def fetch_ollama_tags(base_url: str | None = None, timeout_s: float = 5.0) -> dict[str, Any]:
    target = (base_url or resolve_ollama_base_url()).rstrip("/")
    response = requests.get(f"{target}/api/tags", timeout=timeout_s)
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def generate_chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    base_url: str | None = None,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    target = (base_url or resolve_ollama_base_url()).rstrip("/")
    response = requests.post(
        f"{target}/api/chat",
        json={
            "model": model or resolve_default_model(),
            "messages": messages,
            "stream": False,
        },
        timeout=timeout_s,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}

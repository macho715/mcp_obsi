from __future__ import annotations

import os
import time
from typing import Any

import requests
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.ollama_client import (
    fetch_ollama_tags,
    generate_chat_completion,
    resolve_default_model,
)
from app.retrieval import count_documents, search_documents

app = FastAPI(title="local-rag", version="0.1.0")


class LocalRagUpstreamError(Exception):
    def __init__(self, error_code: str, detail: str, status_code: int = 502) -> None:
        super().__init__(detail)
        self.error_code = error_code
        self.detail = detail
        self.status_code = status_code


class ChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=8000)


class ChatLocalRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=12)
    scope: list[str] = Field(default_factory=list, max_length=20)
    mode: str = "chat"
    routeHint: str = "local"
    model: str | None = Field(default=None, max_length=200)


def resolve_shared_secret() -> str:
    return os.getenv("LOCAL_RAG_SHARED_SECRET", "").strip()


def _is_loopback_client(request: Request) -> bool:
    client_host = request.client.host if request.client else ""
    return client_host in {"127.0.0.1", "::1", "localhost", "testclient"}


def require_local_rag_auth(request: Request, token: str | None) -> None:
    expected_secret = resolve_shared_secret()
    if expected_secret and token != expected_secret:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "LOCAL_RAG_UNAUTHORIZED",
                "detail": "Missing or invalid local-rag token.",
            },
        )
    if not expected_secret and not _is_loopback_client(request):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "LOCAL_RAG_UNAUTHORIZED",
                "detail": "Remote callers require a local-rag token.",
            },
        )


def _model_names(payload: dict[str, Any]) -> set[str]:
    models = payload.get("models", [])
    if not isinstance(models, list):
        return set()
    names: set[str] = set()
    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            names.add(name.strip())
    return names


def get_health_payload() -> dict[str, Any]:
    model_name = resolve_default_model()
    document_count = count_documents()
    try:
        tags_payload = fetch_ollama_tags()
        model_names = _model_names(tags_payload)
        return {
            "status": "ok",
            "api": "up",
            "ollama": "up",
            "vectorstore": "filesystem",
            "documents": document_count,
            "model": model_name,
            "modelLoaded": model_name in model_names,
        }
    except Exception:  # pragma: no cover - exercised by API callers
        return {
            "status": "down",
            "api": "up",
            "ollama": "down",
            "vectorstore": "filesystem",
            "documents": document_count,
            "model": model_name,
            "error": "ollama_unavailable",
        }


def run_chat_local(
    messages: list[ChatMessage],
    scope: list[str],
    mode: str,
    route_hint: str,
    model: str | None = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    query_text = " ".join(item.content for item in messages if item.role == "user").strip()
    sources = search_documents(query_text)
    message_payload = [{"role": item.role, "content": item.content} for item in messages]
    if sources:
        retrieval_context = "\n\n".join(
            f"Source: {item['file']}\nSnippet: {item['snippet']}" for item in sources
        )
        message_payload.insert(
            0,
            {
                "role": "system",
                "content": (
                    "Use the retrieved local knowledge snippets when they are relevant. "
                    "If they are not relevant, answer from the user prompt only.\n\n"
                    f"{retrieval_context}"
                ),
            },
        )
    try:
        completion = generate_chat_completion(message_payload, model=model)
    except requests.RequestException as exc:
        raise LocalRagUpstreamError("OLLAMA_UNAVAILABLE", str(exc), status_code=503) from exc
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    message = completion.get("message", {})
    text = ""
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            text = content
    if not text.strip():
        raise LocalRagUpstreamError(
            "OLLAMA_BAD_RESPONSE",
            "Upstream response did not include message content.",
            status_code=502,
        )
    return {
        "text": text,
        "model": (
            completion.get("model")
            if isinstance(completion.get("model"), str)
            else resolve_default_model()
        ),
        "provider": "local-rag",
        "sources": sources,
        "riskFlags": [],
        "latencyMs": latency_ms,
        "scope": scope,
        "mode": mode,
        "routeHint": route_hint,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return get_health_payload()


@app.post("/api/internal/ai/chat-local")
def chat_local(
    request: Request,
    payload: ChatLocalRequest,
    x_local_rag_token: str | None = Header(default=None, alias="x-local-rag-token"),
) -> dict[str, Any]:
    require_local_rag_auth(request, x_local_rag_token)
    try:
        result = run_chat_local(
            payload.messages,
            payload.scope,
            payload.mode,
            payload.routeHint,
            payload.model,
        )
    except LocalRagUpstreamError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.error_code, "detail": exc.detail},
        ) from exc
    return {
        "text": result["text"],
        "model": result["model"],
        "provider": result["provider"],
        "sources": result["sources"],
        "riskFlags": result["riskFlags"],
        "latencyMs": result["latencyMs"],
    }


@app.get("/api/internal/ai/chat-local/ready")
def chat_local_ready(
    request: Request,
    x_local_rag_token: str | None = Header(default=None, alias="x-local-rag-token"),
) -> dict[str, Any]:
    require_local_rag_auth(request, x_local_rag_token)
    return {"status": "ok"}

import os

import pytest
from app.retrieval import clear_runtime_cache, get_retrieval_cache, search_documents
from fastapi.testclient import TestClient

from app.main import ChatMessage, LocalRagUpstreamError, app, run_chat_local


def test_health_reports_ollama_ready(monkeypatch):
    def fake_health() -> dict[str, object]:
        return {
            "status": "ok",
            "api": "up",
            "ollama": "up",
            "vectorstore": "disabled",
            "documents": 0,
        }

    monkeypatch.setattr("app.main.get_health_payload", fake_health)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "api": "up",
        "ollama": "up",
        "vectorstore": "disabled",
        "documents": 0,
    }


def test_chat_local_returns_text_and_provider(monkeypatch):
    monkeypatch.delenv("LOCAL_RAG_SHARED_SECRET", raising=False)

    def fake_chat(_messages, _scope, _mode, _route_hint, _model=None):
        return {
            "text": "local answer",
            "model": "gemma4:e4b",
            "provider": "local-rag",
            "sources": [],
            "riskFlags": [],
            "latencyMs": 12,
        }

    monkeypatch.setattr("app.main.run_chat_local", fake_chat)
    client = TestClient(app)

    response = client.post(
        "/api/internal/ai/chat-local",
        json={
            "messages": [{"role": "user", "content": "hello"}],
            "scope": [],
            "mode": "chat",
            "routeHint": "local",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "text": "local answer",
        "model": "gemma4:e4b",
        "provider": "local-rag",
        "sources": [],
        "riskFlags": [],
        "latencyMs": 12,
    }


def test_chat_local_rejects_missing_token_when_secret_configured(monkeypatch):
    monkeypatch.setenv("LOCAL_RAG_SHARED_SECRET", "test-secret")
    monkeypatch.setattr(
        "app.main.run_chat_local",
        lambda *_args: {
            "text": "local answer",
            "model": "gemma4:e4b",
            "provider": "local-rag",
            "sources": [],
            "riskFlags": [],
            "latencyMs": 12,
        },
    )
    client = TestClient(app)

    response = client.post(
        "/api/internal/ai/chat-local",
        json={
            "messages": [{"role": "user", "content": "hello"}],
            "scope": [],
            "mode": "chat",
            "routeHint": "local",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "LOCAL_RAG_UNAUTHORIZED"


def test_chat_local_accepts_valid_token_when_secret_configured(monkeypatch):
    monkeypatch.setenv("LOCAL_RAG_SHARED_SECRET", "test-secret")
    monkeypatch.setattr(
        "app.main.run_chat_local",
        lambda *_args: {
            "text": "local answer",
            "model": "gemma4:e4b",
            "provider": "local-rag",
            "sources": [],
            "riskFlags": [],
            "latencyMs": 12,
        },
    )
    client = TestClient(app)

    response = client.post(
        "/api/internal/ai/chat-local",
        headers={"x-local-rag-token": "test-secret"},
        json={
            "messages": [{"role": "user", "content": "hello"}],
            "scope": [],
            "mode": "chat",
            "routeHint": "local",
        },
    )

    assert response.status_code == 200
    assert response.json()["text"] == "local answer"


def test_chat_local_ready_requires_valid_token_when_secret_configured(monkeypatch):
    monkeypatch.setenv("LOCAL_RAG_SHARED_SECRET", "test-secret")
    client = TestClient(app)

    response = client.get("/api/internal/ai/chat-local/ready")
    ok_response = client.get(
        "/api/internal/ai/chat-local/ready",
        headers={"x-local-rag-token": "test-secret"},
    )

    assert response.status_code == 401
    assert ok_response.status_code == 200
    assert ok_response.json() == {"status": "ok"}


def test_chat_local_rejects_remote_client_without_secret(monkeypatch):
    monkeypatch.delenv("LOCAL_RAG_SHARED_SECRET", raising=False)
    monkeypatch.setattr(
        "app.main.run_chat_local",
        lambda *_args: {
            "text": "local answer",
            "model": "gemma4:e4b",
            "provider": "local-rag",
            "sources": [],
            "riskFlags": [],
            "latencyMs": 12,
        },
    )
    client = TestClient(app, client=("203.0.113.10", 50000))

    response = client.post(
        "/api/internal/ai/chat-local",
        json={
            "messages": [{"role": "user", "content": "hello"}],
            "scope": [],
            "mode": "chat",
            "routeHint": "local",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "LOCAL_RAG_UNAUTHORIZED"


def test_run_chat_local_rejects_missing_upstream_text(monkeypatch):
    def fake_completion(_messages, model=None, **_kwargs):
        return {"model": "gemma4:e4b", "message": {}}

    monkeypatch.setattr("app.main.generate_chat_completion", fake_completion)

    with pytest.raises(LocalRagUpstreamError) as exc_info:
        run_chat_local(
            [ChatMessage(role="user", content="hello")],
            [],
            "chat",
            "local",
        )

    assert exc_info.value.error_code == "OLLAMA_BAD_RESPONSE"


def test_run_chat_local_forwards_model_override(monkeypatch):
    seen: dict[str, object] = {}

    def fake_completion(_messages, model=None, **_kwargs):
        seen["model"] = model
        return {
            "model": model or "gemma4:e4b",
            "message": {"content": "ok"},
        }

    monkeypatch.setattr("app.main.generate_chat_completion", fake_completion)

    result = run_chat_local(
        [ChatMessage(role="user", content="hello")],
        [],
        "chat",
        "local",
        "gemma4:e2b",
    )

    assert result["model"] == "gemma4:e2b"
    assert seen["model"] == "gemma4:e2b"


def test_run_chat_local_includes_sources_from_docs(tmp_path, monkeypatch):
    docs_dir = tmp_path / "wiki"
    docs_dir.mkdir()
    (docs_dir / "gemma.md").write_text(
        "# Gemma 4\n\nGemma 4 is a lightweight multimodal model from Google DeepMind.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LOCAL_RAG_DOCS_DIR", str(docs_dir))
    clear_runtime_cache()

    def fake_completion(_messages, model=None, **_kwargs):
        return {
            "model": "gemma4:e4b",
            "message": {"content": "Gemma 4 is a lightweight multimodal model."},
        }

    monkeypatch.setattr("app.main.generate_chat_completion", fake_completion)

    result = run_chat_local(
        [ChatMessage(role="user", content="Tell me about Gemma 4")],
        [],
        "chat",
        "local",
    )

    assert result["text"] == "Gemma 4 is a lightweight multimodal model."
    assert len(result["sources"]) == 1
    assert result["sources"][0]["file"] == "gemma.md"
    assert result["sources"][0]["source_path"] == "gemma.md"


def test_run_chat_local_skips_unreadable_docs(tmp_path, monkeypatch):
    docs_dir = tmp_path / "wiki"
    docs_dir.mkdir()
    (docs_dir / "bad.md").write_bytes(b"\xff\xfe\x00")
    (docs_dir / "good.md").write_text(
        "# Gemma\n\nGemma 4 has a 128K context window.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LOCAL_RAG_DOCS_DIR", str(docs_dir))
    clear_runtime_cache()

    def fake_completion(_messages, model=None, **_kwargs):
        return {
            "model": "gemma4:e4b",
            "message": {"content": "Gemma 4 has a 128K context window."},
        }

    monkeypatch.setattr("app.main.generate_chat_completion", fake_completion)

    result = run_chat_local(
        [ChatMessage(role="user", content="Tell me Gemma context window")],
        [],
        "chat",
        "local",
    )

    assert len(result["sources"]) == 1
    assert result["sources"][0]["file"] == "good.md"


def test_search_documents_reflects_changed_file_without_full_reset(tmp_path, monkeypatch):
    docs_dir = tmp_path / "wiki"
    docs_dir.mkdir()
    doc = docs_dir / "gemma.md"
    doc.write_text("# Gemma\n\nGemma 4 supports multimodal inputs.\n", encoding="utf-8")
    monkeypatch.setenv("LOCAL_RAG_DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("LOCAL_RAG_CACHE_PATH", str(tmp_path / "cache.json"))
    clear_runtime_cache()

    first = search_documents("multimodal")
    assert len(first) == 1

    doc.write_text("# Gemma\n\nGemma 4 supports long context windows.\n", encoding="utf-8")

    second = search_documents("context")
    assert len(second) == 1
    assert second[0]["source_path"] == "gemma.md"
    assert "context" in second[0]["snippet"].lower()


def test_search_documents_evicted_deleted_file(tmp_path, monkeypatch):
    docs_dir = tmp_path / "wiki"
    docs_dir.mkdir()
    doc = docs_dir / "gemma.md"
    doc.write_text("# Gemma\n\nGemma 4 supports multimodal inputs.\n", encoding="utf-8")
    monkeypatch.setenv("LOCAL_RAG_DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("LOCAL_RAG_CACHE_PATH", str(tmp_path / "cache.json"))
    clear_runtime_cache()

    assert len(search_documents("multimodal")) == 1

    doc.unlink()

    assert search_documents("multimodal") == []


def test_search_documents_cache_respects_larger_limit(tmp_path, monkeypatch):
    docs_dir = tmp_path / "wiki"
    docs_dir.mkdir()
    (docs_dir / "one.md").write_text("Gemma 4 multimodal overview", encoding="utf-8")
    (docs_dir / "two.md").write_text("Gemma 4 multimodal architecture", encoding="utf-8")
    monkeypatch.setenv("LOCAL_RAG_DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("LOCAL_RAG_CACHE_PATH", str(tmp_path / "cache.json"))
    monkeypatch.setenv("LOCAL_RAG_QUERY_CACHE_TTL_SEC", "60")
    clear_runtime_cache()

    first = search_documents("Gemma multimodal", limit=1)
    second = search_documents("Gemma multimodal", limit=2)

    assert len(first) == 1
    assert len(second) == 2


def test_search_documents_ignores_sidecar_write_failure(tmp_path, monkeypatch):
    docs_dir = tmp_path / "wiki"
    docs_dir.mkdir()
    (docs_dir / "one.md").write_text("Gemma 4 multimodal overview", encoding="utf-8")
    monkeypatch.setenv("LOCAL_RAG_DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("LOCAL_RAG_CACHE_PATH", str(tmp_path / "cache.json"))
    clear_runtime_cache()
    get_retrieval_cache()
    monkeypatch.setattr(
        "pathlib.Path.write_text",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("read-only")),
    )

    results = search_documents("Gemma multimodal", limit=1)

    assert len(results) == 1


def test_search_documents_discards_sidecar_from_other_docs_dir(tmp_path, monkeypatch):
    docs_dir_one = tmp_path / "wiki-one"
    docs_dir_two = tmp_path / "wiki-two"
    docs_dir_one.mkdir()
    docs_dir_two.mkdir()
    cache_path = tmp_path / "shared-cache.json"
    first_doc = docs_dir_one / "same.md"
    second_doc = docs_dir_two / "same.md"
    first_doc.write_text("Gemma 4 multimodal guide", encoding="utf-8")
    second_doc.write_text("Llama 3 deployment note", encoding="utf-8")
    first_stat = first_doc.stat()
    os.utime(second_doc, ns=(first_stat.st_atime_ns, first_stat.st_mtime_ns))

    monkeypatch.setenv("LOCAL_RAG_DOCS_DIR", str(docs_dir_one))
    monkeypatch.setenv("LOCAL_RAG_CACHE_PATH", str(cache_path))
    clear_runtime_cache()
    assert len(search_documents("Gemma", limit=1)) == 1

    monkeypatch.setenv("LOCAL_RAG_DOCS_DIR", str(docs_dir_two))
    clear_runtime_cache()
    results = search_documents("Gemma", limit=1)

    assert results == []

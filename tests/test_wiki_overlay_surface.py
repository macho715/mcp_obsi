import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from app.chatgpt_mcp_server import FastMCP, create_chatgpt_mcp_server
from app.models import MemoryCreate
from app.services.memory_store import MemoryStore


def test_chatgpt_profile_exposes_resources_and_prompts(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_chatgpt_mcp_server(store)

    resources = asyncio.run(server.list_resources())
    resource_uris = {str(resource.uri) for resource in resources}
    assert "resource://wiki/index" in resource_uris
    assert "resource://wiki/log/recent" in resource_uris
    assert "resource://schema/memory" in resource_uris
    assert "resource://ops/verification/latest" in resource_uris
    assert "resource://ops/routes/profile-matrix" in resource_uris

    templates = asyncio.run(server.list_resource_templates())
    template_uris = {template.uriTemplate for template in templates}
    assert "resource://wiki/topic/{slug}" in template_uris

    prompts = asyncio.run(server.list_prompts())
    prompt_names = {prompt.name for prompt in prompts}
    assert {
        "ingest_memory_to_wiki",
        "reconcile_conflict",
        "weekly_lint_report",
        "summarize_recent_project_state",
    }.issubset(prompt_names)


def test_reading_wiki_resources_materializes_overlay_files(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    store.save(
        MemoryCreate(
            memory_type="decision",
            title="HVDC wiki overlay seed",
            content="Recent memory pointer for wiki overlay generation.",
            source="manual",
            append_daily=False,
            occurred_at=datetime(2026, 4, 11, 9, 0, tzinfo=UTC),
        )
    )
    server = create_chatgpt_mcp_server(store)

    index_contents = asyncio.run(server.read_resource("resource://wiki/index"))
    log_contents = asyncio.run(server.read_resource("resource://wiki/log/recent"))
    schema_contents = asyncio.run(server.read_resource("resource://schema/memory"))

    assert "Wiki Index" in index_contents[0].content
    assert "HVDC wiki overlay seed" in index_contents[0].content
    assert "Wiki Log" in log_contents[0].content

    schema_bundle = json.loads(schema_contents[0].content)
    assert "memory_create" in schema_bundle
    assert "memory_patch" in schema_bundle
    assert "memory_record" in schema_bundle

    assert (tmp_path / "vault" / "wiki" / "index.md").exists()
    assert (tmp_path / "vault" / "wiki" / "log.md").exists()
    assert (tmp_path / "vault" / "wiki" / "topics").exists()
    assert (tmp_path / "vault" / "wiki" / "entities").exists()


def test_chatgpt_prompt_renders_recent_project_state(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    store.save(
        MemoryCreate(
            memory_type="decision",
            title="Project Alpha decision",
            content="Alpha project state changed.",
            source="manual",
            project="alpha",
            append_daily=False,
            occurred_at=datetime(2026, 4, 11, 10, 0, tzinfo=UTC),
        )
    )
    server = create_chatgpt_mcp_server(store)

    rendered = asyncio.run(
        server.get_prompt(
            "summarize_recent_project_state",
            {"project": "alpha", "limit": 5},
        )
    )

    text_blob = json.dumps(rendered.model_dump(mode="json"), ensure_ascii=False)
    assert "alpha" in text_blob.lower()
    assert "Project Alpha decision" in text_blob

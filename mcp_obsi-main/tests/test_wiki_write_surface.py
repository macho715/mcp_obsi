import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from app.chatgpt_mcp_server import FastMCP, create_chatgpt_mcp_server
from app.mcp_server import create_mcp_server
from app.models import MemoryCreate
from app.services.memory_store import MemoryStore


def test_main_mcp_server_registers_wiki_write_tools(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_mcp_server(store)

    assert "sync_wiki_index" in server._tool_manager._tools
    assert "append_wiki_log" in server._tool_manager._tools
    assert "write_wiki_page" in server._tool_manager._tools
    assert "lint_wiki" in server._tool_manager._tools
    assert "reconcile_conflict" in server._tool_manager._tools


def test_read_only_specialist_profiles_do_not_expose_wiki_write_tools(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_chatgpt_mcp_server(store)

    assert "sync_wiki_index" not in server._tool_manager._tools
    assert "append_wiki_log" not in server._tool_manager._tools
    assert "write_wiki_page" not in server._tool_manager._tools
    assert "lint_wiki" not in server._tool_manager._tools
    assert "reconcile_conflict" not in server._tool_manager._tools


def test_chatgpt_write_profile_wiki_tools_write_overlay_files(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    store.save(
        MemoryCreate(
            memory_type="decision",
            title="Wiki write seed",
            content="Seed content",
            source="manual",
            append_daily=False,
            occurred_at=datetime(2026, 4, 11, 12, 0, tzinfo=UTC),
        )
    )
    server = create_chatgpt_mcp_server(store, include_write_tools=True)

    sync_result = json.loads(asyncio.run(server._tool_manager.get_tool("sync_wiki_index").fn()))
    assert sync_result["status"] == "synced"
    assert (tmp_path / "vault" / "wiki" / "index.md").exists()

    write_result = json.loads(
        asyncio.run(
            server._tool_manager.get_tool("write_wiki_page").fn(
                section="topics",
                slug="alpha-project",
                title="Alpha Project",
                content="Compiled topic note",
                source_memory_ids=["MEM-EXAMPLE-1"],
            )
        )
    )
    assert write_result["status"] == "written"
    assert (tmp_path / "vault" / "wiki" / "topics" / "alpha-project.md").exists()

    log_result = json.loads(
        asyncio.run(
            server._tool_manager.get_tool("append_wiki_log").fn(
                message="Overlay sync completed",
                category="sync",
                related_ids=["MEM-EXAMPLE-1"],
            )
        )
    )
    assert log_result["status"] == "appended"
    assert "Overlay sync completed" in (tmp_path / "vault" / "wiki" / "log.md").read_text(
        encoding="utf-8"
    )

    conflict_result = json.loads(
        asyncio.run(
            server._tool_manager.get_tool("reconcile_conflict").fn(
                topic_slug="alpha-conflict",
                claim_a="Claim A text",
                claim_b="Claim B text",
                source_a="source-a",
                source_b="source-b",
            )
        )
    )
    assert conflict_result["status"] == "written"
    assert (tmp_path / "vault" / "wiki" / "conflicts" / "alpha-conflict.md").exists()

    lint_result = json.loads(asyncio.run(server._tool_manager.get_tool("lint_wiki").fn()))
    assert lint_result["status"] == "completed"
    assert (tmp_path / "vault" / "wiki" / "reports" / "latest-lint-report.md").exists()

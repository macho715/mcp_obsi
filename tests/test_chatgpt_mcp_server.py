import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from app.chatgpt_mcp_server import FastMCP, create_chatgpt_mcp_server
from app.models import MemoryCreate
from app.services.memory_store import MemoryStore


def test_create_chatgpt_mcp_server_exposes_read_only_search_fetch_and_recent_listing(
    tmp_path: Path,
):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_chatgpt_mcp_server(store)

    assert server is not None
    assert list(server._tool_manager._tools.keys()) == [
        "search",
        "fetch",
        "list_recent_memories",
    ]


def test_create_chatgpt_mcp_server_write_profile_exposes_memory_write_tools(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_chatgpt_mcp_server(store, include_write_tools=True)

    assert server is not None
    assert list(server._tool_manager._tools.keys()) == [
        "search",
        "fetch",
        "list_recent_memories",
        "save_memory",
        "get_memory",
        "update_memory",
        "sync_wiki_index",
        "append_wiki_log",
        "write_wiki_page",
        "lint_wiki",
        "reconcile_conflict",
    ]


def test_chatgpt_profile_tools_are_read_only(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_chatgpt_mcp_server(store)

    search_tool = server._tool_manager.get_tool("search")
    fetch_tool = server._tool_manager.get_tool("fetch")
    recent_tool = server._tool_manager.get_tool("list_recent_memories")

    assert search_tool.annotations.readOnlyHint is True
    assert search_tool.annotations.destructiveHint is False
    assert search_tool.annotations.openWorldHint is False
    assert fetch_tool.annotations.readOnlyHint is True
    assert fetch_tool.annotations.destructiveHint is False
    assert fetch_tool.annotations.openWorldHint is False
    assert recent_tool.annotations.readOnlyHint is True
    assert recent_tool.annotations.destructiveHint is False
    assert recent_tool.annotations.openWorldHint is False


def test_chatgpt_write_profile_marks_write_tools_non_read_only(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_chatgpt_mcp_server(store, include_write_tools=True)

    save_tool = server._tool_manager.get_tool("save_memory")
    update_tool = server._tool_manager.get_tool("update_memory")
    sync_tool = server._tool_manager.get_tool("sync_wiki_index")

    assert save_tool.annotations.readOnlyHint is False
    assert save_tool.annotations.destructiveHint is False
    assert save_tool.annotations.openWorldHint is False
    assert update_tool.annotations.readOnlyHint is False
    assert update_tool.annotations.destructiveHint is False
    assert update_tool.annotations.openWorldHint is False
    assert sync_tool.annotations.readOnlyHint is False


def test_chatgpt_search_treats_explicit_recent_query_as_recent_browse(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    for offset in range(30):
        store.save(
            MemoryCreate(
                memory_type="decision",
                title=f"ChatGPT Specialist Write Check {offset:02d}",
                content="Verification note",
                source="manual",
                project="local-verification",
                tags=["verification", "rollback-archived"],
                append_daily=False,
                occurred_at=datetime(2026, 3, 28, 0, 0, offset, tzinfo=UTC),
            )
        )
    business = store.save(
        MemoryCreate(
            memory_type="decision",
            title="HVDC business memory",
            content="Newest business note",
            source="manual",
            append_daily=False,
            occurred_at=datetime(2026, 3, 27, 23, 59, 59, tzinfo=UTC),
        )
    )

    server = create_chatgpt_mcp_server(store)
    search_tool = server._tool_manager.get_tool("search")
    payload = json.loads(asyncio.run(search_tool.fn("latest memory memo")))

    assert payload["results"][0]["id"] == business["id"]


def test_chatgpt_search_keeps_date_only_general_query_searchable(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    target = store.save(
        MemoryCreate(
            memory_type="decision",
            title="2026 migration memo",
            content="Target search document",
            source="manual",
            append_daily=False,
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    store.save(
        MemoryCreate(
            memory_type="decision",
            title="Newest unrelated note",
            content="Latest but unrelated",
            source="manual",
            append_daily=False,
            occurred_at=datetime(2026, 4, 8, tzinfo=UTC),
        )
    )

    server = create_chatgpt_mcp_server(store)
    search_tool = server._tool_manager.get_tool("search")
    payload = json.loads(asyncio.run(search_tool.fn("2026 memo")))

    assert payload["results"][0]["id"] == target["id"]


def test_chatgpt_search_keeps_explicit_verification_query_searchable(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    verification = store.save(
        MemoryCreate(
            memory_type="decision",
            title="ChatGPT Specialist Write Check 20260328-194027",
            content="Verification note",
            source="manual",
            project="local-verification",
            tags=["verification", "rollback-archived"],
            append_daily=False,
            occurred_at=datetime(2026, 3, 28, tzinfo=UTC),
        )
    )
    store.save(
        MemoryCreate(
            memory_type="decision",
            title="HVDC business memory",
            content="Business note",
            source="manual",
            append_daily=False,
            occurred_at=datetime(2026, 3, 27, tzinfo=UTC),
        )
    )

    server = create_chatgpt_mcp_server(store)
    search_tool = server._tool_manager.get_tool("search")
    payload = json.loads(asyncio.run(search_tool.fn("write check")))

    assert payload["results"][0]["id"] == verification["id"]

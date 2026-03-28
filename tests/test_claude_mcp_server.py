from pathlib import Path

from app.claude_mcp_server import FastMCP, create_claude_mcp_server
from app.services.memory_store import MemoryStore


def test_create_claude_mcp_server_exposes_only_search_and_fetch(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_claude_mcp_server(store)

    assert server is not None
    assert list(server._tool_manager._tools.keys()) == ["search", "fetch"]


def test_create_claude_mcp_server_write_profile_exposes_memory_write_tools(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_claude_mcp_server(store, include_write_tools=True)

    assert server is not None
    assert list(server._tool_manager._tools.keys()) == [
        "search",
        "fetch",
        "save_memory",
        "get_memory",
        "update_memory",
    ]


def test_claude_profile_tools_are_read_only(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_claude_mcp_server(store)

    search_tool = server._tool_manager.get_tool("search")
    fetch_tool = server._tool_manager.get_tool("fetch")

    assert search_tool.annotations.readOnlyHint is True
    assert search_tool.annotations.destructiveHint is False
    assert search_tool.annotations.openWorldHint is False
    assert fetch_tool.annotations.readOnlyHint is True
    assert fetch_tool.annotations.destructiveHint is False
    assert fetch_tool.annotations.openWorldHint is False


def test_claude_write_profile_marks_write_tools_non_read_only(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_claude_mcp_server(store, include_write_tools=True)

    save_tool = server._tool_manager.get_tool("save_memory")
    update_tool = server._tool_manager.get_tool("update_memory")

    assert save_tool.annotations.readOnlyHint is False
    assert save_tool.annotations.destructiveHint is False
    assert save_tool.annotations.openWorldHint is False
    assert update_tool.annotations.readOnlyHint is False
    assert update_tool.annotations.destructiveHint is False
    assert update_tool.annotations.openWorldHint is False

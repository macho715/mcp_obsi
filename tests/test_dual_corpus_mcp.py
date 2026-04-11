from pathlib import Path

from app.chatgpt_mcp_server import create_chatgpt_mcp_server
from app.claude_mcp_server import create_claude_mcp_server
from app.services.memory_store import MemoryStore


def test_chatgpt_readonly_surface_includes_wiki_read_tools(tmp_path: Path):
    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_chatgpt_mcp_server(store)
    names = set(server._tool_manager._tools)

    assert "search_wiki" in names
    assert "fetch_wiki" in names
    assert "save_memory" not in names


def test_claude_write_surface_keeps_memory_tools_and_adds_wiki_read_tools(
    tmp_path: Path,
):
    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_claude_mcp_server(store, include_write_tools=True)
    names = set(server._tool_manager._tools)

    assert {
        "search",
        "fetch",
        "list_recent_memories",
        "save_memory",
        "get_memory",
        "update_memory",
    }.issubset(names)
    assert {"search_wiki", "fetch_wiki"}.issubset(names)

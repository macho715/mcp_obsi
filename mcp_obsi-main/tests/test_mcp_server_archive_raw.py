import asyncio
from pathlib import Path

from app.mcp_server import FastMCP, create_mcp_server
from app.services.memory_store import MemoryStore


def test_mcp_server_registers_archive_raw_tool(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_mcp_server(store)

    assert server is not None
    assert "archive_raw" in server._tool_manager._tools


def test_archive_raw_tool_writes_mcp_raw_file(tmp_path: Path):
    if FastMCP is None:  # pragma: no cover
        return

    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")
    server = create_mcp_server(store)
    tool_entry = server._tool_manager._tools["archive_raw"]

    coro = tool_entry.fn(
        mcp_id="convo-mcp-archive-tool-1",
        source="cursor",
        body_markdown="## User\nhi\n",
        created_by="pytest",
        created_at_utc="2026-03-28T15:00:00+00:00",
        conversation_date="2026-03-28",
        project="TestProj",
        tags=["pytest"],
    )
    result = asyncio.run(coro)

    assert result["status"] == "saved"
    assert result["path"] == "mcp_raw/cursor/2026-03-28/convo-mcp-archive-tool-1.md"
    assert (vault / result["path"]).exists()

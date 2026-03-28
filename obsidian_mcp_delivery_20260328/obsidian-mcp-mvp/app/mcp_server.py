from __future__ import annotations

from app.models import MemoryCreate, MemoryPatch, MemoryType
from app.services.memory_store import MemoryStore
from mcp.server.fastmcp import FastMCP


def create_mcp_server(store: MemoryStore) -> FastMCP:
    mcp = FastMCP(
        name="ObsidianMemory",
        instructions="Search and persist structured memories into an Obsidian vault.",
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
    )

    @mcp.tool()
    def search_memory(
        query: str,
        types: list[str] | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
        recency_days: int | None = None,
    ) -> dict:
        """Search normalized memory notes by text, type, project, tags, and recency."""
        rows = store.search(
            query=query,
            types=types,
            project=project,
            tags=tags,
            limit=limit,
            recency_days=recency_days,
        )
        return {"results": [row.to_search_item() for row in rows], "count": len(rows)}

    @mcp.tool()
    def save_memory(
        memory_type: str,
        title: str,
        content: str,
        source: str,
        project: str | None = None,
        tags: list[str] | None = None,
        confidence: float = 0.80,
        sensitivity: str = "p1",
        append_daily: bool = True,
    ) -> dict:
        """Create a new memory note in Obsidian and index it in SQLite."""
        payload = MemoryCreate(
            memory_type=MemoryType(memory_type),
            title=title,
            content=content,
            source=source,
            project=project,
            tags=tags or [],
            confidence=confidence,
            sensitivity=sensitivity,
            append_daily=append_daily,
        )
        rec = store.create(payload)
        return {"ok": True, "record": rec.to_search_item()}

    @mcp.tool()
    def get_memory(memory_id: str) -> dict:
        """Get a memory note by id."""
        rec = store.get(memory_id)
        if rec is None:
            return {"ok": False, "error": f"Memory not found: {memory_id}"}
        return {"ok": True, "record": rec.to_search_item()}

    @mcp.tool()
    def list_recent_memories(
        limit: int = 10,
        memory_type: str | None = None,
        project: str | None = None,
    ) -> dict:
        """List recent memory notes ordered by update time descending."""
        rows = store.list_recent(limit=limit, memory_type=memory_type, project=project)
        return {"results": [row.to_search_item() for row in rows], "count": len(rows)}

    @mcp.tool()
    def update_memory(
        memory_id: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
        confidence: float | None = None,
        status: str | None = None,
    ) -> dict:
        """Patch an existing memory note."""
        payload = MemoryPatch(
            memory_id=memory_id,
            title=title,
            content=content,
            tags=tags,
            confidence=confidence,
            status=status,
        )
        rec = store.update(payload)
        return {"ok": True, "record": rec.to_search_item()}

    @mcp.tool()
    def search(query: str, limit: int = 5) -> dict:
        """Compatibility wrapper for generic search clients."""
        rows = store.search(query=query, limit=limit)
        return {"results": [row.to_search_item() for row in rows]}

    @mcp.tool()
    def fetch(id: str) -> dict:
        """Compatibility wrapper for generic fetch clients."""
        rec = store.get(id)
        if rec is None:
            return {"ok": False, "error": f"Memory not found: {id}"}
        item = rec.to_search_item()
        return {
            "id": item["id"],
            "title": item["title"],
            "text": item["text"],
            "url": rec.path,
            "metadata": item["metadata"],
        }

    return mcp

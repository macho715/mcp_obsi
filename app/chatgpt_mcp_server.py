import json

from app.config import settings
from app.mcp_server import (
    FastMCP,
    TransportSecuritySettings,
    build_fetch_wrapper_response,
    build_search_wrapper_response,
)
from app.models import MemoryCreate, MemoryPatch
from app.services.memory_store import MemoryStore

try:
    from mcp.types import ToolAnnotations
except ImportError:  # pragma: no cover
    ToolAnnotations = None


def _readonly_annotations():
    if ToolAnnotations is None:  # pragma: no cover
        return None
    return ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=True,
    )


def _write_annotations():
    if ToolAnnotations is None:  # pragma: no cover
        return None
    return ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=False,
    )


def create_chatgpt_mcp_server(store: MemoryStore, include_write_tools: bool = False):
    if FastMCP is None:  # pragma: no cover
        return None

    transport_security = None
    if (
        TransportSecuritySettings is not None
        and settings.runtime_allowed_hosts_list
        and settings.runtime_allowed_origins_list
    ):
        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=settings.runtime_allowed_hosts_list,
            allowed_origins=settings.runtime_allowed_origins_list,
        )

    mcp = FastMCP(
        name=(
            "obsidian-memory-chatgpt-write" if include_write_tools else "obsidian-memory-chatgpt"
        ),
        instructions=(
            "This is a ChatGPT-focused MCP profile for Obsidian-backed memory. "
            "Use search to discover relevant notes and fetch to retrieve the selected note. "
            "Use save_memory and update_memory only for deliberate durable memory writes."
            if include_write_tools
            else "This is a ChatGPT-focused, read-only MCP profile for Obsidian-backed memory. "
            "Use search to discover relevant notes and fetch to retrieve the selected note. "
            "Do not mutate state through this profile."
        ),
        streamable_http_path="/",
        transport_security=transport_security,
    )

    @mcp.tool(
        name="search",
        title="Search Obsidian memory",
        description=(
            "Use this when you need to search the Obsidian-backed memory store for "
            "relevant notes by query string."
        ),
        annotations=_readonly_annotations(),
        structured_output=False,
    )
    async def search(query: str) -> str:
        hits = store.search(query=query, limit=5)["results"]
        return json.dumps(build_search_wrapper_response(hits), ensure_ascii=False)

    @mcp.tool(
        name="fetch",
        title="Fetch Obsidian note",
        description=(
            "Use this when you already have a search result id and need the full note "
            "content for ChatGPT citations or follow-up reasoning."
        ),
        annotations=_readonly_annotations(),
        structured_output=False,
    )
    async def fetch(id: str) -> str:
        item = store.get(id)
        return json.dumps(build_fetch_wrapper_response(id, item), ensure_ascii=False)

    if include_write_tools:

        @mcp.tool(
            name="save_memory",
            title="Save durable memory",
            description=(
                "Use this when ChatGPT needs to persist a durable preference, project fact, "
                "decision, person note, todo, or conversation summary into Obsidian memory."
            ),
            annotations=_write_annotations(),
            structured_output=False,
        )
        async def save_memory(
            memory_type: str,
            title: str,
            content: str,
            source: str,
            project: str | None = None,
            tags: list[str] | None = None,
            confidence: float = 0.8,
            sensitivity: str = "p1",
            append_daily: bool = False,
            occurred_at: str | None = None,
        ) -> str:
            payload = MemoryCreate(
                memory_type=memory_type,
                title=title,
                content=content,
                source=source,
                project=project,
                tags=tags or [],
                confidence=confidence,
                sensitivity=sensitivity,
                append_daily=append_daily,
                occurred_at=occurred_at,
            )
            return json.dumps(store.save(payload), ensure_ascii=False)

        @mcp.tool(
            name="get_memory",
            title="Get memory record",
            description=(
                "Use this when ChatGPT already has a memory id and needs the full stored "
                "record, including status and metadata, not just the fetch wrapper."
            ),
            annotations=_readonly_annotations(),
            structured_output=False,
        )
        async def get_memory(memory_id: str) -> str:
            result = store.get(memory_id)
            return json.dumps(
                result or {"status": "not_found", "id": memory_id}, ensure_ascii=False
            )

        @mcp.tool(
            name="update_memory",
            title="Update durable memory",
            description=(
                "Use this when ChatGPT needs to revise or archive an existing durable memory "
                "record by id."
            ),
            annotations=_write_annotations(),
            structured_output=False,
        )
        async def update_memory(
            memory_id: str,
            title: str | None = None,
            content: str | None = None,
            tags: list[str] | None = None,
            confidence: float | None = None,
            status: str | None = None,
        ) -> str:
            patch = MemoryPatch(
                memory_id=memory_id,
                title=title,
                content=content,
                tags=tags,
                confidence=confidence,
                status=status,
            )
            return json.dumps(store.update(patch), ensure_ascii=False)

    return mcp

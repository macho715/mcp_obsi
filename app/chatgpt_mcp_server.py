import json

from app.config import settings
from app.mcp_server import (
    FastMCP,
    TransportSecuritySettings,
    build_fetch_wrapper_response,
    build_search_wrapper_response,
)
from app.models import MemoryCreate, MemoryPatch
from app.prompts_server import register_prompts
from app.resources_server import register_resources
from app.services.memory_store import MemoryStore
from app.services.wiki_search_service import WikiSearchService
from app.utils.specialist_readonly import specialist_search_hits
from app.wiki_tools import register_wiki_tools

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
            "If the user asks for recent, latest, list, browse, or recently saved notes, call "
            "list_recent_memories first instead of guessing search keywords. If search returns "
            "a likely hit and the user asked to show, open, read, summarize, or inspect the "
            "note, call fetch immediately on that hit before answering. Use search to discover "
            "relevant notes, list_recent_memories to browse the latest notes, and fetch to "
            "retrieve the selected note. "
            "Use save_memory and update_memory only for deliberate durable memory writes."
            if include_write_tools
            else "This is a ChatGPT-focused, read-only MCP profile for Obsidian-backed memory. "
            "If the user asks for recent, latest, list, browse, or recently saved notes, call "
            "list_recent_memories first instead of guessing search keywords. If search returns "
            "a likely hit and the user asked to show, open, read, summarize, or inspect the "
            "note, call fetch immediately on that hit before answering. Use search to discover "
            "relevant notes, list_recent_memories to browse the latest notes, and fetch to "
            "retrieve the selected note. Do not mutate state through this profile."
        ),
        streamable_http_path="/",
        transport_security=transport_security,
    )
    wiki_search = WikiSearchService(store.vault_path)

    @mcp.tool(
        name="search",
        title="Search Obsidian memory",
        description=(
            "Use this when you need to search the Obsidian-backed memory store for "
            "relevant notes by query string. Do not use this as a substitute for recent or "
            "latest listing; use list_recent_memories for that."
        ),
        annotations=_readonly_annotations(),
        structured_output=False,
    )
    async def search(query: str) -> str:
        hits = specialist_search_hits(store, query=query, limit=5)
        return json.dumps(build_search_wrapper_response(hits), ensure_ascii=False)

    @mcp.tool(
        name="fetch",
        title="Fetch Obsidian note",
        description=(
            "Use this when you already have a search result id and need the full note "
            "content for ChatGPT citations or follow-up reasoning. If the user asked to show, "
            "open, read, or summarize a specific search hit, call this right after search."
        ),
        annotations=_readonly_annotations(),
        structured_output=False,
    )
    async def fetch(id: str) -> str:
        item = store.get(id)
        return json.dumps(build_fetch_wrapper_response(id, item), ensure_ascii=False)

    @mcp.tool(
        name="list_recent_memories",
        title="List recent Obsidian memories",
        description=(
            "Use this when ChatGPT needs the latest memory notes or a paged recent list "
            "without guessing a search keyword first. Prefer this for recent, latest, list, "
            "browse, or recently saved note requests."
        ),
        annotations=_readonly_annotations(),
        structured_output=False,
    )
    async def list_recent_memories(
        limit: int = 10,
        memory_type: str | None = None,
        project: str | None = None,
        offset: int = 0,
    ) -> str:
        return json.dumps(
            store.recent(
                limit=limit,
                memory_type=memory_type,
                project=project,
                offset=offset,
            ),
            ensure_ascii=False,
        )

    @mcp.tool(
        name="search_wiki",
        title="Search wiki analyses",
        description=(
            "Use this when ChatGPT needs compiled wiki notes from wiki/analyses without "
            "changing canonical memory search behavior."
        ),
        annotations=_readonly_annotations(),
        structured_output=False,
    )
    async def search_wiki(query: str, path_prefix: str = "wiki/analyses", limit: int = 8) -> str:
        return json.dumps(
            wiki_search.search(query=query, path_prefix=path_prefix, limit=limit),
            ensure_ascii=False,
        )

    @mcp.tool(
        name="fetch_wiki",
        title="Fetch wiki note",
        description=(
            "Use this when ChatGPT needs the full body of a wiki note by path or slug."
        ),
        annotations=_readonly_annotations(),
        structured_output=False,
    )
    async def fetch_wiki(
        path: str | None = None,
        slug: str | None = None,
        include_frontmatter: bool = True,
        include_body: bool = True,
    ) -> str:
        payload = wiki_search.fetch(path=path, slug=slug)
        if not include_frontmatter:
            payload["frontmatter"] = None
        if not include_body:
            payload["body"] = ""
        return json.dumps(payload, ensure_ascii=False)

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

    register_resources(mcp, store)
    register_prompts(mcp, store)
    if include_write_tools:
        register_wiki_tools(mcp, store)

    return mcp

from datetime import date, datetime

from app.config import settings
from app.models import MemoryCreate, MemoryPatch, RawConversationCreate
from app.services.memory_store import MemoryStore

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
except ImportError:  # pragma: no cover
    FastMCP = None
    TransportSecuritySettings = None


def build_search_wrapper_response(hits: list[dict]) -> dict:
    return {
        "results": [
            {
                "id": hit["id"],
                "title": hit["title"],
                "url": f"obsidian://open?vault={settings.obs_vault_name}&file={hit['path']}",
            }
            for hit in hits
        ]
    }


def build_fetch_wrapper_response(memory_id: str, item: dict | None) -> dict:
    if not item:
        return {
            "id": memory_id,
            "title": "Not found",
            "text": "",
            "url": "",
            "metadata": {"status": "not_found"},
        }
    return {
        "id": item["id"],
        "title": item["title"],
        "text": item["content"],
        "url": f"obsidian://open?vault={settings.obs_vault_name}&file={item['path']}",
        "metadata": {
            "type": item["type"],
            "project": item["project"],
            "source": item["source"],
            "tags": item["tags"],
        },
    }


def create_mcp_server(store: MemoryStore):
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
        name="obsidian-memory",
        instructions=(
            "This server provides shared long-term memory backed by an Obsidian vault. "
            "Use read tools first. Use write tools only for deliberate durable content: "
            "archive_raw for full conversation transcripts (mcp_raw tree), save_memory for "
            "atomic memory notes, update_memory for revisions."
        ),
        streamable_http_path="/",
        transport_security=transport_security,
    )

    @mcp.tool()
    async def search_memory(
        query: str,
        types: list[str] | None = None,
        roles: list[str] | None = None,
        topics: list[str] | None = None,
        entities: list[str] | None = None,
        projects: list[str] | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
        recency_days: int | None = None,
    ) -> dict:
        return store.search(
            query=query,
            types=types,
            roles=roles,
            topics=topics,
            entities=entities,
            projects=projects,
            project=project,
            tags=tags,
            limit=limit,
            recency_days=recency_days,
        )

    @mcp.tool()
    async def save_memory(
        title: str,
        content: str,
        source: str,
        memory_type: str | None = None,
        roles: list[str] | None = None,
        topics: list[str] | None = None,
        entities: list[str] | None = None,
        projects: list[str] | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        raw_refs: list[str] | None = None,
        confidence: float = 0.8,
        sensitivity: str = "p1",
        status: str = "active",
        language: str = "ko",
        notes: str | None = None,
        append_daily: bool = True,
        occurred_at: str | None = None,
        due_at: str | None = None,
    ) -> dict:
        payload = MemoryCreate(
            memory_type=memory_type,
            title=title,
            content=content,
            source=source,
            roles=roles or [],
            topics=topics or [],
            entities=entities or [],
            projects=projects or [],
            project=project,
            tags=tags or [],
            raw_refs=raw_refs or [],
            confidence=confidence,
            sensitivity=sensitivity,
            status=status,
            language=language,
            notes=notes,
            append_daily=append_daily,
            occurred_at=occurred_at,
            due_at=due_at,
        )
        return store.save(payload)

    @mcp.tool()
    async def get_memory(memory_id: str) -> dict:
        result = store.get(memory_id)
        return result or {"status": "not_found", "id": memory_id}

    @mcp.tool()
    async def list_recent_memories(
        limit: int = 10, memory_type: str | None = None, project: str | None = None
    ) -> dict:
        return store.recent(limit=limit, memory_type=memory_type, project=project)

    @mcp.tool()
    async def update_memory(
        memory_id: str,
        title: str | None = None,
        content: str | None = None,
        roles: list[str] | None = None,
        topics: list[str] | None = None,
        entities: list[str] | None = None,
        projects: list[str] | None = None,
        tags: list[str] | None = None,
        raw_refs: list[str] | None = None,
        confidence: float | None = None,
        status: str | None = None,
        language: str | None = None,
        notes: str | None = None,
    ) -> dict:
        patch = MemoryPatch(
            memory_id=memory_id,
            title=title,
            content=content,
            roles=roles,
            topics=topics,
            entities=entities,
            projects=projects,
            tags=tags,
            raw_refs=raw_refs,
            confidence=confidence,
            status=status,
            language=language,
            notes=notes,
        )
        return store.update(patch)

    @mcp.tool()
    async def archive_raw(
        mcp_id: str,
        source: str,
        body_markdown: str,
        created_by: str = "mcp-server",
        created_at_utc: str | None = None,
        conversation_date: str | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Persist one raw conversation file under mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md."""

        def _parse_utc(s: str | None) -> datetime | None:
            if not s or not str(s).strip():
                return None
            text = str(s).strip().replace("Z", "+00:00")
            return datetime.fromisoformat(text)

        def _parse_day(s: str | None) -> date | None:
            if not s or not str(s).strip():
                return None
            text = str(s).strip()[:10]
            return date.fromisoformat(text)

        payload = RawConversationCreate(
            mcp_id=mcp_id,
            source=source,
            body_markdown=body_markdown,
            created_by=created_by,
            created_at_utc=_parse_utc(created_at_utc),
            conversation_date=_parse_day(conversation_date),
            project=project,
            tags=tags or [],
        )
        return store.archive_raw_conversation(payload)

    @mcp.tool()
    async def search(query: str) -> dict:
        hits = store.search(query=query, limit=5)["results"]
        return build_search_wrapper_response(hits)

    @mcp.tool()
    async def fetch(id: str) -> dict:
        item = store.get(id)
        return build_fetch_wrapper_response(id, item)

    return mcp

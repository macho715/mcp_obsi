import json

from app.services.conflict_service import ConflictService
from app.services.lint_service import LintService
from app.services.memory_store import MemoryStore
from app.services.wiki_index_service import WikiIndexService
from app.services.wiki_log_service import WikiLogService
from app.services.wiki_store import WikiStore

try:
    from mcp.types import ToolAnnotations
except ImportError:  # pragma: no cover
    ToolAnnotations = None


def _write_annotations():
    if ToolAnnotations is None:  # pragma: no cover
        return None
    return ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        openWorldHint=False,
        idempotentHint=False,
    )


def register_wiki_tools(server, store: MemoryStore) -> None:
    wiki_store = WikiStore(store.vault_path)
    wiki_index = WikiIndexService(wiki_store, store)
    wiki_log = WikiLogService(wiki_store, store)
    conflict_service = ConflictService(wiki_store)
    lint_service = LintService(wiki_store)

    @server.tool(
        name="sync_wiki_index",
        title="Sync wiki index",
        description="Rebuild the compiled wiki index from recent durable memory pointers.",
        annotations=_write_annotations(),
        structured_output=False,
    )
    async def sync_wiki_index(limit: int = 20) -> str:
        content = wiki_index.sync(limit=limit)
        return json.dumps(
            {
                "status": "synced",
                "path": str(wiki_store.overlay_path("index.md")).replace("\\", "/"),
                "preview": content.splitlines()[:8],
            },
            ensure_ascii=False,
        )

    @server.tool(
        name="append_wiki_log",
        title="Append wiki log",
        description="Append an audit-style entry to the compiled wiki log.",
        annotations=_write_annotations(),
        structured_output=False,
    )
    async def append_wiki_log(
        message: str,
        category: str = "ops",
        related_ids: list[str] | None = None,
    ) -> str:
        return json.dumps(
            wiki_log.append_entry(message=message, category=category, related_ids=related_ids),
            ensure_ascii=False,
        )

    @server.tool(
        name="write_wiki_page",
        title="Write wiki page",
        description=(
            "Write or refresh a compiled wiki page under topics, entities, conflicts, or reports."
        ),
        annotations=_write_annotations(),
        structured_output=False,
    )
    async def write_wiki_page(
        section: str,
        slug: str,
        title: str,
        content: str,
        source_memory_ids: list[str] | None = None,
    ) -> str:
        path = wiki_store.write_page(
            section=section,
            slug=slug,
            title=title,
            content=content,
            source_memory_ids=source_memory_ids,
        )
        return json.dumps(
            {"status": "written", "path": str(path).replace("\\", "/")},
            ensure_ascii=False,
        )

    @server.tool(
        name="lint_wiki",
        title="Lint wiki overlay",
        description=(
            "Run a report-first lint over compiled wiki artifacts and save the latest report."
        ),
        annotations=_write_annotations(),
        structured_output=False,
    )
    async def lint_wiki() -> str:
        return json.dumps(lint_service.run(), ensure_ascii=False)

    @server.tool(
        name="reconcile_conflict",
        title="Reconcile conflict",
        description="Write a compiled conflict note that preserves both competing claims.",
        annotations=_write_annotations(),
        structured_output=False,
    )
    async def reconcile_conflict(
        topic_slug: str,
        claim_a: str,
        claim_b: str,
        source_a: str | None = None,
        source_b: str | None = None,
    ) -> str:
        return json.dumps(
            conflict_service.reconcile(
                topic_slug=topic_slug,
                claim_a=claim_a,
                claim_b=claim_b,
                source_a=source_a,
                source_b=source_b,
            ),
            ensure_ascii=False,
        )

import json
from pathlib import Path

from app.config import settings
from app.models import MemoryCreate, MemoryPatch, MemoryRecord
from app.services.memory_store import MemoryStore
from app.services.wiki_index_service import WikiIndexService
from app.services.wiki_log_service import WikiLogService
from app.services.wiki_store import WikiStore


def register_resources(server, store: MemoryStore) -> None:
    wiki_store = WikiStore(store.vault_path, settings.wiki_overlay_dirname)
    wiki_index = WikiIndexService(wiki_store, store)
    wiki_log = WikiLogService(wiki_store, store)

    @server.resource(
        "resource://wiki/index",
        name="wiki_index",
        title="Wiki Index",
        description="Compiled wiki index generated from recent durable memory pointers.",
        mime_type="text/markdown",
    )
    async def wiki_index_resource() -> str:
        return wiki_index.sync(limit=12)

    @server.resource(
        "resource://wiki/log/recent",
        name="wiki_log_recent",
        title="Wiki Recent Log",
        description="Append-style recent activity view for the compiled wiki overlay.",
        mime_type="text/markdown",
    )
    async def wiki_log_recent_resource() -> str:
        return wiki_log.sync_recent(limit=12)

    @server.resource(
        "resource://wiki/topic/{slug}",
        name="wiki_topic",
        title="Wiki Topic Page",
        description="Read a compiled topic page from the wiki overlay by slug.",
        mime_type="text/markdown",
    )
    async def wiki_topic_resource(slug: str) -> str:
        content = wiki_store.read_text(f"topics/{slug}.md")
        if content is not None:
            return content
        return f"# Topic: {slug}\n\nNo compiled topic page exists yet.\n"

    @server.resource(
        "resource://schema/memory",
        name="memory_schema",
        title="Memory Schema",
        description="JSON schema bundle for memory create, patch, and record models.",
        mime_type="application/json",
    )
    async def memory_schema_resource() -> str:
        bundle = {
            "memory_create": MemoryCreate.model_json_schema(),
            "memory_patch": MemoryPatch.model_json_schema(),
            "memory_record": MemoryRecord.model_json_schema(),
        }
        return json.dumps(bundle, ensure_ascii=False, indent=2)

    @server.resource(
        "resource://ops/verification/latest",
        name="verification_latest",
        title="Latest Verification Guidance",
        description="Current verification commands and evidence paths for the MCP runtime.",
        mime_type="text/markdown",
    )
    async def verification_latest_resource() -> str:
        evidence_path = Path("docs") / "MCP_RUNTIME_EVIDENCE.md"
        if evidence_path.exists():
            return evidence_path.read_text(encoding="utf-8")
        return (
            "# Latest Verification Guidance\n\n"
            "- `.venv\\Scripts\\python.exe -m pytest -q`\n"
            "- `.venv\\Scripts\\python.exe -m ruff check .`\n"
            "- `.venv\\Scripts\\python.exe -m ruff format --check .`\n"
        )

    @server.resource(
        "resource://ops/routes/profile-matrix",
        name="route_profile_matrix",
        title="Route Profile Matrix",
        description="Current route, auth, and mutation profile for MCP endpoints.",
        mime_type="text/markdown",
    )
    async def route_profile_matrix_resource() -> str:
        return "\n".join(
            [
                "# Route Profile Matrix",
                "",
                "| Route | Auth | Mutation | Intended use |",
                "|---|---|---|---|",
                (
                    f"| `/mcp` | bearer `{bool(settings.mcp_api_token.strip())}` | yes | "
                    "primary full profile |"
                ),
                "| `/chatgpt-mcp` | no bearer by design | no | read-only ChatGPT specialist |",
                "| `/chatgpt-mcp-write` | bearer | yes | write-capable ChatGPT specialist |",
                "| `/claude-mcp` | no bearer by design | no | read-only Claude specialist |",
                "| `/claude-mcp-write` | bearer | yes | write-capable Claude specialist |",
            ]
        )

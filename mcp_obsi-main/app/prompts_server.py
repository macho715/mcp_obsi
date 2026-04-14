from mcp.server.fastmcp.prompts.base import AssistantMessage, UserMessage

from app.services.memory_store import MemoryStore


def register_prompts(server, store: MemoryStore) -> None:
    @server.prompt(
        name="ingest_memory_to_wiki",
        title="Ingest Memory To Wiki",
        description=(
            "Review recent durable memory and decide what should be promoted "
            "into the compiled wiki overlay."
        ),
    )
    async def ingest_memory_to_wiki(project: str | None = None, limit: int = 10):
        recent = store.recent(limit=limit, project=project)
        titles = (
            "\n".join(f"- {item['title']}" for item in recent["results"]) or "- No recent items"
        )
        return [
            AssistantMessage(
                "You are preparing a wiki overlay update from durable memory. "
                "Keep memory as the source of truth and treat wiki pages as "
                "compiled artifacts."
            ),
            UserMessage(
                "Review the following recent memory pointers and decide which "
                "ones should update wiki/index, wiki/log, or topic/entity "
                f"overlays.\n\nProject: {project or 'all'}\n\nRecent items:\n{titles}"
            ),
        ]

    @server.prompt(
        name="reconcile_conflict",
        title="Reconcile Conflict",
        description=("Prepare a human-in-the-loop reconciliation workflow for conflicting claims."),
    )
    async def reconcile_conflict(topic_slug: str, claim_a: str, claim_b: str):
        return [
            AssistantMessage(
                "Do not overwrite either claim. Compare them, identify the "
                "evidence gap, and propose a conflict note for the compiled wiki."
            ),
            UserMessage(
                f"Topic slug: {topic_slug}\n\nClaim A:\n{claim_a}\n\nClaim B:\n{claim_b}\n\n"
                "Produce a reconciliation plan and a conflict note draft."
            ),
        ]

    @server.prompt(
        name="weekly_lint_report",
        title="Weekly Lint Report",
        description=(
            "Generate a weekly wiki lint review covering orphan pages, stale "
            "claims, and missing evidence."
        ),
    )
    async def weekly_lint_report(project: str | None = None):
        return [
            AssistantMessage(
                "Treat wiki lint as report-first. Do not silently mutate "
                "compiled pages before proposing a patch."
            ),
            UserMessage(
                f"Prepare a weekly lint report for project `{project or 'all'}` "
                "covering orphan pages, stale claims, broken links, and "
                "missing evidence."
            ),
        ]

    @server.prompt(
        name="summarize_recent_project_state",
        title="Summarize Recent Project State",
        description=(
            "Summarize recent project state from durable memory and the compiled wiki overlay."
        ),
    )
    async def summarize_recent_project_state(project: str | None = None, limit: int = 10):
        recent = store.recent(limit=limit, project=project)
        titles = (
            "\n".join(f"- {item['title']}" for item in recent["results"]) or "- No recent items"
        )
        return [
            AssistantMessage(
                "Summarize project state using memory as the source of truth "
                "and wiki overlay artifacts as compiled context."
            ),
            UserMessage(
                f"Summarize the recent project state for `{project or 'all'}`."
                f"\n\nRecent memory pointers:\n{titles}"
            ),
        ]

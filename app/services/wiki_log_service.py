from datetime import UTC, datetime

from app.services.memory_store import MemoryStore
from app.services.wiki_store import WikiStore


class WikiLogService:
    def __init__(self, wiki_store: WikiStore, memory_store: MemoryStore):
        self.wiki_store = wiki_store
        self.memory_store = memory_store

    def render_recent(self, limit: int = 10) -> str:
        recent = self.memory_store.recent(limit=limit)
        lines = [
            "# Wiki Log",
            "",
            f"- Generated at: {datetime.now(UTC).isoformat()}",
            "",
            "## Recent Memory Activity",
            "",
        ]

        if not recent["results"]:
            lines.append("- No recent memory activity available.")
        else:
            for item in recent["results"]:
                classification = item.get("classification", "unknown")
                lines.append(
                    f"- {item['created_at']} | `{item['id']}` | {item['title']} | {classification}"
                )

        return "\n".join(lines)

    def sync_recent(self, limit: int = 10) -> str:
        content = self.render_recent(limit=limit)
        self.wiki_store.write_text("log.md", content)
        return content

    def append_entry(
        self,
        message: str,
        category: str = "ops",
        related_ids: list[str] | None = None,
    ) -> dict:
        timestamp = datetime.now(UTC).isoformat()
        related_suffix = f" | related: {', '.join(related_ids)}" if related_ids else ""
        line = f"- {timestamp} | {category} | {message}{related_suffix}\n"
        self.wiki_store.append_text("log.md", line)
        return {
            "status": "appended",
            "path": str(self.wiki_store.overlay_path("log.md")).replace("\\", "/"),
            "timestamp": timestamp,
        }

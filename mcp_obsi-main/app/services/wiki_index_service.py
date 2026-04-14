from datetime import UTC, datetime

from app.services.memory_store import MemoryStore
from app.services.wiki_store import WikiStore


class WikiIndexService:
    def __init__(self, wiki_store: WikiStore, memory_store: MemoryStore):
        self.wiki_store = wiki_store
        self.memory_store = memory_store

    def render(self, limit: int = 10) -> str:
        recent = self.memory_store.recent(limit=limit)
        lines = [
            "# Wiki Index",
            "",
            f"- Generated at: {datetime.now(UTC).isoformat()}",
            f"- Recent sample size: {len(recent['results'])}",
            "",
            "## Recent Memory Pointers",
            "",
        ]

        if not recent["results"]:
            lines.append("- No recent memory pointers available.")
        else:
            for item in recent["results"]:
                project = f" | project: {item['project']}" if item.get("project") else ""
                lines.append(f"- `{item['id']}` | {item['title']} | {item['type']}{project}")

        lines.extend(
            [
                "",
                "## Overlay Directories",
                "",
                "- `wiki/topics/`",
                "- `wiki/entities/`",
                "- `wiki/conflicts/`",
                "- `wiki/reports/`",
            ]
        )
        return "\n".join(lines)

    def sync(self, limit: int = 10) -> str:
        content = self.render(limit=limit)
        self.wiki_store.write_text("index.md", content)
        return content

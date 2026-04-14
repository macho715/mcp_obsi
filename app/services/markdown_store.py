from datetime import datetime
from pathlib import Path

import yaml

from app.models import MemoryRecord


class MarkdownStore:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)

    def write_memory(self, rec: MemoryRecord) -> None:
        path = self.vault_path / rec.path
        path.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = {
            "schema_type": "memory_item",
            "schema_version": rec.schema_version,
            "note_kind": rec.note_kind,
            "memory_id": rec.id,
            "memory_type": rec.memory_type.value,
            "roles": [role.value for role in rec.roles],
            "title": rec.title,
            "source": rec.source,
            "created_by": rec.created_by,
            "project": rec.project,
            "topics": rec.topics,
            "entities": rec.entities,
            "projects": rec.projects,
            "tags": rec.tags,
            "raw_refs": rec.raw_refs,
            "relations": [relation.model_dump() for relation in rec.relations],
            "confidence": rec.confidence,
            "sensitivity": rec.sensitivity,
            "status": rec.status,
            "language": rec.language,
            "notes": rec.notes,
            "created_at_utc": rec.created_at.isoformat(),
            "updated_at_utc": rec.updated_at.isoformat(),
            "mcp_sig": rec.mcp_sig,
        }
        body = (
            "---\n"
            + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
            + "---\n\n"
            + rec.content.strip()
            + "\n"
        )
        path.write_text(body, encoding="utf-8")

    def read_memory_document(self, rel_path: str) -> dict | None:
        path = self.vault_path / rel_path
        if not path.exists():
            return None

        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            raise ValueError(f"memory note at {rel_path} is missing frontmatter")

        parts = text.split("\n---\n", 1)
        if len(parts) != 2:
            raise ValueError(f"memory note at {rel_path} has malformed frontmatter")

        frontmatter_text = parts[0][4:]
        body = parts[1].lstrip("\n").rstrip("\n")
        frontmatter = yaml.safe_load(frontmatter_text) or {}
        frontmatter["content"] = body
        return frontmatter

    def append_daily(self, text: str, dt: datetime) -> None:
        path = self.vault_path / "10_Daily" / f"{dt.strftime('%Y-%m-%d')}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(f"# {dt.strftime('%Y-%m-%d')}\n\n", encoding="utf-8")
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"\n## {dt.strftime('%H:%M')}\n- Memory: {text.strip()}\n")

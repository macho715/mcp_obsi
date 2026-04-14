from __future__ import annotations

import re
from pathlib import Path

import yaml

from app.models import MemoryRecord, MemoryType


_FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


class MarkdownStore:
    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)

    def write_record(self, rec: MemoryRecord) -> Path:
        target = self.vault_path / rec.path
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": rec.id,
            "type": rec.memory_type.value,
            "title": rec.title,
            "source": rec.source,
            "project": rec.project,
            "tags": rec.tags,
            "confidence": rec.confidence,
            "sensitivity": rec.sensitivity,
            "status": rec.status,
            "created_at": rec.created_at.isoformat(),
            "updated_at": rec.updated_at.isoformat(),
        }
        front_matter = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False).strip()
        content = f"---\n{front_matter}\n---\n\n{rec.content.strip()}\n"
        target.write_text(content, encoding="utf-8")
        return target

    def read_record(self, relative_path: str) -> MemoryRecord:
        target = self.vault_path / relative_path
        raw = target.read_text(encoding="utf-8")
        match = _FRONT_MATTER_RE.match(raw)
        if not match:
            raise ValueError(f"Invalid front matter format: {target}")

        front_matter_raw, body = match.groups()
        meta = yaml.safe_load(front_matter_raw) or {}
        return MemoryRecord(
            id=meta["id"],
            memory_type=MemoryType(meta["type"]),
            title=meta["title"],
            content=body.strip(),
            source=meta["source"],
            project=meta.get("project"),
            tags=meta.get("tags", []) or [],
            confidence=float(meta.get("confidence", 0.8)),
            sensitivity=meta.get("sensitivity", "p1"),
            status=meta.get("status", "active"),
            created_at=meta["created_at"],
            updated_at=meta["updated_at"],
            path=relative_path,
        )

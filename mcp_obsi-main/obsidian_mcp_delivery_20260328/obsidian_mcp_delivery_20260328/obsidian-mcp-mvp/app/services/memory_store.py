from __future__ import annotations

from pathlib import Path

from app.models import MemoryCreate, MemoryPatch, MemoryRecord
from app.services.daily_store import DailyStore
from app.services.index_store import IndexStore
from app.services.markdown_store import MarkdownStore
from app.utils.ids import make_memory_id
from app.utils.sanitize import clean_tag, clean_text
from app.utils.time import now_tz


class MemoryStore:
    def __init__(self, vault_path: Path, index_store: IndexStore, timezone: str) -> None:
        self.vault_path = vault_path
        self.index_store = index_store
        self.timezone = timezone
        self.markdown_store = MarkdownStore(vault_path)
        self.daily_store = DailyStore(vault_path)
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        for folder in ["10_Daily", "20_AI_Memory", "90_System"]:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)

    def _build_rel_path(self, memory_type: str, memory_id: str, timestamp) -> str:
        return f"20_AI_Memory/{memory_type}/{timestamp.strftime('%Y')}/{timestamp.strftime('%m')}/{memory_id}.md"

    def create(self, payload: MemoryCreate) -> MemoryRecord:
        timestamp = payload.occurred_at or now_tz(self.timezone)
        memory_id = make_memory_id(timestamp)
        rel_path = self._build_rel_path(payload.memory_type.value, memory_id, timestamp)

        rec = MemoryRecord(
            id=memory_id,
            memory_type=payload.memory_type,
            title=clean_text(payload.title),
            content=clean_text(payload.content),
            source=payload.source,
            project=payload.project,
            tags=[clean_tag(tag) for tag in payload.tags],
            confidence=payload.confidence,
            sensitivity=payload.sensitivity,
            status="active",
            created_at=timestamp,
            updated_at=timestamp,
            path=rel_path,
        )

        self.markdown_store.write_record(rec)
        self.index_store.upsert(rec)
        if payload.append_daily:
            self.daily_store.append_memory(rec)
        return rec

    def get(self, memory_id: str) -> MemoryRecord | None:
        rec = self.index_store.get(memory_id)
        if rec is None:
            return None
        return self.markdown_store.read_record(rec.path)

    def list_recent(self, limit: int = 10, memory_type: str | None = None, project: str | None = None) -> list[MemoryRecord]:
        return self.index_store.list_recent(limit=limit, memory_type=memory_type, project=project)

    def search(
        self,
        query: str,
        types: list[str] | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
        recency_days: int | None = None,
    ) -> list[MemoryRecord]:
        normalized_tags = [clean_tag(tag) for tag in tags] if tags else None
        return self.index_store.search(
            query=query.strip(),
            types=types,
            project=project,
            tags=normalized_tags,
            limit=limit,
            recency_days=recency_days,
        )

    def update(self, payload: MemoryPatch) -> MemoryRecord:
        current = self.get(payload.memory_id)
        if current is None:
            raise KeyError(f"Memory not found: {payload.memory_id}")

        updated = current.model_copy(
            update={
                "title": clean_text(payload.title) if payload.title is not None else current.title,
                "content": clean_text(payload.content) if payload.content is not None else current.content,
                "tags": [clean_tag(tag) for tag in payload.tags] if payload.tags is not None else current.tags,
                "confidence": payload.confidence if payload.confidence is not None else current.confidence,
                "status": payload.status if payload.status is not None else current.status,
                "updated_at": now_tz(self.timezone),
            }
        )

        self.markdown_store.write_record(updated)
        self.index_store.upsert(updated)
        return updated

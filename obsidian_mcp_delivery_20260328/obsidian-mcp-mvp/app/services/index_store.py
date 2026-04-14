from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.models import MemoryRecord, MemoryType


class IndexStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    project TEXT,
                    tags TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    sensitivity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    path TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_updated_at ON memories(updated_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project)")
            conn.commit()

    def _row_to_record(self, row: sqlite3.Row | None) -> MemoryRecord | None:
        if row is None:
            return None
        return MemoryRecord(
            id=row["id"],
            memory_type=MemoryType(row["memory_type"]),
            title=row["title"],
            content=row["content"],
            source=row["source"],
            project=row["project"],
            tags=json.loads(row["tags"]),
            confidence=row["confidence"],
            sensitivity=row["sensitivity"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            path=row["path"],
        )

    def upsert(self, rec: MemoryRecord) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memories (
                    id, memory_type, title, content, source, project, tags,
                    confidence, sensitivity, status, created_at, updated_at, path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    memory_type=excluded.memory_type,
                    title=excluded.title,
                    content=excluded.content,
                    source=excluded.source,
                    project=excluded.project,
                    tags=excluded.tags,
                    confidence=excluded.confidence,
                    sensitivity=excluded.sensitivity,
                    status=excluded.status,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    path=excluded.path
                """,
                (
                    rec.id,
                    rec.memory_type.value,
                    rec.title,
                    rec.content,
                    rec.source,
                    rec.project,
                    json.dumps(rec.tags, ensure_ascii=False),
                    rec.confidence,
                    rec.sensitivity,
                    rec.status,
                    rec.created_at.isoformat(),
                    rec.updated_at.isoformat(),
                    rec.path,
                ),
            )
            conn.commit()

    def get(self, memory_id: str) -> MemoryRecord | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            return self._row_to_record(row)

    def list_recent(self, limit: int = 10, memory_type: str | None = None, project: str | None = None) -> list[MemoryRecord]:
        sql = "SELECT * FROM memories WHERE 1=1"
        params: list[object] = []
        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)
        if project:
            sql += " AND project = ?"
            params.append(project)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_record(row) for row in rows if row is not None]

    def search(
        self,
        query: str,
        types: list[str] | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
        recency_days: int | None = None,
    ) -> list[MemoryRecord]:
        sql = "SELECT * FROM memories WHERE (title LIKE ? OR content LIKE ?)"
        like_query = f"%{query}%"
        params: list[object] = [like_query, like_query]

        if types:
            placeholders = ",".join("?" for _ in types)
            sql += f" AND memory_type IN ({placeholders})"
            params.extend(types)

        if project:
            sql += " AND project = ?"
            params.append(project)

        if recency_days:
            since = datetime.utcnow() - timedelta(days=recency_days)
            sql += " AND updated_at >= ?"
            params.append(since.isoformat())

        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(max(limit * 3, limit))

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        records = [self._row_to_record(row) for row in rows if row is not None]

        if tags:
            wanted = set(tags)
            records = [rec for rec in records if wanted.issubset(set(rec.tags))]

        return records[:limit]

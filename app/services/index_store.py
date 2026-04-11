import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.models import MemoryRecord


class IndexStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _flatten_json_text(raw_json: str) -> str:
        try:
            values = json.loads(raw_json or "[]")
        except json.JSONDecodeError:
            return ""
        if not isinstance(values, list):
            return ""
        return " ".join(str(value).strip() for value in values if str(value).strip())

    @staticmethod
    def _fts_query(raw_query: str) -> str:
        tokens = [token.strip() for token in raw_query.split() if token.strip()]
        if not tokens:
            return ""
        escaped_tokens = [token.replace('"', '""') for token in tokens]
        return " ".join(f'"{token}"' for token in escaped_tokens)

    def _verify_features(self, conn: sqlite3.Connection) -> None:
        json_ok = conn.execute("SELECT json_valid('[]')").fetchone()[0]
        if json_ok != 1:
            raise RuntimeError("SQLite JSON1 support is required for memory index queries.")
        try:
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS temp.__fts5_check USING fts5(x)")
            conn.execute("DROP TABLE IF EXISTS temp.__fts5_check")
        except sqlite3.DatabaseError as exc:
            raise RuntimeError("SQLite FTS5 support is required for memory index search.") from exc

    def _refresh_search_text_columns(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute("SELECT id, tags, topics, entities, projects FROM memories").fetchall()
        for row in rows:
            conn.execute(
                """
                UPDATE memories
                SET tags_text = ?, topics_text = ?, entities_text = ?, projects_text = ?
                WHERE id = ?
                """,
                (
                    self._flatten_json_text(row["tags"]),
                    self._flatten_json_text(row["topics"]),
                    self._flatten_json_text(row["entities"]),
                    self._flatten_json_text(row["projects"]),
                    row["id"],
                ),
            )

    def _ensure_fts(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                title,
                content,
                tags_text,
                topics_text,
                entities_text,
                projects_text,
                content='memories',
                content_rowid='rowid',
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(
                    rowid, title, content, tags_text, topics_text, entities_text, projects_text
                ) VALUES (
                    new.rowid, new.title, new.content, new.tags_text, new.topics_text,
                    new.entities_text, new.projects_text
                );
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(
                    memories_fts, rowid, title, content, tags_text, topics_text, entities_text,
                    projects_text
                ) VALUES (
                    'delete', old.rowid, old.title, old.content, old.tags_text, old.topics_text,
                    old.entities_text, old.projects_text
                );
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(
                    memories_fts, rowid, title, content, tags_text, topics_text, entities_text,
                    projects_text
                ) VALUES (
                    'delete', old.rowid, old.title, old.content, old.tags_text, old.topics_text,
                    old.entities_text, old.projects_text
                );
                INSERT INTO memories_fts(
                    rowid, title, content, tags_text, topics_text, entities_text, projects_text
                ) VALUES (
                    new.rowid, new.title, new.content, new.tags_text, new.topics_text,
                    new.entities_text, new.projects_text
                );
            END;
            """
        )
        conn.execute("INSERT INTO memories_fts(memories_fts) VALUES ('rebuild')")

    def _init_db(self) -> None:
        with self._conn() as conn:
            self._verify_features(conn)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    roles TEXT NOT NULL DEFAULT '[]',
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    project TEXT,
                    topics TEXT NOT NULL DEFAULT '[]',
                    entities TEXT NOT NULL DEFAULT '[]',
                    projects TEXT NOT NULL DEFAULT '[]',
                    tags TEXT NOT NULL,
                    tags_text TEXT NOT NULL DEFAULT '',
                    topics_text TEXT NOT NULL DEFAULT '',
                    entities_text TEXT NOT NULL DEFAULT '',
                    projects_text TEXT NOT NULL DEFAULT '',
                    raw_refs TEXT NOT NULL DEFAULT '[]',
                    relations TEXT NOT NULL DEFAULT '[]',
                    confidence REAL NOT NULL,
                    sensitivity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    language TEXT NOT NULL DEFAULT 'ko',
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    path TEXT NOT NULL,
                    mcp_sig TEXT
                )
                """
            )
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(memories)").fetchall()
            }
            if "mcp_sig" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN mcp_sig TEXT")
            if "roles" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN roles TEXT NOT NULL DEFAULT '[]'")
            if "topics" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN topics TEXT NOT NULL DEFAULT '[]'")
            if "entities" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN entities TEXT NOT NULL DEFAULT '[]'")
            if "projects" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN projects TEXT NOT NULL DEFAULT '[]'")
            if "raw_refs" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN raw_refs TEXT NOT NULL DEFAULT '[]'")
            if "relations" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN relations TEXT NOT NULL DEFAULT '[]'")
            if "tags_text" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN tags_text TEXT NOT NULL DEFAULT ''")
            if "topics_text" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN topics_text TEXT NOT NULL DEFAULT ''")
            if "entities_text" not in columns:
                conn.execute(
                    "ALTER TABLE memories ADD COLUMN entities_text TEXT NOT NULL DEFAULT ''"
                )
            if "projects_text" not in columns:
                conn.execute(
                    "ALTER TABLE memories ADD COLUMN projects_text TEXT NOT NULL DEFAULT ''"
                )
            if "language" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN language TEXT NOT NULL DEFAULT 'ko'")
            if "notes" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN notes TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_updated_at ON memories(updated_at DESC)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project)")
            self._refresh_search_text_columns(conn)
            self._ensure_fts(conn)
            conn.commit()

    def upsert(self, rec: MemoryRecord) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memories (
                    id, memory_type, roles, title, content, source, project, topics, entities,
                    projects, tags, tags_text, topics_text, entities_text, projects_text,
                    raw_refs, relations, confidence, sensitivity, status,
                    language, notes, created_at, updated_at, path, mcp_sig
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(id) DO UPDATE SET
                    memory_type=excluded.memory_type,
                    roles=excluded.roles,
                    title=excluded.title,
                    content=excluded.content,
                    source=excluded.source,
                    project=excluded.project,
                    topics=excluded.topics,
                    entities=excluded.entities,
                    projects=excluded.projects,
                    tags=excluded.tags,
                    tags_text=excluded.tags_text,
                    topics_text=excluded.topics_text,
                    entities_text=excluded.entities_text,
                    projects_text=excluded.projects_text,
                    raw_refs=excluded.raw_refs,
                    relations=excluded.relations,
                    confidence=excluded.confidence,
                    sensitivity=excluded.sensitivity,
                    status=excluded.status,
                    language=excluded.language,
                    notes=excluded.notes,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    path=excluded.path,
                    mcp_sig=excluded.mcp_sig
                """,
                (
                    rec.id,
                    rec.memory_type.value,
                    json.dumps([role.value for role in rec.roles], ensure_ascii=False),
                    rec.title,
                    rec.content,
                    rec.source,
                    rec.project,
                    json.dumps(rec.topics, ensure_ascii=False),
                    json.dumps(rec.entities, ensure_ascii=False),
                    json.dumps(rec.projects, ensure_ascii=False),
                    json.dumps(rec.tags, ensure_ascii=False),
                    " ".join(rec.tags),
                    " ".join(rec.topics),
                    " ".join(rec.entities),
                    " ".join(rec.projects),
                    json.dumps(rec.raw_refs, ensure_ascii=False),
                    json.dumps(
                        [relation.model_dump() for relation in rec.relations],
                        ensure_ascii=False,
                    ),
                    rec.confidence,
                    rec.sensitivity,
                    rec.status,
                    rec.language,
                    rec.notes,
                    rec.created_at.isoformat(),
                    rec.updated_at.isoformat(),
                    rec.path,
                    rec.mcp_sig,
                ),
            )
            conn.commit()

    def _row_to_dict(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        for key in ["roles", "topics", "entities", "projects", "tags", "raw_refs", "relations"]:
            item[key] = json.loads(item.get(key) or "[]")
        return item

    def get(self, memory_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        return self._row_to_dict(row)

    def recent(
        self,
        limit: int = 10,
        memory_type: str | None = None,
        project: str | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM memories WHERE 1=1"
        args: list[Any] = []
        if memory_type:
            sql += " AND memory_type = ?"
            args.append(memory_type)
        if project:
            sql += " AND project = ?"
            args.append(project)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        args.extend([limit, max(offset, 0)])
        with self._conn() as conn:
            rows = conn.execute(sql, args).fetchall()
        return [self._row_to_dict(row) for row in rows if row is not None]

    def search(
        self,
        query: str,
        limit: int = 5,
        memory_types: list[str] | None = None,
        roles: list[str] | None = None,
        topics: list[str] | None = None,
        entities: list[str] | None = None,
        projects: list[str] | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
        after: date | None = None,
        before: date | None = None,
        recency_days: int | None = None,
    ) -> list[dict[str, Any]]:
        sql = "SELECT m.* FROM memories m"
        args: list[Any] = []
        conditions: list[str] = []

        normalized_query = self._fts_query(query.strip())
        if memory_types:
            placeholders = ",".join("?" for _ in memory_types)
            conditions.append(f"m.memory_type IN ({placeholders})")
            args.extend(memory_types)

        if roles:
            for role in roles:
                conditions.append(
                    "EXISTS (SELECT 1 FROM json_each(m.roles) je WHERE lower(je.value) = lower(?))"
                )
                args.append(role)

        if topics:
            for topic in topics:
                conditions.append(
                    "EXISTS (SELECT 1 FROM json_each(m.topics) je WHERE lower(je.value) = lower(?))"
                )
                args.append(topic)

        if entities:
            for entity in entities:
                conditions.append(
                    "EXISTS (SELECT 1 FROM json_each(m.entities) je "
                    "WHERE lower(je.value) = lower(?))"
                )
                args.append(entity)

        if projects:
            for scoped_project in projects:
                conditions.append(
                    "EXISTS (SELECT 1 FROM json_each(m.projects) je "
                    "WHERE lower(je.value) = lower(?))"
                )
                args.append(scoped_project)

        if tags:
            for tag in tags:
                conditions.append(
                    "EXISTS (SELECT 1 FROM json_each(m.tags) je WHERE lower(je.value) = lower(?))"
                )
                args.append(tag)

        if project:
            conditions.append("m.project = ?")
            args.append(project)

        if status:
            conditions.append("m.status = ?")
            args.append(status)

        if after:
            conditions.append("date(m.created_at) >= date(?)")
            args.append(after.isoformat())

        if before:
            conditions.append("date(m.created_at) <= date(?)")
            args.append(before.isoformat())

        where_sql = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        if normalized_query:
            condition_sql = " AND " + " AND ".join(conditions) if conditions else ""
            sql = (
                "SELECT m.*, bm25(memories_fts, 5.0, 1.0, 0.2, 0.2, 0.2, 0.2) AS score "
                "FROM memories_fts JOIN memories m ON m.rowid = memories_fts.rowid "
                "WHERE memories_fts MATCH ?"
                + condition_sql
                + " ORDER BY score ASC, m.updated_at DESC LIMIT ?"
            )
            args = [normalized_query, *args, max(limit * 5, limit)]
        else:
            sql += f"{where_sql} ORDER BY m.updated_at DESC LIMIT ?"
            args.append(max(limit * 5, limit))

        with self._conn() as conn:
            rows = conn.execute(sql, args).fetchall()
        items = [self._row_to_dict(row) for row in rows if row is not None]

        if recency_days is not None:
            cutoff = datetime.now().astimezone() - timedelta(days=recency_days)
            filtered_items = []
            for item in items:
                updated_at = datetime.fromisoformat(item["updated_at"])
                if updated_at.tzinfo is None:
                    updated_at = updated_at.astimezone()
                if updated_at >= cutoff:
                    filtered_items.append(item)
            items = filtered_items

        return items[:limit]

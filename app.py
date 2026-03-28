from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("MEMORY_DB_PATH", str(BASE_DIR / "memory.db")))
SCHEMA_PATH = BASE_DIR / "schema.sql"
VAULT_NAME = os.getenv("MEMORY_VAULT_NAME", "MemoryVault")


# --------------------------
# helpers
# --------------------------
def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in values:
        v = normalize_text(str(item))
        if not v:
            continue
        key = v.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_memory_id() -> str:
    return f"mem-{utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"


def pack_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def unpack_json(value: str):
    return json.loads(value) if value else []


def to_flat_text(items: list[str]) -> str:
    return " ".join(normalize_list(items))


def fts_quote(term: str) -> str:
    safe = term.replace('"', '""')
    return f'"{safe}"'


# --------------------------
# models
# --------------------------
class MemorySource(str, Enum):
    chatgpt = "chatgpt"
    claude = "claude"
    grok = "grok"
    cursor = "cursor"
    manual = "manual"


class MemoryRole(str, Enum):
    decision = "decision"
    fact = "fact"
    preference = "preference"
    todo = "todo"
    summary = "summary"


class MemoryStatus(str, Enum):
    active = "active"
    superseded = "superseded"
    archived = "archived"


class RelationType(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    follows = "follows"
    supersedes = "supersedes"
    depends_on = "depends_on"
    mentions = "mentions"


class Relation(BaseModel):
    type: RelationType
    target_id: str = Field(min_length=1, max_length=120)

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, v: str) -> str:
        return normalize_text(v)


class SaveMemoryV2(BaseModel):
    schema_version: Literal["2.0"] = "2.0"
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    source: MemorySource
    roles: list[MemoryRole] = Field(min_length=1)
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw_refs: list[str] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    status: MemoryStatus = MemoryStatus.active
    occurred_at: datetime | None = None
    due_at: datetime | None = None
    language: str = Field(default="ko", min_length=2, max_length=10)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("title", "content", "notes", mode="before")
    @classmethod
    def normalize_text_fields(cls, v):
        if v is None:
            return v
        return normalize_text(str(v))

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_roles(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            v = [v]
        seen: set[str] = set()
        out: list[str] = []
        for item in v:
            role = normalize_text(str(item)).lower()
            if not role:
                continue
            if role in seen:
                continue
            seen.add(role)
            out.append(role)
        return out

    @field_validator("topics", "entities", "projects", "tags", "raw_refs", mode="before")
    @classmethod
    def normalize_list_fields(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            v = [v]
        return normalize_list([str(x) for x in v])

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, v):
        return normalize_text(str(v)).lower()

    @model_validator(mode="after")
    def derive_namespaced_tags(self) -> "SaveMemoryV2":
        derived = []
        derived.extend(f"role/{r.value}" for r in self.roles)
        derived.extend(f"topic/{x}" for x in self.topics)
        derived.extend(f"entity/{x}" for x in self.entities)
        derived.extend(f"project/{x}" for x in self.projects)
        self.tags = normalize_list(self.tags + derived)
        return self


class SearchPlan(BaseModel):
    raw_query: str
    text_terms: list[str] = Field(default_factory=list)
    roles: list[MemoryRole] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: MemoryStatus = MemoryStatus.active
    after: date | None = None
    before: date | None = None
    limit: int = Field(default=5, ge=1, le=20)


class SaveMemoryResponse(BaseModel):
    status: Literal["saved"]
    memory_id: str
    metadata: dict


class SearchHit(BaseModel):
    memory_id: str
    title: str
    content_preview: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    parsed_query: SearchPlan
    count: int
    results: list[SearchHit]


class FetchResponse(BaseModel):
    id: str
    title: str
    text: str
    url: str
    metadata: dict


# --------------------------
# query parser
# --------------------------
TOKEN_RE = re.compile(
    r'(?P<kv>[A-Za-z_][A-Za-z0-9_-]*:"[^"]*"|[A-Za-z_][A-Za-z0-9_-]*:\S+)|(?P<quoted>"[^"]*")|(?P<bare>\S+)'
)


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"잘못된 날짜 형식: {value}") from exc


def parse_search_query(q: str) -> SearchPlan:
    q = normalize_text(q)
    if not q:
        raise HTTPException(status_code=422, detail="빈 검색어는 허용되지 않습니다.")

    text_terms: list[str] = []
    roles: list[str] = []
    topics: list[str] = []
    entities: list[str] = []
    projects: list[str] = []
    tags: list[str] = []
    status = "active"
    after: date | None = None
    before: date | None = None
    limit = 5

    for m in TOKEN_RE.finditer(q):
        token = m.group(0)

        if m.group("kv"):
            key, raw_value = token.split(":", 1)
            key = key.strip().lower()
            value = raw_value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            value = normalize_text(value)

            try:
                if key == "text":
                    if value:
                        text_terms.append(value)
                elif key == "role":
                    roles.append(value.lower())
                elif key == "topic":
                    topics.append(value)
                elif key == "entity":
                    entities.append(value)
                elif key == "project":
                    projects.append(value)
                elif key == "tag":
                    tags.append(value)
                elif key == "status":
                    status = value.lower()
                elif key == "after":
                    after = parse_iso_date(value)
                elif key == "before":
                    before = parse_iso_date(value)
                elif key == "limit":
                    limit = max(1, min(20, int(value)))
                else:
                    text_terms.append(f"{key}:{value}")
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=f"잘못된 토큰 값: {token}") from exc

        elif m.group("quoted"):
            value = normalize_text(token[1:-1])
            if value:
                text_terms.append(value)
        else:
            value = normalize_text(token)
            if value:
                text_terms.append(value)

    plan = SearchPlan(
        raw_query=q,
        text_terms=normalize_list(text_terms),
        roles=roles,
        topics=normalize_list(topics),
        entities=normalize_list(entities),
        projects=normalize_list(projects),
        tags=normalize_list(tags),
        status=status,
        after=after,
        before=before,
        limit=limit,
    )
    return plan


# --------------------------
# sqlite repository
# --------------------------
class SQLiteMemoryRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def verify_features(self, conn: sqlite3.Connection) -> None:
        json_ok = conn.execute("SELECT json_valid('[]')").fetchone()[0]
        if json_ok != 1:
            raise RuntimeError("현재 SQLite 빌드에서 JSON1을 사용할 수 없습니다.")
        try:
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS temp.__fts5_check USING fts5(x)")
            conn.execute("DROP TABLE IF EXISTS temp.__fts5_check")
        except sqlite3.DatabaseError as exc:
            raise RuntimeError("현재 SQLite 빌드에서 FTS5를 사용할 수 없습니다.") from exc

    def init_db(self) -> None:
        with self.get_conn() as conn:
            self.verify_features(conn)
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            # 외부 content FTS는 기존 row 백필이 필요할 수 있다.
            conn.execute("INSERT INTO memories_fts(memories_fts) VALUES ('rebuild')")
            conn.commit()

    def save(self, payload: SaveMemoryV2) -> dict:
        now = utcnow()
        memory_id = new_memory_id()
        occurred_at = payload.occurred_at or now

        row = {
            "memory_id": memory_id,
            "schema_version": payload.schema_version,
            "title": payload.title,
            "content": payload.content,
            "source": payload.source.value,
            "roles_json": pack_json([r.value for r in payload.roles]),
            "topics_json": pack_json(payload.topics),
            "entities_json": pack_json(payload.entities),
            "projects_json": pack_json(payload.projects),
            "tags_json": pack_json(payload.tags),
            "raw_refs_json": pack_json(payload.raw_refs),
            "relations_json": pack_json([r.model_dump(mode="json") for r in payload.relations]),
            "tags_text": to_flat_text(payload.tags),
            "topics_text": to_flat_text(payload.topics),
            "entities_text": to_flat_text(payload.entities),
            "projects_text": to_flat_text(payload.projects),
            "confidence": payload.confidence,
            "status": payload.status.value,
            "occurred_at": occurred_at.isoformat(),
            "due_at": payload.due_at.isoformat() if payload.due_at else None,
            "language": payload.language,
            "notes": payload.notes,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        sql = """
        INSERT INTO memories (
            memory_id, schema_version, title, content, source,
            roles_json, topics_json, entities_json, projects_json, tags_json,
            raw_refs_json, relations_json,
            tags_text, topics_text, entities_text, projects_text,
            confidence, status, occurred_at, due_at, language, notes,
            created_at, updated_at
        ) VALUES (
            :memory_id, :schema_version, :title, :content, :source,
            :roles_json, :topics_json, :entities_json, :projects_json, :tags_json,
            :raw_refs_json, :relations_json,
            :tags_text, :topics_text, :entities_text, :projects_text,
            :confidence, :status, :occurred_at, :due_at, :language, :notes,
            :created_at, :updated_at
        )
        """

        with self.get_conn() as conn:
            conn.execute(sql, row)
            conn.commit()

        return {
            "status": "saved",
            "memory_id": memory_id,
            "metadata": {
                "roles": [r.value for r in payload.roles],
                "topics": payload.topics,
                "entities": payload.entities,
                "projects": payload.projects,
                "tags": payload.tags,
                "status": payload.status.value,
                "occurred_at": occurred_at.isoformat(),
            },
        }

    def _base_filters(self, plan: SearchPlan) -> tuple[list[str], list]:
        clauses = ["m.status = ?"]
        params: list = [plan.status.value]

        if plan.after:
            clauses.append("date(m.occurred_at) >= date(?)")
            params.append(plan.after.isoformat())
        if plan.before:
            clauses.append("date(m.occurred_at) <= date(?)")
            params.append(plan.before.isoformat())

        for role in plan.roles:
            clauses.append("EXISTS (SELECT 1 FROM json_each(m.roles_json) je WHERE je.value = ?)")
            params.append(role.value)
        for topic in plan.topics:
            clauses.append("EXISTS (SELECT 1 FROM json_each(m.topics_json) je WHERE je.value = ?)")
            params.append(topic)
        for entity in plan.entities:
            clauses.append("EXISTS (SELECT 1 FROM json_each(m.entities_json) je WHERE je.value = ?)")
            params.append(entity)
        for project in plan.projects:
            clauses.append("EXISTS (SELECT 1 FROM json_each(m.projects_json) je WHERE je.value = ?)")
            params.append(project)
        for tag in plan.tags:
            clauses.append("EXISTS (SELECT 1 FROM json_each(m.tags_json) je WHERE je.value = ?)")
            params.append(tag)

        return clauses, params

    def search(self, plan: SearchPlan) -> dict:
        clauses, params = self._base_filters(plan)

        if plan.text_terms:
            match_expr = " AND ".join(fts_quote(term) for term in plan.text_terms)
            sql = f"""
            SELECT
                m.memory_id,
                m.title,
                snippet(memories_fts, 1, '⟦', '⟧', ' … ', 18) AS content_preview,
                bm25(memories_fts, 5.0, 1.0, 0.2, 0.2, 0.2, 0.2) AS score,
                m.roles_json,
                m.topics_json,
                m.entities_json,
                m.projects_json,
                m.tags_json,
                m.confidence,
                m.status,
                m.occurred_at
            FROM memories_fts
            JOIN memories m ON m.rowid = memories_fts.rowid
            WHERE memories_fts MATCH ? AND {' AND '.join(clauses)}
            ORDER BY score ASC, m.occurred_at DESC
            LIMIT ?
            """
            query_params = [match_expr] + params + [plan.limit]
        else:
            sql = f"""
            SELECT
                m.memory_id,
                m.title,
                substr(m.content, 1, 240) AS content_preview,
                (-1.0 * m.confidence) AS score,
                m.roles_json,
                m.topics_json,
                m.entities_json,
                m.projects_json,
                m.tags_json,
                m.confidence,
                m.status,
                m.occurred_at
            FROM memories m
            WHERE {' AND '.join(clauses)}
            ORDER BY m.occurred_at DESC, m.confidence DESC
            LIMIT ?
            """
            query_params = params + [plan.limit]

        with self.get_conn() as conn:
            rows = conn.execute(sql, query_params).fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "memory_id": row["memory_id"],
                    "title": row["title"],
                    "content_preview": row["content_preview"],
                    "score": round(float(row["score"]), 6),
                    "metadata": {
                        "roles": unpack_json(row["roles_json"]),
                        "topics": unpack_json(row["topics_json"]),
                        "entities": unpack_json(row["entities_json"]),
                        "projects": unpack_json(row["projects_json"]),
                        "tags": unpack_json(row["tags_json"]),
                        "confidence": row["confidence"],
                        "status": row["status"],
                        "occurred_at": row["occurred_at"],
                    },
                }
            )
        return {"parsed_query": plan.model_dump(mode="json"), "count": len(results), "results": results}

    def fetch(self, memory_id: str) -> dict | None:
        sql = """
        SELECT
            memory_id, title, content, roles_json, topics_json, entities_json,
            projects_json, tags_json, raw_refs_json, relations_json,
            confidence, status, occurred_at
        FROM memories
        WHERE memory_id = ?
        """
        with self.get_conn() as conn:
            row = conn.execute(sql, (memory_id,)).fetchone()
        if row is None:
            return None

        occurred = datetime.fromisoformat(row["occurred_at"])
        file_path = f"memory/{occurred.strftime('%Y/%m')}/{row['memory_id']}.md"
        return {
            "id": row["memory_id"],
            "title": row["title"],
            "text": row["content"],
            "url": f"obsidian://open?vault={VAULT_NAME}&file={file_path}",
            "metadata": {
                "roles": unpack_json(row["roles_json"]),
                "topics": unpack_json(row["topics_json"]),
                "entities": unpack_json(row["entities_json"]),
                "projects": unpack_json(row["projects_json"]),
                "tags": unpack_json(row["tags_json"]),
                "raw_refs": unpack_json(row["raw_refs_json"]),
                "relations": unpack_json(row["relations_json"]),
                "confidence": row["confidence"],
                "status": row["status"],
                "occurred_at": row["occurred_at"],
            },
        }


repo = SQLiteMemoryRepository(DB_PATH)
app = FastAPI(title="memory-api-v2-sqlite")


@app.get("/healthz")
async def healthz():
    return {"ok": True, "db": str(DB_PATH)}


@app.post("/save_memory", response_model=SaveMemoryResponse)
async def save_memory(payload: SaveMemoryV2):
    return repo.save(payload)


@app.get("/search", response_model=SearchResponse)
async def search_memories(
    q: Annotated[
        str,
        Query(min_length=1, description='예: text:"aggregate split" role:decision project:HVDC entity:DSV limit:5'),
    ]
):
    plan = parse_search_query(q)
    return repo.search(plan)


@app.get("/fetch/{memory_id}", response_model=FetchResponse)
async def fetch_memory(memory_id: str):
    item = repo.fetch(memory_id)
    if item is None:
        raise HTTPException(status_code=404, detail="memory not found")
    return item


@app.on_event("startup")
async def seed_demo():
    with repo.get_conn() as conn:
        n = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    if n > 0:
        return

    repo.save(
        SaveMemoryV2(
            title="Voyage 71 aggregate split",
            content="Voyage 71은 20mm aggregate only로 유지하고, 5mm aggregate는 Voyage 72로 이연한다.",
            source="chatgpt",
            roles=["decision", "fact"],
            topics=["aggregate", "shipment", "planning"],
            entities=["DSV", "AGI"],
            projects=["HVDC"],
            raw_refs=["convo-2026-03-28-001"],
            confidence=0.92,
            occurred_at="2026-03-28T10:20:00+00:00",
        )
    )
    repo.save(
        SaveMemoryV2(
            title="사용자 응답 언어 선호",
            content="사용자는 기본 응답 언어로 한국어를 선호한다.",
            source="manual",
            roles=["preference"],
            topics=["language", "format"],
            projects=["general"],
            confidence=0.98,
            occurred_at="2026-03-28T11:00:00+00:00",
        )
    )

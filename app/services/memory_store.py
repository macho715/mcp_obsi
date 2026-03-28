from datetime import datetime
from pathlib import Path

from app.config import settings
from app.models import (
    MemoryCreate,
    MemoryPatch,
    MemoryRecord,
    MemoryRelation,
    MemoryRole,
    MemoryType,
    RawConversationCreate,
)
from app.services.daily_store import DailyStore
from app.services.index_store import IndexStore
from app.services.markdown_store import MarkdownStore
from app.services.raw_archive_store import RawArchiveStore
from app.services.schema_validator import SchemaValidator
from app.utils.ids import make_memory_id
from app.utils.integrity import sign_payload, verify_payload
from app.utils.sanitize import (
    reject_sensitive_label,
    sanitize_free_text_for_sensitivity,
    sanitize_tags,
)
from app.utils.search_query import parse_search_query
from app.utils.time import now_tz


class MemoryStore:
    ROLE_TO_MEMORY_TYPE = {
        MemoryRole.decision: MemoryType.decision,
        MemoryRole.fact: MemoryType.project_fact,
        MemoryRole.preference: MemoryType.preference,
        MemoryRole.todo: MemoryType.todo,
        MemoryRole.summary: MemoryType.conversation_summary,
    }
    MEMORY_TYPE_TO_ROLES = {
        MemoryType.decision: [MemoryRole.decision],
        MemoryType.project_fact: [MemoryRole.fact],
        MemoryType.preference: [MemoryRole.preference],
        MemoryType.todo: [MemoryRole.todo],
        MemoryType.person: [MemoryRole.fact],
        MemoryType.conversation_summary: [MemoryRole.summary],
    }

    def __init__(
        self,
        vault_path: Path,
        index_db_path: Path,
        timezone: str | None = None,
    ):
        self.vault_path = vault_path
        self.md = MarkdownStore(vault_path)
        self.daily = DailyStore(vault_path)
        self.idx = IndexStore(index_db_path)
        self.validator = SchemaValidator()
        self.raw = RawArchiveStore(
            vault_path,
            validator=self.validator,
            hmac_secret=settings.mcp_hmac_secret,
        )
        self.timezone = timezone or settings.timezone
        self.hmac_secret = settings.mcp_hmac_secret
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        for folder in ["10_Daily", "20_AI_Memory", "90_System", "mcp_raw", "memory"]:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)

    def _new_id(self, dt: datetime) -> str:
        return make_memory_id(dt)

    def _normalize_tags(self, tags: list[str]) -> list[str]:
        return sanitize_tags(tags)

    def _derive_namespaced_tags(
        self,
        tags: list[str],
        roles: list[MemoryRole] | list[str],
        topics: list[str],
        entities: list[str],
        projects: list[str],
    ) -> list[str]:
        normalized_roles = [
            role.value if isinstance(role, MemoryRole) else str(role) for role in roles
        ]
        derived = [f"role/{role}" for role in normalized_roles]
        derived.extend(f"topic/{topic}" for topic in topics)
        derived.extend(f"entity/{entity}" for entity in entities)
        derived.extend(f"project/{project}" for project in projects)
        return self._normalize_tags([*tags, *derived])

    def _normalize_list(self, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            stripped = value.strip()
            if not stripped:
                continue
            marker = stripped.casefold()
            if marker in seen:
                continue
            seen.add(marker)
            normalized.append(stripped)
        return normalized

    def _normalize_relations(self, relations: list[MemoryRelation] | None) -> list[MemoryRelation]:
        if not relations:
            return []
        normalized: list[MemoryRelation] = []
        seen: set[tuple[str, str]] = set()
        for relation in relations:
            key = (relation.type.strip(), relation.target_id.strip())
            if not key[0] or not key[1] or key in seen:
                continue
            seen.add(key)
            normalized.append(MemoryRelation(type=key[0], target_id=key[1]))
        return normalized

    def _resolve_roles(
        self, memory_type: MemoryType | None, roles: list[MemoryRole]
    ) -> list[MemoryRole]:
        if roles:
            ordered_roles = list(dict.fromkeys(roles))
            if memory_type and memory_type not in self.ROLE_TO_MEMORY_TYPE.values():
                return ordered_roles
            if (
                memory_type
                and self.MEMORY_TYPE_TO_ROLES.get(memory_type)
                and self.MEMORY_TYPE_TO_ROLES[memory_type][0] not in ordered_roles
            ):
                ordered_roles.insert(0, self.MEMORY_TYPE_TO_ROLES[memory_type][0])
            return ordered_roles
        if memory_type is None:
            raise ValueError("either memory_type or roles must be provided")
        return self.MEMORY_TYPE_TO_ROLES[memory_type]

    def _resolve_memory_type(
        self, memory_type: MemoryType | None, roles: list[MemoryRole]
    ) -> MemoryType:
        if memory_type is not None:
            return memory_type
        if not roles:
            raise ValueError("either memory_type or roles must be provided")
        return self.ROLE_TO_MEMORY_TYPE[roles[0]]

    def _resolve_projects(
        self, project: str | None, projects: list[str]
    ) -> tuple[str | None, list[str]]:
        normalized_projects = self._normalize_list(projects)
        if project:
            normalized_project = reject_sensitive_label("project", project)
            if normalized_project and normalized_project not in normalized_projects:
                normalized_projects.insert(0, normalized_project)
        project_value = normalized_projects[0] if normalized_projects else None
        return project_value, normalized_projects

    def _memory_document(self, rec: MemoryRecord) -> dict:
        document = {
            "schema_type": "memory_item",
            "schema_version": rec.schema_version,
            "note_kind": rec.note_kind,
            "memory_id": rec.id,
            "memory_type": rec.memory_type.value,
            "roles": [role.value for role in rec.roles],
            "source": rec.source,
            "created_by": rec.created_by,
            "created_at_utc": rec.created_at.isoformat(),
            "updated_at_utc": rec.updated_at.isoformat(),
            "title": rec.title,
            "content": rec.content,
            "project": rec.project,
            "topics": rec.topics,
            "entities": rec.entities,
            "projects": rec.projects,
            "tags": rec.tags,
            "raw_refs": rec.raw_refs,
            "relations": [relation.model_dump() for relation in rec.relations],
            "confidence": rec.confidence,
            "status": rec.status,
            "sensitivity": rec.sensitivity,
            "language": rec.language,
            "notes": rec.notes,
            "mcp_sig": rec.mcp_sig,
        }
        self.validator.validate_memory(document)
        return document

    def _memory_rel_path(self, dt: datetime, memory_id: str, memory_type: MemoryType) -> Path:
        _ = memory_type
        return Path("memory") / dt.strftime("%Y") / dt.strftime("%m") / f"{memory_id}.md"

    def _signed_record(self, rec: MemoryRecord) -> MemoryRecord:
        if not self.hmac_secret:
            return rec.model_copy(update={"mcp_sig": None})
        document = self._memory_document(rec)
        signature = sign_payload(
            self.hmac_secret,
            {key: value for key, value in document.items() if key != "mcp_sig"},
        )
        return rec.model_copy(update={"mcp_sig": signature})

    def _verify_existing_memory_integrity(self, rel_path: str, expected_sig: str | None) -> None:
        if not self.hmac_secret:
            return
        if expected_sig is None:
            return
        existing = self.md.read_memory_document(rel_path)
        if existing is None:
            raise ValueError(f"stored memory file missing for integrity check: {rel_path}")
        existing_sig = existing.get("mcp_sig")
        if existing_sig != expected_sig:
            raise ValueError(f"stored memory integrity check failed for {rel_path}")
        self.validator.validate_memory(existing)
        if not verify_payload(
            self.hmac_secret,
            existing,
            existing_sig,
        ):
            raise ValueError(f"stored memory integrity check failed for {rel_path}")

    def archive_raw_conversation(self, payload: RawConversationCreate) -> dict:
        return self.raw.save(payload)

    def save(self, payload: MemoryCreate) -> dict:
        now = payload.occurred_at or now_tz(self.timezone)
        memory_id = self._new_id(now)
        roles = self._resolve_roles(payload.memory_type, payload.roles)
        memory_type = self._resolve_memory_type(payload.memory_type, roles)
        project_value, project_values = self._resolve_projects(payload.project, payload.projects)
        rel_path = self._memory_rel_path(now, memory_id, memory_type)

        rec = MemoryRecord(
            id=memory_id,
            memory_type=memory_type,
            roles=roles,
            title=sanitize_free_text_for_sensitivity("title", payload.title, payload.sensitivity),
            content=sanitize_free_text_for_sensitivity(
                "content",
                payload.content,
                payload.sensitivity,
            ),
            source=reject_sensitive_label("source", payload.source) or "",
            created_by=reject_sensitive_label("created_by", payload.created_by) or "mcp-server",
            project=project_value,
            topics=self._normalize_list(payload.topics),
            entities=self._normalize_list(payload.entities),
            projects=project_values,
            tags=self._derive_namespaced_tags(
                payload.tags,
                roles,
                self._normalize_list(payload.topics),
                self._normalize_list(payload.entities),
                project_values,
            ),
            raw_refs=self._normalize_list(payload.raw_refs),
            relations=self._normalize_relations(payload.relations),
            confidence=payload.confidence,
            sensitivity=payload.sensitivity,
            status=payload.status,
            language=payload.language,
            notes=payload.notes.strip() if payload.notes is not None else None,
            created_at=now,
            updated_at=now,
            path=str(rel_path).replace("\\", "/"),
        )

        rec = self._signed_record(rec)
        self._memory_document(rec)
        self.md.write_memory(rec)
        self.idx.upsert(rec)

        if payload.append_daily:
            self.daily.append_memory(rec)

        return {"id": rec.id, "path": rec.path, "status": "saved"}

    def search(
        self,
        query: str,
        types=None,
        roles=None,
        topics=None,
        entities=None,
        projects=None,
        project=None,
        tags=None,
        limit: int = 5,
        recency_days: int | None = None,
    ) -> dict:
        search_plan = parse_search_query(query, default_limit=limit)
        resolved_roles = self._normalize_list(roles or [])
        resolved_topics = self._normalize_list(topics or [])
        resolved_entities = self._normalize_list(entities or [])
        resolved_projects = self._normalize_list(projects or [])
        resolved_tags = self._normalize_tags(tags or [])

        merged_roles = list(dict.fromkeys([*search_plan.roles, *resolved_roles]))
        merged_topics = list(dict.fromkeys([*search_plan.topics, *resolved_topics]))
        merged_entities = list(dict.fromkeys([*search_plan.entities, *resolved_entities]))
        merged_projects = list(dict.fromkeys([*search_plan.projects, *resolved_projects]))
        merged_tags = list(dict.fromkeys([*search_plan.tags, *resolved_tags]))
        text_query = " ".join(search_plan.text_terms).strip()
        effective_query = text_query if text_query else query.strip()

        rows = self.idx.search(
            query=effective_query,
            memory_types=types,
            roles=merged_roles,
            topics=merged_topics,
            entities=merged_entities,
            projects=merged_projects,
            project=project,
            tags=merged_tags,
            status=search_plan.status,
            after=search_plan.after,
            before=search_plan.before,
            limit=search_plan.limit or limit,
            recency_days=recency_days,
        )
        hits = []
        for row in rows:
            hits.append(
                {
                    "id": row["id"],
                    "type": row["memory_type"],
                    "roles": row["roles"],
                    "title": row["title"],
                    "content": row["content"][:300],
                    "source": row["source"],
                    "project": row["project"],
                    "topics": row["topics"],
                    "entities": row["entities"],
                    "projects": row["projects"],
                    "tags": row["tags"],
                    "raw_refs": row["raw_refs"],
                    "confidence": row["confidence"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "path": row["path"],
                }
            )
        return {"results": hits}

    def get(self, memory_id: str) -> dict | None:
        row = self.idx.get(memory_id)
        if not row:
            return None
        return {
            "id": row["id"],
            "type": row["memory_type"],
            "roles": row["roles"],
            "title": row["title"],
            "content": row["content"],
            "source": row["source"],
            "project": row["project"],
            "topics": row["topics"],
            "entities": row["entities"],
            "projects": row["projects"],
            "tags": row["tags"],
            "raw_refs": row["raw_refs"],
            "relations": row["relations"],
            "confidence": row["confidence"],
            "sensitivity": row["sensitivity"],
            "status": row["status"],
            "language": row["language"],
            "notes": row["notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "path": row["path"],
            "mcp_sig": row.get("mcp_sig"),
        }

    def recent(
        self, limit: int = 10, memory_type: str | None = None, project: str | None = None
    ) -> dict:
        rows = self.idx.recent(limit=limit, memory_type=memory_type, project=project)
        return {
            "results": [
                {
                    "id": row["id"],
                    "type": row["memory_type"],
                    "roles": row["roles"],
                    "title": row["title"],
                    "source": row["source"],
                    "project": row["project"],
                    "projects": row["projects"],
                    "created_at": row["created_at"],
                    "path": row["path"],
                }
                for row in rows
            ]
        }

    def update(self, patch: MemoryPatch) -> dict:
        current = self.get(patch.memory_id)
        if not current:
            return {"status": "not_found", "id": patch.memory_id}

        self._verify_existing_memory_integrity(current["path"], current.get("mcp_sig"))
        now = now_tz(self.timezone)
        updated = MemoryRecord(
            id=current["id"],
            memory_type=current["type"],
            roles=self._resolve_roles(
                current["type"],
                patch.roles if patch.roles is not None else current.get("roles", []),
            ),
            title=sanitize_free_text_for_sensitivity(
                "title",
                patch.title,
                current["sensitivity"],
            )
            if patch.title is not None
            else current["title"],
            content=sanitize_free_text_for_sensitivity(
                "content",
                patch.content,
                current["sensitivity"],
            )
            if patch.content is not None
            else current["content"],
            source=current["source"],
            created_by="mcp-server",
            project=self._resolve_projects(
                current["project"],
                patch.projects if patch.projects is not None else current.get("projects", []),
            )[0],
            topics=self._normalize_list(
                patch.topics if patch.topics is not None else current.get("topics", [])
            ),
            entities=self._normalize_list(
                patch.entities if patch.entities is not None else current.get("entities", [])
            ),
            projects=self._resolve_projects(
                current["project"],
                patch.projects if patch.projects is not None else current.get("projects", []),
            )[1],
            tags=self._derive_namespaced_tags(
                patch.tags if patch.tags is not None else current["tags"],
                self._resolve_roles(
                    current["type"],
                    patch.roles if patch.roles is not None else current.get("roles", []),
                ),
                self._normalize_list(
                    patch.topics if patch.topics is not None else current.get("topics", [])
                ),
                self._normalize_list(
                    patch.entities if patch.entities is not None else current.get("entities", [])
                ),
                self._resolve_projects(
                    current["project"],
                    patch.projects if patch.projects is not None else current.get("projects", []),
                )[1],
            ),
            raw_refs=self._normalize_list(
                patch.raw_refs if patch.raw_refs is not None else current.get("raw_refs", [])
            ),
            relations=self._normalize_relations(
                patch.relations if patch.relations is not None else current.get("relations", [])
            ),
            confidence=patch.confidence if patch.confidence is not None else current["confidence"],
            sensitivity=current["sensitivity"],
            status=patch.status or current["status"],
            language=patch.language or current.get("language", "ko"),
            notes=patch.notes if patch.notes is not None else current.get("notes"),
            created_at=datetime.fromisoformat(current["created_at"]),
            updated_at=now,
            path=current["path"],
        )

        updated = self._signed_record(updated)
        self._memory_document(updated)
        self.md.write_memory(updated)
        self.idx.upsert(updated)
        return {"status": "updated", "id": updated.id, "path": updated.path}

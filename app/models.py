from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\r\n", "\n").replace("\r", "\n").split()).strip()


def _normalize_content_text(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    while "\n\n\n" in normalized:
        normalized = normalized.replace("\n\n\n", "\n\n")
    return normalized.strip()


def _normalize_string_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _normalize_text(str(value))
        if not cleaned:
            continue
        marker = cleaned.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        normalized.append(cleaned)
    return normalized


class MemoryType(StrEnum):
    preference = "preference"
    project_fact = "project_fact"
    decision = "decision"
    person = "person"
    todo = "todo"
    conversation_summary = "conversation_summary"


class MemoryRole(StrEnum):
    decision = "decision"
    fact = "fact"
    preference = "preference"
    todo = "todo"
    summary = "summary"


class MemoryRelation(BaseModel):
    type: str
    target_id: str

    @field_validator("type", "target_id", mode="before")
    @classmethod
    def normalize_relation_fields(cls, value: str) -> str:
        return _normalize_text(str(value))


class MemoryRecord(BaseModel):
    id: str
    schema_version: str = "2.0"
    note_kind: str = "memory"
    memory_type: MemoryType
    roles: list[MemoryRole] = Field(default_factory=list)
    title: str
    content: str
    source: str
    created_by: str = "mcp-server"
    project: str | None = None
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw_refs: list[str] = Field(default_factory=list)
    relations: list[MemoryRelation] = Field(default_factory=list)
    confidence: float = 0.8
    sensitivity: str = "p1"
    status: str = "active"
    language: str = "ko"
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    path: str
    mcp_sig: str | None = None


class MemoryCreate(BaseModel):
    schema_version: str = "2.0"
    memory_type: MemoryType | None = None
    title: str
    content: str
    source: str
    created_by: str = "mcp-server"
    project: str | None = None
    roles: list[MemoryRole] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw_refs: list[str] = Field(default_factory=list)
    relations: list[MemoryRelation] = Field(default_factory=list)
    confidence: float = 0.8
    sensitivity: str = "p1"
    status: str = "active"
    language: str = "ko"
    notes: str | None = None
    append_daily: bool = True
    occurred_at: datetime | None = None
    due_at: datetime | None = None

    @field_validator("title", "notes", mode="before")
    @classmethod
    def normalize_text_fields(cls, value):
        if value is None:
            return value
        return _normalize_text(str(value))

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content_field(cls, value):
        if value is None:
            return value
        return _normalize_content_text(str(value))

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_roles(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            role = _normalize_text(str(item)).lower()
            if not role or role in seen:
                continue
            seen.add(role)
            normalized.append(role)
        return normalized

    @field_validator("topics", "entities", "projects", "tags", "raw_refs", mode="before")
    @classmethod
    def normalize_list_fields(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]
        return _normalize_string_list([str(item) for item in value])

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return _normalize_text(str(value)).lower()

    @model_validator(mode="after")
    def derive_namespaced_tags(self) -> "MemoryCreate":
        derived_tags = [f"role/{role.value}" for role in self.roles]
        derived_tags.extend(f"topic/{topic}" for topic in self.topics)
        derived_tags.extend(f"entity/{entity}" for entity in self.entities)
        derived_tags.extend(f"project/{project}" for project in self.projects)
        self.tags = _normalize_string_list([*self.tags, *derived_tags])
        return self


class MemoryPatch(BaseModel):
    memory_id: str
    title: str | None = None
    content: str | None = None
    roles: list[MemoryRole] | None = None
    topics: list[str] | None = None
    entities: list[str] | None = None
    projects: list[str] | None = None
    tags: list[str] | None = None
    raw_refs: list[str] | None = None
    relations: list[MemoryRelation] | None = None
    confidence: float | None = None
    status: str | None = None
    language: str | None = None
    notes: str | None = None

    @field_validator("title", "notes", mode="before")
    @classmethod
    def normalize_patch_text_fields(cls, value):
        if value is None:
            return value
        return _normalize_text(str(value))

    @field_validator("content", mode="before")
    @classmethod
    def normalize_patch_content_field(cls, value):
        if value is None:
            return value
        return _normalize_content_text(str(value))

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_patch_roles(cls, value):
        if value is None:
            return value
        if not isinstance(value, list):
            value = [value]
        normalized_roles = [
            _normalize_text(str(item)).lower() for item in value if _normalize_text(str(item))
        ]
        return list(dict.fromkeys(normalized_roles))

    @field_validator("topics", "entities", "projects", "tags", "raw_refs", mode="before")
    @classmethod
    def normalize_patch_list_fields(cls, value):
        if value is None:
            return value
        if not isinstance(value, list):
            value = [value]
        return _normalize_string_list([str(item) for item in value])

    @field_validator("language", mode="before")
    @classmethod
    def normalize_patch_language(cls, value):
        if value is None:
            return value
        return _normalize_text(str(value)).lower()


class RawConversationCreate(BaseModel):
    mcp_id: str
    source: str
    body_markdown: str
    created_by: str = "mcp-server"
    created_at_utc: datetime | None = None
    conversation_date: date | None = None
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    mcp_sig: str | None = None


class SearchPlan(BaseModel):
    raw_query: str
    text_terms: list[str] = Field(default_factory=list)
    roles: list[MemoryRole] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: str | None = None
    after: date | None = None
    before: date | None = None
    limit: int | None = Field(default=None, ge=1, le=20)

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    preference = "preference"
    project_fact = "project_fact"
    decision = "decision"
    person = "person"
    todo = "todo"
    conversation_summary = "conversation_summary"


class MemoryRecord(BaseModel):
    id: str
    memory_type: MemoryType
    title: str
    content: str
    source: str
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.80
    sensitivity: str = "p1"
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    path: str

    def to_search_item(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.content,
            "metadata": {
                "memory_type": self.memory_type.value,
                "project": self.project,
                "tags": self.tags,
                "confidence": self.confidence,
                "sensitivity": self.sensitivity,
                "status": self.status,
                "path": self.path,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
            },
        }


class MemoryCreate(BaseModel):
    memory_type: MemoryType
    title: str
    content: str
    source: str
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.80
    sensitivity: str = "p1"
    append_daily: bool = True
    occurred_at: datetime | None = None


class MemoryPatch(BaseModel):
    memory_id: str
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    confidence: float | None = None
    status: str | None = None

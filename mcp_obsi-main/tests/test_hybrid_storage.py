import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from app.config import settings
from app.models import MemoryCreate, RawConversationCreate
from app.services.memory_store import MemoryStore
from app.services.schema_validator import SchemaValidator


def test_memory_note_uses_hybrid_frontmatter_schema(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    result = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Hybrid decision",
            content="Normalize and persist memory notes.",
            source="chatgpt",
            created_by="mcp-server",
            append_daily=False,
        )
    )

    note_path = vault / result["path"]
    raw = note_path.read_text(encoding="utf-8")
    frontmatter_raw = raw.split("---\n", 2)[1]
    frontmatter = yaml.safe_load(frontmatter_raw)

    assert frontmatter["schema_type"] == "memory_item"
    assert frontmatter["memory_id"] == result["id"]
    assert frontmatter["memory_type"] == "decision"
    assert frontmatter["created_by"] == "mcp-server"
    assert "updated_at_utc" in frontmatter


def test_raw_conversation_archive_is_saved_outside_memory_index(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    raw_result = store.archive_raw_conversation(
        RawConversationCreate(
            mcp_id="convo-2026-03-28-001",
            source="chatgpt",
            created_by="plugin-user",
            created_at_utc=datetime(2026, 3, 28, 8, 30, tzinfo=UTC),
            conversation_date=datetime(2026, 3, 28, 8, 30, tzinfo=UTC).date(),
            project="HVDC",
            tags=["raw", "demo"],
            body_markdown="## User\nraw body\n\n## Assistant\nreply",
        )
    )

    raw_path = vault / raw_result["path"]
    raw_frontmatter = yaml.safe_load(raw_path.read_text(encoding="utf-8").split("---\n", 2)[1])

    assert raw_path.exists()
    assert raw_result["path"] == "mcp_raw/chatgpt/2026-03-28/convo-2026-03-28-001.md"
    assert raw_frontmatter["schema_type"] == "raw_conversation"

    search_results = store.search(query="raw body", limit=5)
    assert search_results["results"] == []


def test_raw_conversation_archive_gets_mcp_sig_when_secret_enabled(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    original_secret = settings.mcp_hmac_secret
    settings.mcp_hmac_secret = "unit-test-hmac-secret"

    try:
        store = MemoryStore(vault, db, timezone="UTC")
        raw_result = store.archive_raw_conversation(
            RawConversationCreate(
                mcp_id="convo-2026-03-28-001-signed",
                source="chatgpt",
                created_by="plugin-user",
                created_at_utc=datetime(2026, 3, 28, 8, 45, tzinfo=UTC),
                conversation_date=datetime(2026, 3, 28, 8, 45, tzinfo=UTC).date(),
                project="HVDC",
                tags=["raw", "demo"],
                body_markdown="## User\nraw body\n\n## Assistant\nreply",
            )
        )

        raw_path = vault / raw_result["path"]
        raw_frontmatter = yaml.safe_load(raw_path.read_text(encoding="utf-8").split("---\n", 2)[1])

        assert raw_path.exists()
        assert raw_frontmatter["mcp_sig"] is not None
        assert raw_frontmatter["mcp_sig"].startswith("hmac-sha256:")
    finally:
        settings.mcp_hmac_secret = original_secret


def test_schema_files_parse_and_validate_examples():
    schema_root = Path(__file__).resolve().parents[1] / "schemas"
    raw_schema = json.loads(
        (schema_root / "raw-conversation.schema.json").read_text(encoding="utf-8")
    )
    memory_schema = json.loads(
        (schema_root / "memory-item.schema.json").read_text(encoding="utf-8")
    )
    memory_schema_v2 = json.loads(
        (schema_root / "memory-item-v2.schema.json").read_text(encoding="utf-8")
    )

    assert raw_schema["$id"] == "raw-conversation.schema.json"
    assert memory_schema["$id"] == "memory-item.schema.json"
    assert memory_schema_v2["$id"] == "memory-item-v2.schema.json"

    validator = SchemaValidator(schema_root=schema_root)
    validator.validate_raw(
        {
            "schema_type": "raw_conversation",
            "mcp_id": "convo-2026-03-28-001",
            "source": "chatgpt",
            "created_by": "plugin-user",
            "created_at_utc": "2026-03-28T08:30:00+00:00",
            "conversation_date": "2026-03-28",
            "project": "HVDC",
            "tags": ["raw", "demo"],
            "mcp_sig": None,
            "body_markdown": "raw body",
        }
    )
    validator.validate_memory(
        {
            "schema_type": "memory_item",
            "schema_version": "2.0",
            "note_kind": "memory",
            "memory_id": "MEM-20260328-083000-A1B2C3",
            "memory_type": "decision",
            "roles": ["decision"],
            "source": "chatgpt",
            "created_by": "mcp-server",
            "created_at_utc": "2026-03-28T08:30:00+00:00",
            "updated_at_utc": "2026-03-28T08:35:00+00:00",
            "title": "Decision",
            "content": "content",
            "project": "HVDC",
            "topics": ["grid planning"],
            "entities": ["transformer-a"],
            "projects": ["HVDC Rollout"],
            "tags": ["decision"],
            "raw_refs": ["raw-2026-03-28-001"],
            "relations": [],
            "confidence": 0.8,
            "status": "active",
            "sensitivity": "p1",
            "language": "ko",
            "notes": None,
            "mcp_sig": None,
        }
    )
    validator.validate_memory(
        {
            "schema_type": "memory_item",
            "memory_id": "MEM-20260328-083000-A1B2C3",
            "memory_type": "decision",
            "source": "chatgpt",
            "created_by": "mcp-server",
            "created_at_utc": "2026-03-28T08:30:00+00:00",
            "updated_at_utc": "2026-03-28T08:35:00+00:00",
            "title": "Decision",
            "content": "content",
            "project": "HVDC",
            "tags": ["decision"],
            "confidence": 0.8,
            "status": "active",
            "sensitivity": "p1",
            "mcp_sig": None,
        }
    )

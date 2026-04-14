from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.models import MemoryCreate, MemoryPatch, RawConversationCreate
from app.services.memory_store import MemoryStore


def test_save_memory_masks_mixed_secret_text_in_markdown_and_index(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    raw_secret = "Bearer abcdefghijklmnop token=supersecret sk-ABCDEF12345678"
    result = store.save(
        MemoryCreate(
            memory_type="decision",
            title=f"Deployment note {raw_secret}",
            content=f"Store this note but mask credentials: {raw_secret}",
            source="chatgpt",
            created_by="tester",
            append_daily=False,
        )
    )

    note_text = (vault / result["path"]).read_text(encoding="utf-8")
    item = store.get(result["id"])
    index_row = store.idx.get(result["id"])

    assert "abcdefghijklmnop" not in note_text
    assert "supersecret" not in note_text
    assert "ABCDEF12345678" not in note_text
    assert item is not None
    assert "[REDACTED]" in item["content"]
    assert index_row is not None
    assert "supersecret" not in index_row["content"]


def test_save_memory_rejects_secret_only_payload(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    with pytest.raises(ValueError, match="content contains only sensitive material"):
        store.save(
            MemoryCreate(
                memory_type="decision",
                title="Leak",
                content="Bearer abcdefghijklmnop",
                source="chatgpt",
                created_by="tester",
                append_daily=False,
            )
        )


def test_save_memory_rejects_sensitive_project_and_tags(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    with pytest.raises(ValueError, match="project contains sensitive token-like data"):
        store.save(
            MemoryCreate(
                memory_type="project_fact",
                title="Project settings",
                content="Normal content",
                source="chatgpt",
                created_by="tester",
                project="token=supersecret",
                append_daily=False,
            )
        )

    with pytest.raises(ValueError, match="tags contains sensitive token-like data"):
        store.save(
            MemoryCreate(
                memory_type="project_fact",
                title="Tagged settings",
                content="Normal content",
                source="chatgpt",
                created_by="tester",
                tags=["api_key=supersecret"],
                append_daily=False,
            )
        )


def test_update_memory_masks_new_secret_text(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    created = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Baseline",
            content="No secret here",
            source="chatgpt",
            created_by="tester",
            append_daily=False,
        )
    )

    result = store.update(
        MemoryPatch(
            memory_id=created["id"],
            content="Rotated token=supersecret but keep the note",
        )
    )

    item = store.get(result["id"])
    assert item is not None
    assert "supersecret" not in item["content"]
    assert "[REDACTED]" in item["content"]


def test_save_memory_p2_rejects_mixed_secret_text_in_free_text(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    with pytest.raises(ValueError, match="sensitive fragments disallowed for sensitivity p2"):
        store.save(
            MemoryCreate(
                memory_type="decision",
                title="Mixed secret note token=supersecret",
                content="Keep token=supersecret in the body",
                source="chatgpt",
                created_by="tester",
                sensitivity="p2",
                append_daily=False,
            )
        )


def test_update_memory_p2_rejects_mixed_secret_text_in_free_text(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    created = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Baseline p2 note",
            content="Safe baseline",
            source="chatgpt",
            created_by="tester",
            sensitivity="p2",
            append_daily=False,
        )
    )

    with pytest.raises(ValueError, match="sensitive fragments disallowed for sensitivity p2"):
        store.update(
            MemoryPatch(
                memory_id=created["id"],
                content="Rotated token=supersecret but keep the note",
            )
        )


def test_update_memory_preserves_existing_state_when_rejected(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    created = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Safe baseline",
            content="Safe content",
            source="chatgpt",
            created_by="tester",
            project="preview",
            append_daily=False,
        )
    )
    before = store.get(created["id"])

    with pytest.raises(ValueError, match="title contains only sensitive material"):
        store.update(
            MemoryPatch(
                memory_id=created["id"],
                title="token=supersecret",
            )
        )

    after = store.get(created["id"])
    assert before is not None
    assert after == before


def test_raw_archive_masks_mixed_text_and_rejects_secret_only_payload(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "90_System" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    mixed = store.archive_raw_conversation(
        RawConversationCreate(
            mcp_id="convo-2026-03-28-mask",
            source="chatgpt",
            created_by="tester",
            created_at_utc=datetime(2026, 3, 28, 8, 30, tzinfo=UTC),
            conversation_date=datetime(2026, 3, 28, 8, 30, tzinfo=UTC).date(),
            tags=["raw", "demo"],
            body_markdown="Conversation with token=supersecret inside a sentence",
        )
    )

    raw_text = (vault / mixed["path"]).read_text(encoding="utf-8")
    assert "supersecret" not in raw_text
    assert "[REDACTED]" in raw_text

    with pytest.raises(ValueError, match="body_markdown contains only sensitive material"):
        store.archive_raw_conversation(
            RawConversationCreate(
                mcp_id="convo-2026-03-28-reject",
                source="chatgpt",
                created_by="tester",
                created_at_utc=datetime(2026, 3, 28, 8, 31, tzinfo=UTC),
                conversation_date=datetime(2026, 3, 28, 8, 31, tzinfo=UTC).date(),
                body_markdown="password=supersecret",
            )
        )

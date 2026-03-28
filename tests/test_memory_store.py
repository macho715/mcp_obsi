from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.config import settings
from app.models import MemoryCreate, MemoryPatch, MemoryRole
from app.services.memory_store import MemoryStore


def test_save_writes_markdown_and_index(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    result = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Voyage 71 decision",
            content="5mm aggregate deferred to Voyage 72.",
            source="manual",
            project="HVDC",
            tags=["voyage71", "aggregate"],
            append_daily=True,
        )
    )

    assert result["status"] == "saved"
    item = store.get(result["id"])
    assert item is not None
    assert item["title"] == "Voyage 71 decision"
    assert item["path"].startswith("memory/")
    assert (vault / item["path"]).exists()
    note_date = datetime.fromisoformat(item["updated_at"]).strftime("%Y-%m-%d")
    daily_note = vault / "10_Daily" / f"{note_date}.md"
    assert (vault / "10_Daily").exists()
    assert daily_note.exists()
    assert "## AI Memory Log" in daily_note.read_text(encoding="utf-8")


def test_save_v2_memory_with_metadata_arrays_persists_frontmatter_and_index(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    result = store.save(
        MemoryCreate(
            roles=[MemoryRole.decision],
            title="Voyage 72 metadata",
            content="Capture the v2 memory metadata shape.",
            source="manual",
            created_by="tester",
            topics=[" Grid Planning ", "grid planning", "Converter Stations"],
            entities=["Transformer A", " transformer a ", "Switchyard"],
            projects=["HVDC Expansion", "hvdc expansion", "HVDC Rollout"],
            raw_refs=["raw-2026-03-28-001", " raw-2026-03-28-001 ", "raw-2026-03-28-002"],
            append_daily=False,
        )
    )

    item = store.get(result["id"])
    document = store.md.read_memory_document(result["path"])

    assert result["status"] == "saved"
    assert item is not None
    assert document is not None
    assert item["type"] == "decision"
    assert item["roles"] == ["decision"]
    assert item["topics"] == ["Grid Planning", "Converter Stations"]
    assert item["entities"] == ["Transformer A", "Switchyard"]
    assert item["projects"] == ["HVDC Expansion", "HVDC Rollout"]
    assert item["raw_refs"] == ["raw-2026-03-28-001", "raw-2026-03-28-002"]
    assert document["schema_version"] == "2.0"
    assert document["note_kind"] == "memory"
    assert document["roles"] == ["decision"]
    assert document["topics"] == ["Grid Planning", "Converter Stations"]
    assert document["entities"] == ["Transformer A", "Switchyard"]
    assert document["projects"] == ["HVDC Expansion", "HVDC Rollout"]
    assert document["raw_refs"] == ["raw-2026-03-28-001", "raw-2026-03-28-002"]


def test_save_skips_daily_note_when_disabled(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    result = store.save(
        MemoryCreate(
            memory_type="project_fact",
            title="Warehouse threshold",
            content="Trigger alert above 85 percent occupancy.",
            source="manual",
            append_daily=False,
        )
    )

    assert result["status"] == "saved"
    assert (vault / "10_Daily").exists()
    note_date = datetime.fromisoformat(store.get(result["id"])["updated_at"]).strftime("%Y-%m-%d")
    assert not (vault / "10_Daily" / f"{note_date}.md").exists()


def test_search_filters_by_topic_entity_and_project_metadata(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    matched = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Shared rollout note",
            content="shared content for metadata filtering",
            source="manual",
            topics=[" Grid Planning ", "Converter Stations"],
            entities=["Transformer A", "Switchyard"],
            projects=["HVDC Expansion", "HVDC Rollout"],
            append_daily=False,
        )
    )
    store.save(
        MemoryCreate(
            memory_type="decision",
            title="Shared rollout decoy",
            content="shared content for metadata filtering",
            source="manual",
            topics=["Other Topic"],
            entities=["Other Entity"],
            projects=["Other Program"],
            append_daily=False,
        )
    )

    result = store.search(
        query="shared content",
        topics=["grid planning"],
        entities=["transformer a"],
        projects=["hvdc rollout"],
    )

    assert [row["id"] for row in result["results"]] == [matched["id"]]


def test_update_normalizes_content_and_tags(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    created = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Original title",
            content="Original content",
            source="manual",
            tags=["Alpha Tag"],
            append_daily=False,
        )
    )

    result = store.update(
        MemoryPatch(
            memory_id=created["id"],
            title="  Updated title  ",
            content="Line one\r\n\r\n\r\nLine two",
            tags=["  New Tag  ", "new   tag", "Second Tag"],
        )
    )

    assert result["status"] == "updated"
    item = store.get(created["id"])
    assert item is not None
    assert item["title"] == "Updated title"
    assert item["content"] == "Line one\n\nLine two"
    assert item["tags"] == ["new-tag", "second-tag", "role/decision"]


def test_search_filters_by_normalized_tags_and_recency(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    old_occurred_at = datetime.now(UTC) - timedelta(days=10)
    new_occurred_at = datetime.now(UTC)

    store.save(
        MemoryCreate(
            memory_type="decision",
            title="Old safety note",
            content="Older note",
            source="manual",
            tags=["Legacy Tag"],
            append_daily=False,
            occurred_at=old_occurred_at,
        )
    )
    store.save(
        MemoryCreate(
            memory_type="decision",
            title="Recent safety note",
            content="Recent note",
            source="manual",
            tags=["Legacy Tag", "Priority"],
            append_daily=False,
            occurred_at=new_occurred_at,
        )
    )

    result = store.search(
        query="safety",
        tags=["legacy   tag", "priority"],
        recency_days=2,
    )

    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "Recent safety note"


def test_save_persists_normalized_record_and_index_row(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    result = store.save(
        MemoryCreate(
            memory_type="decision",
            title="  Preview decision  ",
            content="First line\r\n\r\n\r\nSecond line",
            source="manual",
            created_by="tester",
            project="preview",
            tags=["Preview Tag", "preview tag"],
            append_daily=False,
        )
    )

    item = store.get(result["id"])
    row = store.idx.get(result["id"])

    assert result["status"] == "saved"
    assert item is not None
    assert row is not None
    assert item["title"] == "Preview decision"
    assert item["content"] == "First line\n\nSecond line"
    assert item["path"].startswith("memory/")
    assert item["tags"] == ["preview-tag", "role/decision", "project/preview"]
    assert row["title"] == item["title"]
    assert row["content"] == item["content"]
    assert row["path"] == item["path"]
    assert (vault / item["path"]).exists()


def test_update_changes_only_requested_fields(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db)

    created = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Initial",
            content="Initial content",
            source="manual",
            created_by="tester",
            project="preview",
            tags=["Alpha"],
            confidence=0.55,
            append_daily=False,
        )
    )
    before = store.get(created["id"])

    result = store.update(
        MemoryPatch(
            memory_id=created["id"],
            title="Updated",
            content="Updated content",
        )
    )
    after = store.get(created["id"])

    assert result["status"] == "updated"
    assert before is not None
    assert after is not None
    assert after["title"] == "Updated"
    assert after["content"] == "Updated content"
    assert after["source"] == before["source"]
    assert after["project"] == before["project"]
    assert after["tags"] == before["tags"]
    assert after["confidence"] == before["confidence"]
    assert after["status"] == before["status"]


def test_failed_update_leaves_existing_record_unchanged(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    created = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Stable title",
            content="Stable content",
            source="manual",
            created_by="tester",
            project="preview",
            tags=["Stable"],
            append_daily=False,
        )
    )
    before = store.get(created["id"])

    with pytest.raises(ValueError, match="content contains only sensitive material"):
        store.update(
            MemoryPatch(
                memory_id=created["id"],
                content="Bearer abcdefghijklmnop",
            )
        )

    after = store.get(created["id"])
    row = store.idx.get(created["id"])

    assert before is not None
    assert after == before
    assert row is not None
    assert row["content"] == before["content"]


def test_signed_memory_is_written_with_mcp_sig_when_secret_is_enabled(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    original_secret = settings.mcp_hmac_secret
    settings.mcp_hmac_secret = "unit-test-hmac-secret"

    try:
        store = MemoryStore(vault, db, timezone="UTC")
        result = store.save(
            MemoryCreate(
                memory_type="decision",
                title="Signed memory note",
                content="Signed content",
                source="manual",
                created_by="tester",
                append_daily=False,
            )
        )
        item = store.get(result["id"])
        row = store.idx.get(result["id"])
        frontmatter = (vault / result["path"]).read_text(encoding="utf-8").split("---\n", 2)[1]

        assert item is not None
        assert row is not None
        assert item["mcp_sig"] is not None
        assert row["mcp_sig"] == item["mcp_sig"]
        assert "mcp_sig:" in frontmatter
    finally:
        settings.mcp_hmac_secret = original_secret


def test_tampered_signed_memory_update_is_rejected(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    original_secret = settings.mcp_hmac_secret
    settings.mcp_hmac_secret = "unit-test-hmac-secret"

    try:
        store = MemoryStore(vault, db, timezone="UTC")
        created = store.save(
            MemoryCreate(
                memory_type="decision",
                title="Tamper target",
                content="Original signed content",
                source="manual",
                created_by="tester",
                append_daily=False,
            )
        )
        path = vault / created["path"]
        tampered = path.read_text(encoding="utf-8").replace(
            "Original signed content",
            "Tampered signed content",
        )
        path.write_text(tampered, encoding="utf-8")

        with pytest.raises(ValueError, match="integrity check failed"):
            store.update(
                MemoryPatch(
                    memory_id=created["id"],
                    content="Updated content",
                )
            )
    finally:
        settings.mcp_hmac_secret = original_secret


def test_legacy_unsigned_memory_becomes_signed_on_rewrite(tmp_path: Path):
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    original_secret = settings.mcp_hmac_secret
    settings.mcp_hmac_secret = ""

    try:
        store = MemoryStore(vault, db, timezone="UTC")
        created = store.save(
            MemoryCreate(
                memory_type="decision",
                title="Legacy unsigned note",
                content="Unsigned content",
                source="manual",
                created_by="tester",
                append_daily=False,
            )
        )
        unsigned_item = store.get(created["id"])
        assert unsigned_item is not None
        assert unsigned_item["mcp_sig"] is None
    finally:
        settings.mcp_hmac_secret = original_secret

    settings.mcp_hmac_secret = "unit-test-hmac-secret"
    store = MemoryStore(vault, db, timezone="UTC")
    try:
        result = store.update(
            MemoryPatch(
                memory_id=created["id"],
                title="Legacy unsigned note updated",
            )
        )
        item = store.get(result["id"])
        row = store.idx.get(result["id"])
        frontmatter = (vault / result["path"]).read_text(encoding="utf-8").split("---\n", 2)[1]

        assert result["status"] == "updated"
        assert item is not None
        assert row is not None
        assert item["mcp_sig"] is not None
        assert row["mcp_sig"] == item["mcp_sig"]
        assert "mcp_sig:" in frontmatter
    finally:
        settings.mcp_hmac_secret = original_secret

from datetime import UTC, datetime
from pathlib import Path

from app.models import MemoryCreate
from app.services.memory_store import MemoryStore
from app.services.path_backfill import apply_memory_path_backfill


def _seed_legacy_memory(tmp_path: Path) -> tuple[MemoryStore, str, str, str]:
    vault = tmp_path / "vault"
    db = tmp_path / "data" / "memory_index.sqlite3"
    store = MemoryStore(vault, db, timezone="UTC")

    created = store.save(
        MemoryCreate(
            memory_type="decision",
            title="Legacy path candidate",
            content="Move this note to the v2 memory tree.",
            source="manual",
            append_daily=False,
            occurred_at=datetime(2026, 3, 28, 10, 0, tzinfo=UTC),
        )
    )

    memory_id = created["id"]
    current_path = created["path"]
    legacy_path = f"20_AI_Memory/decision/2026/03/{memory_id}.md"

    current_abs = vault / current_path
    legacy_abs = vault / legacy_path
    legacy_abs.parent.mkdir(parents=True, exist_ok=True)
    current_abs.replace(legacy_abs)

    with store.idx._conn() as conn:
        conn.execute("UPDATE memories SET path = ? WHERE id = ?", (legacy_path, memory_id))
        conn.commit()

    return store, memory_id, legacy_path, current_path


def test_backfill_memory_paths_dry_run_is_non_destructive(tmp_path: Path):
    store, memory_id, legacy_path, current_path = _seed_legacy_memory(tmp_path)
    vault = store.vault_path

    result = apply_memory_path_backfill(vault_path=vault, db_path=store.idx.db_path, apply=False)

    assert result["apply"] is False
    assert result["candidate_count"] == 1
    assert result["moved"] == 1
    assert result["updated_index_only"] == 0
    assert result["candidates"][0]["id"] == memory_id
    assert result["candidates"][0]["from_path"] == legacy_path
    assert result["candidates"][0]["to_path"] == current_path
    assert (vault / legacy_path).exists()
    assert not (vault / current_path).exists()
    assert store.get(memory_id)["path"] == legacy_path


def test_backfill_memory_paths_apply_moves_file_and_updates_index(tmp_path: Path):
    store, memory_id, legacy_path, current_path = _seed_legacy_memory(tmp_path)
    vault = store.vault_path

    result = apply_memory_path_backfill(vault_path=vault, db_path=store.idx.db_path, apply=True)
    item = store.get(memory_id)

    assert result["apply"] is True
    assert result["candidate_count"] == 1
    assert result["moved"] == 1
    assert result["updated_index_only"] == 0
    assert not (vault / legacy_path).exists()
    assert (vault / current_path).exists()
    assert item is not None
    assert item["path"] == current_path

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

LEGACY_MEMORY_PREFIX = "20_AI_Memory/"
CURRENT_MEMORY_PREFIX = "memory/"


@dataclass(frozen=True)
class BackfillCandidate:
    memory_id: str
    legacy_path: str
    target_path: str
    action: str
    reason: str


def build_memory_target_path(memory_id: str, created_at_iso: str) -> str:
    created_at = datetime.fromisoformat(created_at_iso)
    return f"memory/{created_at.strftime('%Y')}/{created_at.strftime('%m')}/{memory_id}.md"


def _load_candidates(
    db_path: Path,
    memory_ids: list[str] | None = None,
) -> list[tuple[str, str, str]]:
    if not db_path.exists():
        raise FileNotFoundError(f"index database not found: {db_path}")

    sql = "SELECT id, path, created_at FROM memories WHERE path LIKE ?"
    args: list[Any] = [f"{LEGACY_MEMORY_PREFIX}%"]
    if memory_ids:
        placeholders = ",".join("?" for _ in memory_ids)
        sql += f" AND id IN ({placeholders})"
        args.extend(memory_ids)
    sql += " ORDER BY created_at ASC"

    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def plan_memory_path_backfill(
    vault_path: Path,
    db_path: Path,
    memory_ids: list[str] | None = None,
) -> list[BackfillCandidate]:
    candidates: list[BackfillCandidate] = []
    for memory_id, legacy_path, created_at in _load_candidates(db_path, memory_ids):
        target_path = build_memory_target_path(memory_id, created_at)
        legacy_abs = vault_path / legacy_path
        target_abs = vault_path / target_path

        if legacy_path == target_path:
            continue

        if legacy_abs.exists() and not target_abs.exists():
            action = "move"
            reason = "legacy_exists_target_missing"
        elif not legacy_abs.exists() and target_abs.exists():
            action = "update_index_only"
            reason = "legacy_missing_target_exists"
        elif legacy_abs.exists() and target_abs.exists():
            if legacy_abs.read_text(encoding="utf-8") == target_abs.read_text(encoding="utf-8"):
                action = "update_index_only"
                reason = "target_already_exists_same_content"
            else:
                action = "conflict"
                reason = "target_already_exists_different_content"
        else:
            action = "missing"
            reason = "legacy_and_target_missing"

        candidates.append(
            BackfillCandidate(
                memory_id=memory_id,
                legacy_path=legacy_path,
                target_path=target_path,
                action=action,
                reason=reason,
            )
        )
    return candidates


def apply_memory_path_backfill(
    vault_path: Path,
    db_path: Path,
    apply: bool = False,
    memory_ids: list[str] | None = None,
) -> dict[str, Any]:
    candidates = plan_memory_path_backfill(
        vault_path=vault_path, db_path=db_path, memory_ids=memory_ids
    )

    summary = {
        "apply": apply,
        "candidate_count": len(candidates),
        "moved": 0,
        "updated_index_only": 0,
        "conflicts": 0,
        "missing": 0,
        "candidates": [
            {
                "id": candidate.memory_id,
                "from_path": candidate.legacy_path,
                "to_path": candidate.target_path,
                "action": candidate.action,
                "reason": candidate.reason,
            }
            for candidate in candidates
        ],
    }

    if not apply:
        for candidate in candidates:
            if candidate.action == "move":
                summary["moved"] += 1
            elif candidate.action == "update_index_only":
                summary["updated_index_only"] += 1
            elif candidate.action == "conflict":
                summary["conflicts"] += 1
            elif candidate.action == "missing":
                summary["missing"] += 1
        return summary

    conn = sqlite3.connect(db_path)
    try:
        for candidate in candidates:
            if candidate.action == "move":
                source = vault_path / candidate.legacy_path
                target = vault_path / candidate.target_path
                target.parent.mkdir(parents=True, exist_ok=True)
                source.replace(target)
                conn.execute(
                    "UPDATE memories SET path = ? WHERE id = ?",
                    (candidate.target_path, candidate.memory_id),
                )
                summary["moved"] += 1
            elif candidate.action == "update_index_only":
                conn.execute(
                    "UPDATE memories SET path = ? WHERE id = ?",
                    (candidate.target_path, candidate.memory_id),
                )
                summary["updated_index_only"] += 1
            elif candidate.action == "conflict":
                summary["conflicts"] += 1
            elif candidate.action == "missing":
                summary["missing"] += 1
        conn.commit()
    finally:
        conn.close()

    return summary

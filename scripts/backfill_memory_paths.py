from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_runtime() -> tuple[object, object]:
    from app.config import settings
    from app.services.path_backfill import apply_memory_path_backfill

    return settings, apply_memory_path_backfill


def parse_args() -> argparse.Namespace:
    settings, _ = _load_runtime()
    parser = argparse.ArgumentParser(
        description="Backfill legacy 20_AI_Memory note paths into memory/YYYY/MM."
    )
    parser.add_argument(
        "--vault-path",
        default=str(settings.vault_path),
        help="Vault root path. Defaults to VAULT_PATH from settings.",
    )
    parser.add_argument(
        "--db-path",
        default=str(settings.index_db_path),
        help="SQLite index path. Defaults to INDEX_DB_PATH from settings.",
    )
    parser.add_argument(
        "--memory-id",
        action="append",
        dest="memory_ids",
        help="Optional memory id filter. Repeat for multiple ids.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform the move and index update. Without this flag, only a dry run is returned.",
    )
    return parser.parse_args()


def main() -> None:
    _, apply_memory_path_backfill = _load_runtime()
    args = parse_args()
    result = apply_memory_path_backfill(
        vault_path=Path(args.vault_path),
        db_path=Path(args.db_path),
        apply=args.apply,
        memory_ids=args.memory_ids,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

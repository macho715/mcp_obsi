from __future__ import annotations

import json
import tarfile
from datetime import UTC, datetime
from pathlib import Path


def clear_directory(path: Path) -> None:
    if not path.exists():
        return
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            child.rmdir()


def main() -> None:
    base = Path("/data")
    backup_dir = base / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    archive = backup_dir / f"drill-{stamp}.tar.gz"

    with tarfile.open(archive, "w:gz") as tf:
        for name in ["vault", "state"]:
            target = base / name
            if target.exists():
                tf.add(target, arcname=name)

    restore_root = Path("/tmp/restore-drill")
    clear_directory(restore_root)
    restore_root.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, "r:gz") as tf:
        try:
            tf.extractall(restore_root, filter="data")
        except TypeError:
            tf.extractall(restore_root)

    restored_files = sorted(str(path) for path in restore_root.rglob("*") if path.is_file())
    print(
        json.dumps(
            {
                "archive": str(archive),
                "restored_files": restored_files,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

"""Create AGENTS.md + KB routing folders under VAULT_PATH (default: ./vault).

Safe: only mkdir + optional stub files. Does not delete anything.

Usage (repo root):
  .venv\\Scripts\\python scripts/bootstrap_vault_layout.py
  .venv\\Scripts\\python scripts/bootstrap_vault_layout.py --vault D:\\path\\to\\vault
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--vault",
        type=Path,
        default=Path("vault"),
        help="Vault root (default: ./vault)",
    )
    args = p.parse_args()
    root: Path = args.vault.resolve()

    dirs = [
        "10_Daily",
        "20_AI_Memory",
        "90_System",
        "mcp_raw",
        "memory",
        "wiki/sources",
        "wiki/concepts",
        "wiki/entities",
        "wiki/analyses",
        "raw/articles",
        "raw/pdf",
        "raw/notes",
    ]
    for rel in dirs:
        (root / rel).mkdir(parents=True, exist_ok=True)

    index = root / "wiki" / "index.md"
    log = root / "wiki" / "log.md"
    if not index.exists():
        index.write_text(
            "# KB index\n\n"
            "Canonical hub for `vault/wiki/`. "
            "Update via KB skills or manual edits.\n",
            encoding="utf-8",
        )
    if not log.exists():
        log.write_text(
            "# Wiki change log\n\nEntries after ingest/lint when workflows update this file.\n",
            encoding="utf-8",
        )

    print(f"OK: vault layout under {root}")


if __name__ == "__main__":
    main()

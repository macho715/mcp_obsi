from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.local_wiki_everything import EverythingHttpError, search_everything

SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".log",
]
DEFAULT_OUTPUT_ROOT = Path("runtime/local-wiki-inventory")

HIGH_RISK_PATH_PARTS = {
    "\\windows\\",
    "\\program files\\",
    "\\program files (x86)\\",
    "\\appdata\\",
    "\\.git\\",
    "\\node_modules\\",
    "\\.venv\\",
    "\\dist\\",
    "\\build\\",
    "\\.cache\\",
}
HIGH_RISK_NAME_PARTS = {
    "password",
    "passwd",
    "secret",
    "token",
    "apikey",
    "api-key",
    "private-key",
}
SIZE_LIMITS = {
    ".log": 2 * 1024 * 1024,
    ".md": 5 * 1024 * 1024,
    ".txt": 5 * 1024 * 1024,
    ".csv": 5 * 1024 * 1024,
    ".json": 5 * 1024 * 1024,
    ".pdf": 20 * 1024 * 1024,
    ".docx": 20 * 1024 * 1024,
    ".xlsx": 20 * 1024 * 1024,
    ".xlsm": 20 * 1024 * 1024,
    ".doc": 0,
    ".xls": 0,
}


def build_extension_queries() -> list[str]:
    return [f"*{extension}" for extension in SUPPORTED_EXTENSIONS]


def classify_candidate(candidate: dict[str, Any]) -> dict[str, str]:
    path = str(candidate.get("path") or "")
    lowered_path = path.lower()
    extension = str(candidate.get("extension") or Path(path).suffix).lower()
    if any(part in lowered_path for part in HIGH_RISK_PATH_PARTS):
        return {"status": "excluded", "reason": "high-risk path"}
    if any(part in Path(path).name.lower() for part in HIGH_RISK_NAME_PARTS):
        return {"status": "excluded", "reason": "high-risk filename"}
    if extension not in SUPPORTED_EXTENSIONS:
        return {"status": "excluded", "reason": "unsupported extension"}

    limit = SIZE_LIMITS.get(extension, 0)
    if limit <= 0:
        return {"status": "excluded", "reason": "limited legacy format"}

    size = candidate.get("size")
    if isinstance(size, int) and size > limit:
        return {"status": "excluded", "reason": "file too large"}
    return {"status": "queued", "reason": "safe candidate"}


def write_inventory(
    payload: dict[str, Any],
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    timestamp: str | None = None,
) -> tuple[Path, Path]:
    stamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    runs = output_root / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    latest = output_root / "latest.json"
    run_path = runs / f"{stamp}.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    latest.write_text(text, encoding="utf-8")
    run_path.write_text(text, encoding="utf-8")
    return latest, run_path


def build_inventory(limit_per_extension: int, dry_run: bool) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for query in build_extension_queries():
        try:
            results = search_everything(query=query, limit=limit_per_extension)
        except EverythingHttpError as exc:
            errors.append({"query": query, "error": str(exc)})
            continue

        for result in results:
            candidates.append({**result, **classify_candidate(result)})

    return {
        "dry_run": dry_run,
        "candidate_count": len(candidates),
        "queued_count": sum(1 for item in candidates if item.get("status") == "queued"),
        "candidates": candidates,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a metadata-only local wiki inventory.")
    parser.add_argument("--limit-per-extension", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = build_inventory(
        limit_per_extension=args.limit_per_extension,
        dry_run=args.dry_run,
    )
    latest, run_path = write_inventory(payload)
    print(f"inventory_latest={latest}")
    print(f"inventory_run={run_path}")
    print(f"queued={payload['queued_count']} total={payload['candidate_count']}")
    if payload["errors"]:
        print("errors:")
        for error in payload["errors"]:
            print(f"- {error['query']}: {error['error']}")


if __name__ == "__main__":
    main()

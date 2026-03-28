from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

from app.config import settings
from app.models import MemoryCreate, RawConversationCreate
from app.services.memory_store import MemoryStore

DEFAULT_RAW_ID = "convo-railway-preview-seed"
DEFAULT_MEMORY_TITLE = "Railway Preview Decision"
DEFAULT_RAW_MARKER = "raw conversation body only"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed Railway-backed MCP storage with one raw and one memory note."
    )
    parser.add_argument("--raw-id", default=DEFAULT_RAW_ID)
    parser.add_argument("--memory-title", default=DEFAULT_MEMORY_TITLE)
    parser.add_argument("--project", default="preview")
    parser.add_argument("--created-by", default="railway-preview")
    parser.add_argument("--raw-marker", default=DEFAULT_RAW_MARKER)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = MemoryStore(settings.vault_path, settings.index_db_path, timezone=settings.timezone)
    occurred_at = datetime(2026, 3, 28, 12, 3, 19, tzinfo=UTC)

    raw_result = store.archive_raw_conversation(
        RawConversationCreate(
            mcp_id=args.raw_id,
            source="manual",
            created_by=args.created_by,
            created_at_utc=occurred_at,
            conversation_date=occurred_at.date(),
            project=args.project,
            tags=[args.project, "raw"],
            body_markdown=(
                "## User\n"
                f"Railway {args.project} seed request.\n\n"
                "## Assistant\n"
                f"This line exists only for raw archive exclusion checks: {args.raw_marker}"
            ),
        )
    )

    existing = store.search(query=args.memory_title, limit=10)["results"]
    memory = next((item for item in existing if item["title"] == args.memory_title), None)
    if memory is None:
        saved = store.save(
            MemoryCreate(
                memory_type="decision",
                title=args.memory_title,
                content=f"E2E hybrid decision stored in Railway {args.project}.",
                source="manual",
                created_by=args.created_by,
                project=args.project,
                tags=[args.project, "railway", "decision"],
                append_daily=False,
                occurred_at=occurred_at,
            )
        )
    else:
        saved = {"id": memory["id"], "path": memory["path"], "status": "existing"}

    print(
        json.dumps(
            {
                "raw": raw_result,
                "memory": saved,
                "queries": {
                    "normalized_hit": args.memory_title,
                    "raw_exclusion": args.raw_marker,
                },
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

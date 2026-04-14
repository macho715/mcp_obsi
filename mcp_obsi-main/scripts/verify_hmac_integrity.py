from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

import yaml

from app.config import settings
from app.services.markdown_store import MarkdownStore
from app.utils.integrity import verify_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify saved markdown documents against mcp_sig.")
    parser.add_argument("--memory-id", required=False)
    parser.add_argument("--raw-id", required=False)
    parser.add_argument("--raw-relative-path", required=False)
    parser.add_argument("--path", required=False)
    parser.add_argument("--vault-path", default=os.getenv("VAULT_PATH") or str(settings.vault_path))
    parser.add_argument(
        "--index-db-path",
        default=os.getenv("INDEX_DB_PATH") or str(settings.index_db_path),
    )
    parser.add_argument(
        "--secret",
        default=os.getenv("MCP_HMAC_SECRET") or settings.mcp_hmac_secret,
        required=False,
    )
    parser.add_argument("--allow-unsigned-legacy", action="store_true")
    return parser.parse_args()


def read_raw_document(vault_root: Path, rel_path: str) -> dict:
    text = (vault_root / rel_path).read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"raw note at {rel_path} is missing frontmatter")
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError(f"raw note at {rel_path} has malformed frontmatter")
    frontmatter = yaml.safe_load(parts[0][4:]) or {}
    frontmatter["body_markdown"] = parts[1].lstrip("\n").rstrip("\n")
    return frontmatter


def memory_result(vault_root: Path, db_path: Path, memory_id: str, secret: str) -> dict:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT path FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if row is None:
        raise ValueError(f"memory id not found: {memory_id}")
    rel_path = row[0]
    document = MarkdownStore(vault_root).read_memory_document(rel_path)
    if document is None:
        raise ValueError(f"memory note not found: {rel_path}")
    signed_payload = {key: value for key, value in document.items() if key != "mcp_sig"}
    return {
        "kind": "memory",
        "id": memory_id,
        "path": rel_path,
        "has_signature": bool(document.get("mcp_sig")),
        "verified": verify_payload(secret, signed_payload, document.get("mcp_sig")),
    }


def verify_document(
    document: dict,
    *,
    kind: str,
    path: str,
    secret: str,
    allow_unsigned_legacy: bool,
    identifier: str | None = None,
) -> dict:
    has_signature = bool(document.get("mcp_sig"))
    signed_payload = {key: value for key, value in document.items() if key != "mcp_sig"}
    verified = (
        verify_payload(secret, signed_payload, document.get("mcp_sig")) if has_signature else False
    )
    if not has_signature and allow_unsigned_legacy:
        verified = True

    result = {
        "kind": kind,
        "path": path,
        "has_signature": has_signature,
        "verified": verified,
    }
    if identifier is not None:
        result["id"] = identifier
    return result


def raw_result(vault_root: Path, rel_path: str, secret: str, allow_unsigned_legacy: bool) -> dict:
    document = read_raw_document(vault_root, rel_path)
    return verify_document(
        document,
        kind="raw",
        path=rel_path,
        secret=secret,
        allow_unsigned_legacy=allow_unsigned_legacy,
    )


def raw_id_result(vault_root: Path, raw_id: str, secret: str, allow_unsigned_legacy: bool) -> dict:
    matches = sorted(vault_root.glob(f"mcp_raw/*/*/{raw_id}.md"))
    if not matches:
        raise ValueError(f"raw id not found: {raw_id}")
    rel_path = matches[0].relative_to(vault_root).as_posix()
    document = read_raw_document(vault_root, rel_path)
    return verify_document(
        document,
        kind="raw",
        path=rel_path,
        secret=secret,
        allow_unsigned_legacy=allow_unsigned_legacy,
        identifier=raw_id,
    )


def path_result(vault_root: Path, rel_path: str, secret: str, allow_unsigned_legacy: bool) -> dict:
    full_path = vault_root / rel_path
    if not full_path.exists():
        raise ValueError(f"path not found: {rel_path}")
    if rel_path.startswith("mcp_raw/"):
        document = read_raw_document(vault_root, rel_path)
        return verify_document(
            document,
            kind="raw",
            path=rel_path,
            secret=secret,
            allow_unsigned_legacy=allow_unsigned_legacy,
        )
    document = MarkdownStore(vault_root).read_memory_document(rel_path)
    if document is None:
        raise ValueError(f"memory note not found: {rel_path}")
    return verify_document(
        document,
        kind="memory",
        path=rel_path,
        secret=secret,
        allow_unsigned_legacy=allow_unsigned_legacy,
    )


def main() -> None:
    args = parse_args()
    if not args.secret:
        raise SystemExit("--secret or MCP_HMAC_SECRET is required")
    if not args.memory_id and not args.raw_relative_path and not args.raw_id and not args.path:
        raise SystemExit("--memory-id, --raw-id, --raw-relative-path, or --path is required")

    vault_root = Path(args.vault_path)
    db_path = Path(args.index_db_path)
    results = []
    if args.memory_id:
        result = memory_result(vault_root, db_path, args.memory_id, args.secret)
        if not result["has_signature"] and args.allow_unsigned_legacy:
            result["verified"] = True
        results.append(result)
    if args.raw_id:
        results.append(
            raw_id_result(vault_root, args.raw_id, args.secret, args.allow_unsigned_legacy)
        )
    if args.raw_relative_path:
        results.append(
            raw_result(vault_root, args.raw_relative_path, args.secret, args.allow_unsigned_legacy)
        )
    if args.path:
        results.append(path_result(vault_root, args.path, args.secret, args.allow_unsigned_legacy))

    print(json.dumps({"results": results}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        raise

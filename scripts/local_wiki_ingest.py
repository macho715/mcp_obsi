from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.sanitize import contains_sensitive_pattern

DEFAULT_INVENTORY_PATH = Path("runtime/local-wiki-inventory/latest.json")
DEFAULT_VAULT_ROOT = Path("vault")
COPILOT_EXTENSION_PRIORITY = {
    ".md": 0,
    ".txt": 0,
    ".csv": 1,
    ".json": 1,
    ".log": 1,
    ".docx": 2,
    ".xlsx": 3,
    ".xlsm": 3,
    ".pdf": 4,
}

ExtractDocument = Callable[[Path], dict[str, Any]]
WriteWikiNote = Callable[..., Path]
CopilotNormalize = Callable[[Path, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class IngestResult:
    path: str
    status: str
    reason: str
    note_path: str | None = None


def load_queued_candidates(
    inventory_path: str | Path = DEFAULT_INVENTORY_PATH,
) -> list[dict[str, Any]]:
    path = Path(inventory_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("inventory candidates must be a list")
    return [candidate for candidate in candidates if candidate.get("status") == "queued"]


def normalize_extraction(
    source_path: str | Path, text: str, extraction_status: str
) -> dict[str, Any]:
    normalized_text = re.sub(r"\s+", " ", text).strip()
    summary = normalized_text[:300]
    title = Path(source_path).stem
    return {
        "title": title,
        "summary": summary,
        "key_facts": [],
        "extracted_structure": [],
        "topics": ["local-file"],
        "entities": [],
        "projects": [],
        "extraction_status": extraction_status,
    }


def local_wiki_has_credential_pattern(text: str) -> bool:
    """Credential hard-stop for local wiki ingest without blocking ordinary PII."""
    return contains_sensitive_pattern(text)


def order_candidates_for_copilot(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda candidate: (
            _copilot_path_penalty(candidate),
            COPILOT_EXTENSION_PRIORITY.get(
                Path(str(candidate.get("path") or "")).suffix.lower(),
                99,
            ),
            str(candidate.get("path") or "").lower(),
        ),
    )


def _copilot_path_penalty(candidate: dict[str, Any]) -> int:
    normalized = str(candidate.get("path") or "").replace("/", "\\").lower()
    low_value_markers = ("\\.codex\\", "\\.cursor\\", "\\$recycle.bin\\")
    return 1 if any(marker in normalized for marker in low_value_markers) else 0


def ingest_candidates(
    candidates: list[dict[str, Any]],
    *,
    vault_root: str | Path = DEFAULT_VAULT_ROOT,
    limit: int = 1,
    dry_run: bool = False,
    normalizer: str = "deterministic",
    extract_document: ExtractDocument | None = None,
    copilot_normalize: CopilotNormalize | None = None,
    write_wiki_note: WriteWikiNote | None = None,
) -> list[IngestResult]:
    if limit < 1:
        return []

    extractor = extract_document or _load_extract_document()
    writer = write_wiki_note
    results: list[IngestResult] = []
    deferred_fallbacks: list[IngestResult] = []
    handled = 0
    candidate_queue = candidates
    if normalizer.strip().lower() == "copilot":
        candidate_queue = order_candidates_for_copilot(candidates)

    for candidate in candidate_queue:
        if handled >= limit:
            break
        if candidate.get("status") != "queued":
            continue

        raw_path = candidate.get("path")
        if not raw_path:
            results.append(IngestResult(path="", status="skipped", reason="missing path"))
            continue

        source_path = Path(raw_path)
        if not source_path.exists():
            results.append(
                IngestResult(path=str(source_path), status="skipped", reason="missing file")
            )
            continue

        extraction = extractor(source_path)
        text = str(extraction.get("text", ""))
        extraction_status = str(extraction.get("status", "ok"))
        if local_wiki_has_credential_pattern(text):
            results.append(
                IngestResult(path=str(source_path), status="skipped", reason="credential pattern")
            )
            continue

        normalized, fallback_reason = _normalize_candidate(
            source_path,
            extraction,
            extraction_status,
            normalizer=normalizer,
            copilot_normalize=copilot_normalize,
        )

        if dry_run:
            reason = "would write wiki note"
            if fallback_reason:
                reason = f"{reason}; copilot fallback: {fallback_reason}"
                if normalizer.strip().lower() == "copilot":
                    deferred_fallbacks.append(
                        IngestResult(path=str(source_path), status="dry-run", reason=reason)
                    )
                    continue
            elif normalizer.strip().lower() == "copilot":
                reason = f"{reason}; normalizer=copilot"
            handled += 1
            results.append(IngestResult(path=str(source_path), status="dry-run", reason=reason))
            continue

        if writer is None:
            writer = _load_write_wiki_note()
        handled += 1
        note_path = writer(
            vault_root=Path(vault_root),
            title=normalized["title"],
            source_path=str(source_path.resolve()),
            source_ext=source_path.suffix.lower(),
            source_size=int(candidate.get("size") or source_path.stat().st_size),
            source_modified_at=str(
                candidate.get("date_modified")
                or candidate.get("modified_at")
                or candidate.get("modifiedAt")
                or ""
            ),
            summary=normalized["summary"],
            key_facts=normalized["key_facts"],
            extracted_structure=normalized["extracted_structure"],
            topics=normalized["topics"],
            entities=normalized["entities"],
            projects=normalized["projects"],
            extraction_status=normalized["extraction_status"],
        )
        reason = "wiki note written"
        if fallback_reason:
            reason = f"{reason}; copilot fallback: {fallback_reason}"
        results.append(
            IngestResult(
                path=str(source_path),
                status="written",
                reason=reason,
                note_path=str(note_path),
            )
        )

    return results or deferred_fallbacks[:limit]


def _load_extract_document() -> ExtractDocument:
    from scripts.local_wiki_extract import extract_document

    return extract_document


def _load_write_wiki_note() -> WriteWikiNote:
    from scripts.local_wiki_writer import write_wiki_note

    return write_wiki_note


def _normalize_candidate(
    source_path: Path,
    extraction: dict[str, Any],
    extraction_status: str,
    *,
    normalizer: str,
    copilot_normalize: CopilotNormalize | None,
) -> tuple[dict[str, Any], str | None]:
    selected = normalizer.strip().lower()
    text = str(extraction.get("text", ""))
    if selected == "deterministic":
        return normalize_extraction(source_path, text, extraction_status), None
    if selected != "copilot":
        raise ValueError("normalizer must be deterministic or copilot")

    runner = copilot_normalize or _load_copilot_normalize()
    try:
        normalized = runner(source_path, extraction)
    except Exception as exc:
        return normalize_extraction(source_path, text, extraction_status), str(exc)

    normalized.setdefault("extraction_status", extraction_status)
    normalized.setdefault("key_facts", [])
    normalized.setdefault("extracted_structure", [])
    normalized.setdefault("topics", ["local-file"])
    normalized.setdefault("entities", [])
    normalized.setdefault("projects", [])
    return normalized, None


def _load_copilot_normalize() -> CopilotNormalize:
    from scripts.local_wiki_copilot import build_copilot_packet, normalize_with_copilot_proxy

    def run(source_path: Path, extraction: dict[str, Any]) -> dict[str, Any]:
        packet = build_copilot_packet(
            source_path=source_path,
            source_ext=source_path.suffix.lower(),
            extraction=extraction,
        )
        return normalize_with_copilot_proxy(packet)

    return run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest queued local wiki inventory candidates.")
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY_PATH)
    parser.add_argument("--vault-root", type=Path, default=DEFAULT_VAULT_ROOT)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--normalizer",
        choices=("deterministic", "copilot"),
        default="deterministic",
    )
    args = parser.parse_args(argv)

    candidates = load_queued_candidates(args.inventory)
    results = ingest_candidates(
        candidates,
        vault_root=args.vault_root,
        limit=args.limit,
        dry_run=args.dry_run,
        normalizer=args.normalizer,
    )
    print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

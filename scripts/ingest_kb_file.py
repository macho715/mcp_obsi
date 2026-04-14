"""
Ingest one file into vault/wiki (obsidian-ingest skill), using in-process stores.

Usage (repo root):
  .venv\\Scripts\\python scripts/ingest_kb_file.py --file "C:\\path\\to\\doc.md"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import textwrap
from datetime import date, datetime

sys.path.insert(0, ".")

from app.config import settings
from app.models import MemoryCreate, RawConversationCreate
from app.services.memory_store import MemoryStore
from app.services.raw_archive_store import RawArchiveStore
from app.services.schema_validator import SchemaValidator
from scripts.ollama_kb import MODELS, generate, health_check, normalize_ascii_slug


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="KB ingest one markdown/article file.")
    p.add_argument("--file", type=pathlib.Path, required=True, help="Source file path")
    p.add_argument(
        "--source-label",
        default="obsidian-ingest",
        help="archive_raw source segment",
    )
    return p.parse_args()


def banner(s: str) -> None:
    print(f"\n{'─' * 60}\n  {s}\n{'─' * 60}")


def main() -> None:
    args = parse_args()
    src = args.file.expanduser().resolve()
    if not src.is_file():
        print(f"FAIL: not a file: {src}", file=sys.stderr)
        sys.exit(1)

    text_body = src.read_text(encoding="utf-8")
    slug_hint = normalize_ascii_slug(src.stem, fallback="ingested-doc")

    banner("Step 0 — Ollama")
    if not health_check():
        print("FAIL: Ollama not reachable", file=sys.stderr)
        sys.exit(1)
    print("OK: Ollama")

    today = date.today().isoformat()
    ingest_suffix = datetime.now().strftime("%H%M%S")
    # Raw archive schema: mcp_id must match ^convo-[A-Za-z0-9._:-]+$
    ascii_slug = "".join(c for c in slug_hint if c.isascii() and (c.isalnum() or c in "-_"))
    ascii_slug = ascii_slug.strip("-") or ""
    if not ascii_slug or set(ascii_slug) <= {"-"}:
        ascii_slug = hashlib.sha256(slug_hint.encode("utf-8")).hexdigest()[:12]
    mcp_id = f"convo-{ascii_slug}-{today}-{ingest_suffix}"

    VAULT = pathlib.Path(settings.vault_path).resolve()
    DB_PATH = pathlib.Path(settings.index_db_path).resolve()
    WIKI_ROOT = VAULT / "wiki"

    validator = SchemaValidator()
    raw_store = RawArchiveStore(vault_path=VAULT, validator=validator)
    mem_store = MemoryStore(vault_path=VAULT, index_db_path=DB_PATH, timezone=settings.timezone)

    banner("Step 1a — vault/raw/articles immutable copy")
    raw_articles = VAULT / "raw" / "articles" / f"{slug_hint}-{ingest_suffix}.md"
    raw_articles.parent.mkdir(parents=True, exist_ok=True)
    raw_articles.write_text(
        f"---\nslug: {slug_hint}\ndate: {today}\nsource: obsidian-ingest\n"
        f"original_file: {src.name}\n---\n\n{text_body}",
        encoding="utf-8",
    )
    print(f"OK: {raw_articles}")

    banner("Step 1b — archive_raw → mcp_raw/")
    raw_payload = RawConversationCreate(
        mcp_id=mcp_id,
        source=args.source_label,
        body_markdown=text_body,
        project="hvdc",
        tags=["kb", "ontology", "hvdc", "ingest"],
        created_at_utc=datetime.now().astimezone(),
    )
    raw_result = raw_store.save(raw_payload)
    print(f"OK: {raw_result['path']}")

    banner("Step 2 — Classify (Ollama)")
    classify_prompt = [
        {
            "role": "system",
            "content": (
                "Classify this document into exactly one: sources, concepts, entities, analyses. "
                "Also: title (Korean OK), slug (lowercase-hyphen ASCII), "
                "tags (3-6 strings), summary (one line Korean). "
                "Reply JSON only: "
                '{"category":"..","title":"..","slug":"..","tags":[..],"summary":".."}'
            ),
        },
        {"role": "user", "content": text_body[:12000]},
    ]
    print("  Calling Ollama classify...")
    raw_class = generate(messages=classify_prompt, model=MODELS["primary"])
    try:
        clean = (
            raw_class.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        meta = json.loads(clean)
    except json.JSONDecodeError:
        meta = {
            "category": "concepts",
            "title": "HVDC 물류 도메인 지식 온톨로지 작성 가이드",
            "slug": slug_hint or "hvdc-ontology-guide-v2",
            "tags": ["hvdc", "ontology", "logistics", "flow-code"],
            "summary": "HVDC shipment 중심 온톨로지·Flow Code v3.5·도메인 모듈 가이드.",
        }
    if not isinstance(meta, dict):
        meta = {}
    cat = meta.get("category", "concepts")
    if cat not in ("sources", "concepts", "entities", "analyses"):
        cat = "concepts"
    meta["category"] = cat
    meta["title"] = str(meta.get("title") or src.stem)
    meta["summary"] = str(meta.get("summary") or f"{meta['title']} 요약")
    raw_tags = meta.get("tags", [])
    if not isinstance(raw_tags, list):
        raw_tags = []
    meta["tags"] = [str(tag).strip() for tag in raw_tags if str(tag).strip()] or [
        "kb",
        cat,
        "ingest",
    ]
    slug = normalize_ascii_slug(str(meta.get("slug") or slug_hint), fallback=slug_hint)
    print(f"OK: category={cat} slug={slug}")

    banner("Step 3 — Extract body (Ollama)")
    extract_prompt = [
        {
            "role": "system",
            "content": (
                "You compile structured KB notes from source text. "
                "Output Obsidian markdown (Korean). "
                "Sections: ## 개요, ## 핵심 원칙, ## 구조·모듈, "
                "## 식별자·Flow Code, ## 검증·게이트. "
                "Do not invent facts absent from the source. Max ~500 words."
            ),
        },
        {"role": "user", "content": text_body},
    ]
    print("  Calling Ollama extract...")
    extracted = generate(messages=extract_prompt, model=MODELS["primary"])
    print(f"OK: {len(extracted)} chars")

    banner("Step 4 — Write wiki note")
    wiki_path = WIKI_ROOT / cat / f"{slug}.md"
    wiki_path.parent.mkdir(parents=True, exist_ok=True)
    if wiki_path.exists():
        print(f"FAIL: canonical wiki note already exists: {wiki_path}", file=sys.stderr)
        sys.exit(1)
    title_esc = str(meta["title"]).replace('"', '\\"')
    fm = (
        f"---\n"
        f"note_kind: wiki\n"
        f"category: {cat}\n"
        f'title: "{title_esc}"\n'
        f"slug: {slug}\n"
        f"created: {today}\n"
        f"tags: {json.dumps(meta.get('tags', []), ensure_ascii=False)}\n"
        f"source_raw_ref: {mcp_id}\n"
        f"---\n\n"
    )
    wiki_path.write_text(fm + extracted, encoding="utf-8")
    print(f"OK: {wiki_path}")

    banner("Step 5 — save_memory pointer")
    mem_payload = MemoryCreate(
        memory_type="project_fact",
        title=f"KB: {meta['title']}",
        content=f"{meta.get('summary', '')}\n\nSee [[wiki/{cat}/{slug}]] for full details.",
        source=args.source_label,
        roles=["fact"],
        topics=list(meta.get("tags", [])),
        entities=[],
        projects=["hvdc", "mcp_obsidian"],
        tags=["kb", "wiki", cat, "hvdc"],
        raw_refs=[mcp_id],
        confidence=0.88,
        language="ko",
    )
    mem_result = mem_store.save(mem_payload)
    mem_id = mem_result.get("id", "?")
    print(f"OK: memory {mem_id} → {mem_result.get('path')}")

    banner("Step 6 — wiki/log.md")
    log_path = WIKI_ROOT / "log.md"
    row = f"| {today} | ingest | {meta['title']} | {cat}/{slug}.md | {mcp_id} | {mem_id} |\n"
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + row, encoding="utf-8")
    else:
        log_path.write_text(
            "| date | action | title | wiki_path | raw_ref | mem_id |\n"
            "|---|---|---|---|---|---|\n" + row,
            encoding="utf-8",
        )
    print(f"OK: {log_path}")

    banner("Step 7 — wiki/index.md Recent Notes")
    idx = WIKI_ROOT / "index.md"
    link_line = f"- [[{cat}/{slug}]] — {meta['title']}\n"
    if idx.exists():
        cur = idx.read_text(encoding="utf-8")
    else:
        cur = "# KB index\n\n## Recent Notes\n\n"
    if "## Recent Notes" in cur:
        parts = cur.split("## Recent Notes", 1)
        tail = parts[1]
        # insert after header line
        lines_tail = tail.lstrip("\n")
        cur = (
            parts[0]
            + "## Recent Notes\n\n"
            + link_line
            + ("\n" if not lines_tail.startswith("\n") else "")
            + lines_tail
        )
    else:
        cur = cur.rstrip() + "\n\n## Recent Notes\n\n" + link_line
    idx.write_text(cur, encoding="utf-8")
    print(f"OK: {idx}")

    banner("COMPLETE")
    print(
        textwrap.dedent(f"""
        raw articles : {raw_articles}
        mcp_raw      : {raw_result["path"]}
        wiki         : {wiki_path}
        memory       : {mem_id}
        Obsidian     : VAULT_PATH={VAULT}
        Sync         : open this folder as vault + Obsidian Sync (if configured)
        """)
    )


if __name__ == "__main__":
    main()

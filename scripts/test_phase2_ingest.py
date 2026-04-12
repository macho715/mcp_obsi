"""
Phase 2: obsidian-ingest end-to-end test script.

Run from repo root:
    .venv\\Scripts\\python scripts/test_phase2_ingest.py

Flow:
  1. Ollama health check
  2. archive_raw  → mcp_raw/
  3. Classify + extract with Ollama (gemma4:e4b)
  4. Write wiki note → vault/wiki/<category>/<slug>.md
  5. save_memory pointer (via MemoryStore)
  6. Update vault/wiki/log.md
  7. Report
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import textwrap
from datetime import date, datetime

sys.path.insert(0, ".")

# ── Imports ──────────────────────────────────────────────────────────────────
from app.config import settings
from app.models import MemoryCreate, RawConversationCreate
from app.services.index_store import IndexStore
from app.services.memory_store import MemoryStore
from app.services.raw_archive_store import RawArchiveStore
from app.services.schema_validator import SchemaValidator
from scripts.ollama_kb import MODELS, generate, health_check, normalize_ascii_slug

# ── Sample input ──────────────────────────────────────────────────────────────
SAMPLE_TITLE = "Gemma 4 모델 아키텍처 개요"
SAMPLE_CONTENT = textwrap.dedent("""\
    Gemma 4는 Google DeepMind가 2025년 발표한 경량 멀티모달 LLM 시리즈다.
    E2B(2B), E4B(4B) 두 가지 edge 변형이 있으며 각각 7.2GB, 9.6GB 크기다.
    두 모델 모두 128K context window를 지원하며 Ollama를 통해 로컬 추론이 가능하다.
    아키텍처는 MoE(Mixture of Experts) 대신 dense transformer 구조를 사용하며
    int4 양자화로 소비자급 GPU에서 실행된다. 주요 용도: 코드 보조, 문서 요약,
    지식 추출 (obsidian-ingest, obsidian-query 스킬에서 기본 모델로 사용).
""")
RUN_SUFFIX = datetime.now().strftime("%H%M%S")
MCP_ID = f"convo-kb-ingest-test-{date.today().isoformat()}-{RUN_SUFFIX}"
SOURCE = "cursor"

# ── Store setup ───────────────────────────────────────────────────────────────
VAULT = pathlib.Path(settings.vault_path)
DB_PATH = pathlib.Path(settings.index_db_path)
WIKI_ROOT = VAULT / "wiki"

validator = SchemaValidator()
raw_store = RawArchiveStore(vault_path=VAULT, validator=validator)
index_store = IndexStore(db_path=DB_PATH)
mem_store = MemoryStore(vault_path=VAULT, index_db_path=DB_PATH)


def banner(step: str) -> None:
    print(f"\n{'─' * 60}\n  {step}\n{'─' * 60}")


# ── Step 1: Ollama health ─────────────────────────────────────────────────────
banner("Step 1 — Ollama health check")
if not health_check():
    print("FAIL: Ollama not reachable at localhost:11434")
    sys.exit(1)
print("OK: Ollama reachable")

# ── Step 2: archive_raw ───────────────────────────────────────────────────────
banner("Step 2 — archive_raw → mcp_raw/")
raw_payload = RawConversationCreate(
    mcp_id=MCP_ID,
    source=SOURCE,
    body_markdown=f"# {SAMPLE_TITLE}\n\n{SAMPLE_CONTENT}",
    project="mcp_obsidian",
    tags=["kb", "gemma", "test"],
    created_at_utc=datetime.now().astimezone(),
)
raw_result = raw_store.save(raw_payload)
print(f"OK: raw archived → {raw_result['path']}")

# ── Step 2b: Copy to vault/raw/ (immutable source layer) ─────────────────────
banner("Step 2b — vault/raw/ immutable copy")
raw_source_path = VAULT / "raw" / "articles" / f"{MCP_ID}.md"
raw_source_path.parent.mkdir(parents=True, exist_ok=True)
raw_source_path.write_text(
    f"---\nslug: {MCP_ID}\ndate: {date.today().isoformat()}\nsource: obsidian-ingest\n---\n\n"
    f"# {SAMPLE_TITLE}\n\n{SAMPLE_CONTENT}",
    encoding="utf-8",
)
print(f"OK: raw copy → {raw_source_path}")

# ── Step 3: Classify with Ollama ──────────────────────────────────────────────
banner("Step 3 — Classify with Ollama (gemma4:e4b)")
classify_prompt = [
    {
        "role": "system",
        "content": (
            "Classify this document into exactly one of these KB categories: "
            "sources, concepts, entities, analyses. "
            "Also extract: title (Korean OK), slug (lowercase-hyphen, ASCII), "
            "tags (3-5 keywords, array), one_line_summary (Korean OK). "
            'Reply JSON only: {"category":"..","title":"..","slug":"..","tags":[..],"summary":".."}'
        ),
    },
    {"role": "user", "content": SAMPLE_CONTENT},
]
print("  Calling Ollama... (may take 30-120s)")
raw_class = generate(messages=classify_prompt, model=MODELS["primary"])
print(f"  Raw response: {raw_class[:200]}")

try:
    clean = (
        raw_class.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    )
    meta = json.loads(clean)
except json.JSONDecodeError:
    print("  WARN: JSON parse failed, using defaults")
    meta = {
        "category": "concepts",
        "title": SAMPLE_TITLE,
        "slug": "gemma4-architecture",
        "tags": ["gemma4", "llm", "ollama", "edge-model"],
        "summary": "Gemma 4 E2B/E4B 아키텍처 및 Ollama 로컬 실행 요약.",
    }
if not isinstance(meta, dict):
    meta = {}
meta["title"] = str(meta.get("title") or SAMPLE_TITLE)
meta["summary"] = str(meta.get("summary") or f"{meta['title']} 요약")
raw_tags = meta.get("tags", [])
if not isinstance(raw_tags, list):
    raw_tags = []
meta["tags"] = [str(tag).strip() for tag in raw_tags if str(tag).strip()] or [
    "gemma4",
    "llm",
    "ollama",
]
print(
    f"  category={meta.get('category', 'concepts')} slug={meta.get('slug', 'gemma4-architecture')}"
)

# ── Step 4: Extract structured content ───────────────────────────────────────
banner("Step 4 — Extract knowledge structure with Ollama")
extract_prompt = [
    {
        "role": "system",
        "content": (
            "Extract key knowledge from this document. "
            "Write a concise Obsidian-friendly Markdown body (Korean OK). "
            "Use ## sections: 개요, 핵심 사실, 관련 항목. "
            "Keep it under 400 words."
        ),
    },
    {"role": "user", "content": SAMPLE_CONTENT},
]
print("  Calling Ollama for extraction...")
extracted_body = generate(messages=extract_prompt, model=MODELS["primary"])
print(f"  Extracted {len(extracted_body)} chars")

# ── Step 5: Write wiki note ───────────────────────────────────────────────────
banner("Step 5 — Write vault/wiki/<category>/<slug>.md")
today_str = date.today().isoformat()
category = meta.get("category", "concepts")
if category not in ("sources", "concepts", "entities", "analyses"):
    category = "concepts"
slug = normalize_ascii_slug(
    str(meta.get("slug") or "gemma4-architecture"), fallback="gemma4-architecture"
)
wiki_note_path = WIKI_ROOT / category / f"{slug}.md"
wiki_note_path.parent.mkdir(parents=True, exist_ok=True)
if wiki_note_path.exists():
    print(f"FAIL: canonical wiki note already exists: {wiki_note_path}")
    sys.exit(1)
title_esc = str(meta["title"]).replace('"', '\\"').replace("\n", " ").replace("\r", " ")

frontmatter = (
    f"---\n"
    f"note_kind: wiki\n"
    f"category: {category}\n"
    f'title: "{title_esc}"\n'
    f"slug: {slug}\n"
    f"created: {today_str}\n"
    f"tags: {json.dumps(meta['tags'], ensure_ascii=False)}\n"
    f"source_raw_ref: {MCP_ID}\n"
    f"---\n\n"
)
wiki_note_path.write_text(frontmatter + extracted_body, encoding="utf-8")
print(f"OK: wiki note written → {wiki_note_path}")

# ── Step 5b: Patch cross-links in related entity/concept notes ────────────────
banner("Step 5b — Cross-link patching")
if os.getenv("KB_PATCH_RELATED_NOTES") == "1":
    new_link = f"[[wiki/{category}/{slug}]]"
    patched = []
    for rel_dir in ("entities", "concepts"):
        rel_root = WIKI_ROOT / rel_dir
        if not rel_root.exists():
            continue
        for rel_path in rel_root.glob("*.md"):
            rel_text = rel_path.read_text(encoding="utf-8")
            if rel_path.stem in extracted_body and new_link not in rel_text:
                rel_path.write_text(
                    rel_text + f"\n\n## Related\n\n- {new_link}\n", encoding="utf-8"
                )
                patched.append(rel_path.name)
    if patched:
        print(f"OK: cross-links added to: {', '.join(patched)}")
    else:
        print("  (no existing entity/concept notes matched)")
else:
    print("  disabled by default; set KB_PATCH_RELATED_NOTES=1 to enable")

# ── Step 6: save_memory pointer ───────────────────────────────────────────────
banner("Step 6 — save_memory pointer")
mem_payload = MemoryCreate(
    memory_type="project_fact",
    title=f"KB: {meta['title']}",
    content=f"{meta['summary']}\n\nSee [[wiki/{category}/{slug}]] for full details.",
    source=SOURCE,
    roles=["fact"],
    topics=meta["tags"],
    entities=[],
    projects=["mcp_obsidian"],
    tags=["kb", "wiki", category],
    raw_refs=[MCP_ID],
    confidence=0.85,
    language="ko",
)
mem_result = mem_store.save(mem_payload)
mem_id = mem_result.get("id", "?")
mem_path = mem_result.get("path", "?")
print(f"OK: save_memory → id={mem_id}  path={mem_path}")

# ── Step 7: Update vault/wiki/log.md ─────────────────────────────────────────
banner("Step 7 — Update vault/wiki/log.md")
log_path = WIKI_ROOT / "log.md"
log_row = (
    f"| {today_str} | ingest | {meta['title']} | {category}/{slug}.md | {MCP_ID} | {mem_id} |\n"
)
if log_path.exists():
    log_path.write_text(
        log_path.read_text(encoding="utf-8") + log_row,
        encoding="utf-8",
    )
else:
    header = "| date | action | title | wiki_path | raw_ref | mem_id |\n|---|---|---|---|---|---|\n"
    log_path.write_text(header + log_row, encoding="utf-8")
print(f"OK: log updated → {log_path}")

# ── Final report ──────────────────────────────────────────────────────────────
banner("Phase 2 COMPLETE")
print(f"""
  raw archived  : vault/mcp_raw/{SOURCE}/{date.today().isoformat()}/{MCP_ID}.md
  wiki note     : {wiki_note_path}
  memory id     : {mem_id}
  memory path   : {mem_path}
  log updated   : vault/wiki/log.md
""")

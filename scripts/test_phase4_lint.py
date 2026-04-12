"""
Phase 4: obsidian-lint end-to-end test script.

Run from repo root:
    .venv\\Scripts\\python scripts/test_phase4_lint.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import date

sys.path.insert(0, ".")

from app.config import settings
from app.models import MemoryCreate
from app.services.memory_store import MemoryStore
from scripts.ollama_kb import MODELS, generate, health_check

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
VAULT_ROOT = pathlib.Path(settings.vault_path).resolve()
VAULT_WIKI = VAULT_ROOT / "wiki"
RUNTIME_PATCHES = REPO_ROOT / "runtime" / "patches"
REQUIRED_FIELDS = {"note_kind", "title", "created", "tags"}
TODAY = date.today().isoformat()


def banner(step: str) -> None:
    print(f"\n{'─' * 60}\n  {step}\n{'─' * 60}")


def normalize_wikilink_target(link: str) -> str:
    return link.split("|", 1)[0].split("#", 1)[0].strip().removesuffix(".md")


def resolve_wikilink_path(target: str) -> pathlib.Path | None:
    if not target:
        return None
    if target.startswith(("memory/", "10_Daily/", "mcp_raw/")):
        return None

    pure_target = pathlib.PurePosixPath(target.removeprefix("wiki/"))
    direct_candidate = VAULT_WIKI.joinpath(*pure_target.parts).with_suffix(".md")
    if direct_candidate.exists():
        return direct_candidate

    if len(pure_target.parts) == 1:
        matches = sorted(VAULT_WIKI.rglob(f"{pure_target.name}.md"))
        if matches:
            return matches[0]

    return None


# ── Step 1: Collect notes ─────────────────────────────────────────────────────
banner("Step 1 — Collect wiki notes")
if not VAULT_WIKI.exists():
    print("FAIL: vault/wiki/ does not exist")
    sys.exit(1)

notes = []
for md in sorted(VAULT_WIKI.rglob("*.md")):
    if md.name in ("index.md", "log.md"):
        continue
    notes.append({"path": md, "text": md.read_text(encoding="utf-8")})
print(f"  Notes found: {len(notes)}")
if not notes:
    print("STOP: vault/wiki/ is empty. Run obsidian-ingest first.")
    sys.exit(0)

# ── Step 2: Deterministic checks ─────────────────────────────────────────────
banner("Step 2 — Deterministic checks")
findings = []

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)

for note in notes:
    text = note["text"]
    path = note["path"]

    # Missing frontmatter
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        findings.append({"path": str(path), "issue": "missing_frontmatter", "auto_fix": False})
        continue

    fm_text = fm_match.group(1)
    # Missing required fields
    for field in REQUIRED_FIELDS:
        if not re.search(rf"^{field}\s*:", fm_text, re.MULTILINE):
            findings.append(
                {
                    "path": str(path),
                    "issue": f"missing_field:{field}",
                    "auto_fix": False,
                }
            )

    # tags not array
    tags_match = re.search(r"^tags\s*:\s*(.+)$", fm_text, re.MULTILINE)
    if tags_match:
        val = tags_match.group(1).strip()
        if not val.startswith("[") and not val.startswith("-"):
            findings.append({"path": str(path), "issue": "tags_not_array", "auto_fix": True})

    # Broken wikilinks (only wiki-local links, skip memory/ 10_Daily/ etc.)
    for link in WIKILINK_RE.findall(text):
        target_slug = normalize_wikilink_target(link)
        if resolve_wikilink_path(target_slug) is None:
            findings.append(
                {
                    "path": str(path),
                    "issue": f"broken_wikilink:{target_slug}",
                    "auto_fix": False,
                }
            )

print(f"  Findings: {len(findings)}")
for f in findings:
    print(f"    [{f['issue']}]  {f['path']}")

# Orphan page detection
banner("Step 2b — Orphan page detection")
all_links_from: dict[str, set[str]] = {}
all_links_to: dict[str, set[str]] = {}
for note in notes:
    note_key = str(note["path"].relative_to(VAULT_WIKI))
    outgoing = {
        str(resolved.relative_to(VAULT_WIKI))
        for lnk in WIKILINK_RE.findall(note["text"])
        if (resolved := resolve_wikilink_path(normalize_wikilink_target(lnk))) is not None
    }
    all_links_from[note_key] = outgoing
    for tgt in outgoing:
        all_links_to.setdefault(tgt, set()).add(note_key)

orphans = []
for note in notes:
    note_key = str(note["path"].relative_to(VAULT_WIKI))
    no_outgoing = not all_links_from.get(note_key)
    no_incoming = note_key not in all_links_to
    if no_outgoing and no_incoming:
        orphans.append(note["path"])
        findings.append({"path": str(note["path"]), "issue": "orphan_page", "auto_fix": False})
print(f"  Orphan pages: {len(orphans)}")

# Evidence gap detection
banner("Step 2c — Evidence gap detection")
evidence_gaps = []
for note in notes:
    fm_match = FRONTMATTER_RE.match(note["text"])
    if fm_match:
        fm_text = fm_match.group(1)
        has_raw_id = bool(re.search(r"^source_raw_(?:id|ref)\s*:\s*\S", fm_text, re.MULTILINE))
        if not has_raw_id:
            evidence_gaps.append(note["path"])
            findings.append({"path": str(note["path"]), "issue": "evidence_gap", "auto_fix": False})
print(f"  Evidence gaps: {len(evidence_gaps)}")

# Missing cross-reference detection
banner("Step 2d — Missing cross-reference detection")
entity_stems = (
    {p.stem for p in (VAULT_WIKI / "entities").glob("*.md")}
    if (VAULT_WIKI / "entities").exists()
    else set()
)
for note in notes:
    if note["path"].parent.name == "entities":
        continue
    existing_links = {
        lnk.split("|")[0].strip().split("/")[-1] for lnk in WIKILINK_RE.findall(note["text"])
    }
    for stem in entity_stems:
        if stem in note["text"] and stem not in existing_links:
            findings.append(
                {
                    "path": str(note["path"]),
                    "issue": f"missing_cross_reference:{stem}",
                    "auto_fix": False,
                }
            )
print(f"  Total findings after all deterministic checks: {len(findings)}")

# ── Step 3: Semantic checks (Ollama) ─────────────────────────────────────────
banner("Step 3 — Semantic checks (gemma4:e2b)")
duplicates = []
contradictions = []
stale_notes: list[dict] = []
quality_flags = []

ollama_ok = health_check()
if not ollama_ok:
    print("  WARN: Ollama unavailable — skipping semantic checks")
else:
    # Contradiction detection
    contra_prompt = [
        {
            "role": "system",
            "content": (
                "Detect contradictions between knowledge notes. "
                "Given notes (index: title + excerpt), return JSON array of contradicting pairs: "
                '[[i, j, "claim_a", "claim_b"], ...] Return [] if none.'
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                f"[{i}] {n['path'].stem}: {n['text'][:300]}" for i, n in enumerate(notes)
            ),
        },
    ]
    print("  Calling Ollama for contradiction detection...")
    contra_raw = generate(messages=contra_prompt, model=MODELS["light"])
    try:
        clean = (
            contra_raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        start, end = clean.find("["), clean.rfind("]") + 1
        if start >= 0 and end > start:
            contradictions = json.loads(clean[start:end])
    except (json.JSONDecodeError, ValueError):
        print("  WARN: contradiction parse failed, skipping")
    print(f"  Contradictions found: {len(contradictions)}")

    # Stale check for notes older than 90 days with no updated field
    from datetime import datetime

    today_dt = datetime.now().date()
    for note in notes:
        fm_match = FRONTMATTER_RE.match(note["text"])
        if not fm_match:
            continue
        fm_text = fm_match.group(1)
        created_m = re.search(r"^created\s*:\s*(\d{4}-\d{2}-\d{2})", fm_text, re.MULTILINE)
        updated_m = re.search(r"^updated\s*:", fm_text, re.MULTILINE)
        if created_m and not updated_m:
            try:
                created_dt = datetime.fromisoformat(created_m.group(1)).date()
                if (today_dt - created_dt).days >= 90:
                    stale_prompt = [
                        {
                            "role": "system",
                            "content": (
                                f"This KB note was written on {created_dt}. Today is {today_dt}. "
                                "List any likely outdated claims. "
                                'Reply JSON: {"stale_claims": ["..."], "overall_stale": true/false}'
                            ),
                        },
                        {"role": "user", "content": note["text"][:1500]},
                    ]
                    stale_raw = generate(messages=stale_prompt, model=MODELS["light"])
                    try:
                        clean = (
                            stale_raw.strip()
                            .removeprefix("```json")
                            .removeprefix("```")
                            .removesuffix("```")
                            .strip()
                        )
                        stale_result = json.loads(clean)
                    except (json.JSONDecodeError, ValueError):
                        stale_result = {"stale_claims": [], "overall_stale": False}
                    if stale_result.get("overall_stale"):
                        stale_notes.append(
                            {
                                "path": str(note["path"]),
                                "created": str(created_dt),
                                "stale_claims": stale_result.get("stale_claims", []),
                            }
                        )
            except ValueError:
                pass
    print(f"  Stale notes found: {len(stale_notes)}")

    # Duplicate detection
    dup_prompt = [
        {
            "role": "system",
            "content": (
                "Detect near-duplicate knowledge notes. "
                "Given a list of notes (index: title + excerpt), return a JSON array "
                'of pairs that are likely duplicates: [[i, j, "reason"], ...] '
                "Return [] if none."
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                f"[{i}] {n['path'].stem}: {n['text'][:200]}" for i, n in enumerate(notes)
            ),
        },
    ]
    print("  Calling Ollama for duplicate detection (gemma4:e2b)...")
    dup_raw = generate(messages=dup_prompt, model=MODELS["light"])
    print(f"  Raw dup response: {dup_raw[:120]}")
    try:
        clean = (
            dup_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
        start, end = clean.find("["), clean.rfind("]") + 1
        if start >= 0 and end > start:
            duplicates = json.loads(clean[start:end])
    except (json.JSONDecodeError, ValueError):
        print("  WARN: dup parse failed, skipping")

    print(f"  Duplicate pairs found: {len(duplicates)}")
    for d in duplicates:
        print(f"    {d}")

# ── Step 4: Write patch plan ──────────────────────────────────────────────────
banner("Step 4 — Write patch plan")
RUNTIME_PATCHES.mkdir(parents=True, exist_ok=True)
patch_path = RUNTIME_PATCHES / f"kb-lint-{TODAY}.json"
patch_data = {
    "generated": TODAY,
    "total_notes": len(notes),
    "findings": findings,
    "duplicates": duplicates,
    "contradictions": contradictions,
    "stale_notes": stale_notes,
    "quality_flags": quality_flags,
    "auto_fixable": sum(1 for f in findings if f.get("auto_fix")),
}
patch_path.write_text(json.dumps(patch_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"  Patch plan written → {patch_path}")

# ── Step 5: Update log ────────────────────────────────────────────────────────
banner("Step 5 — Update vault/wiki/log.md")
log_path = VAULT_WIKI / "log.md"
n_findings = len(findings)
n_auto = patch_data["auto_fixable"]
n_dups = len(duplicates)
n_contra = len(contradictions)
n_stale = len(stale_notes)
log_row = (
    f"| {TODAY} | lint | {len(notes)} notes scanned, {n_findings} findings, "
    f"{n_dups} dups, {n_contra} contradictions, {n_stale} stale"
    f" | obsidian-lint | patch: {patch_path} |\n"
)
if log_path.exists():
    log_path.write_text(log_path.read_text(encoding="utf-8") + log_row, encoding="utf-8")
else:
    log_path.write_text(
        "| date | action | details | actor | artifact |\n|---|---|---|---|---|\n" + log_row,
        encoding="utf-8",
    )
print(f"  log updated → {log_path}")

# ── Step 6: save_memory audit pointer ────────────────────────────────────────
banner("Step 6 — save_memory audit pointer")
vault_path = pathlib.Path(settings.vault_path)
db_path = pathlib.Path(settings.index_db_path)
mem_store = MemoryStore(vault_path=vault_path, index_db_path=db_path)

mem_payload = MemoryCreate(
    memory_type="conversation_summary",
    title=f"KB Lint {TODAY}: {len(notes)} notes, {n_findings} findings",
    content=(
        f"Lint run on {TODAY}. "
        f"{len(notes)} notes scanned, {n_findings} findings "
        f"({n_auto} auto-fixable), {n_dups} duplicate pairs, "
        f"{n_contra} contradictions, {n_stale} stale notes.\n\n"
        f"Patch plan: {patch_path}"
    ),
    source="obsidian-lint",
    roles=["summary"],
    topics=["kb", "lint"],
    entities=[],
    projects=["mcp_obsidian"],
    tags=["kb", "lint", "audit"],
    raw_refs=[],
    confidence=0.95,
    language="ko",
)
mem_result = mem_store.save(mem_payload)
mem_id = mem_result.get("id", "?")
print(f"  save_memory → id={mem_id}")

# ── Final report ──────────────────────────────────────────────────────────────
banner("Phase 4 COMPLETE")
print(f"""
  notes scanned    : {len(notes)}
  findings         : {n_findings} ({n_auto} auto-fixable)
  orphan pages     : {len(orphans)}
  evidence gaps    : {len(evidence_gaps)}
  contradictions   : {len(contradictions)} pairs
  stale notes      : {len(stale_notes)}
  duplicates       : {n_dups} pairs
  patch plan       : {patch_path}
  log updated      : {log_path}
  memory id        : {mem_id}
""")

---
name: obsidian-lint
description: >-
  Audit vault/wiki/ notes for missing frontmatter, broken wikilinks, orphan pages,
  missing cross-references, evidence gaps, stale claims, contradictions, and duplicates.
  Produces a patch plan in runtime/patches/ and saves a summary via save_memory.
  Use when the user asks to "lint the KB", "audit wiki notes", "find broken links",
  "check frontmatter", "clean up the vault", "find contradictions", "check for stale notes",
  "KB 노트 점검", "KB 상태 확인", "위키 정리해줘", "오류 찾아줘", or "고쳐줘".
triggers:
  - "lint 돌려줘"
  - "KB 점검"
  - "obsidian-lint"
  - "위키 감사"
  - "일관성 검사"
  - "lint the KB"
  - "audit wiki notes"
  - "find broken links"
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut

# obsidian-lint

Audit existing `vault/wiki/` notes for quality issues: missing frontmatter
fields, broken wikilinks, stale content, duplicates, and structural
inconsistencies. Produce a patch plan in `runtime/patches/` and optionally
apply auto-fixable issues.

**Use this skill when** the user asks to "lint the KB", "audit wiki notes",
"find broken links", "check frontmatter", or "clean up the vault".

---

## Prerequisites

- `vault/wiki/` populated by prior `obsidian-ingest` runs.
- Ollama running at `http://localhost:11434` (used for semantic duplicate
  detection and content quality scoring). Light model `gemma4:e2b` by default.
- `runtime/patches/` directory exists (created by setup).

Check Ollama: `python - <<'EOF'
from scripts.ollama_kb import health_check; print("OK" if health_check() else "FAIL")
EOF`

---

## Shared Ollama Call Convention

All Ollama calls use `scripts/ollama_kb.py::generate()`.
Run Python from the **repo root**:

```python
import sys
sys.path.insert(0, ".")          # repo root must be cwd
from scripts.ollama_kb import generate, MODELS

# obsidian-lint defaults to light model; upgrade to primary for complex cases
model = MODELS["light"]
response = generate(messages=messages, model=model)
```

---

## Step 1 — Collect all wiki notes

```python
import pathlib

wiki_root = pathlib.Path("vault/wiki")
notes = []
for md in sorted(wiki_root.rglob("*.md")):
    if md.name in ("index.md", "log.md"):
        continue
    text = md.read_text(encoding="utf-8")
    notes.append({"path": md, "text": text})
```

---

## Step 2 — Deterministic checks (no Ollama needed)

For each note, check:

| Check | Issue type | Auto-fix? |
|---|---|---|
| Missing frontmatter `---` block | `missing_frontmatter` | No |
| Missing required keys (`note_kind`, `title`, `created`, `tags`) | `missing_field:<key>` | Partial |
| Broken wikilink `[[...]]` target not found in `vault/wiki/` | `broken_wikilink:<target>` | No |
| `tags` field is a string, not a list | `tags_not_array` | Yes |
| `created` not ISO date format | `invalid_date` | No |
| File name differs from `slug` frontmatter field | `slug_mismatch` | Yes (rename) |
| No outgoing `[[link]]` at all (Karpathy: every note must link) | `orphan_page` | No |
| Note mentions an entity stem that exists as `vault/wiki/entities/<name>.md` but has no `[[entities/<name>]]` link | `missing_cross_reference:<name>` | Partial |
| `source_raw_id` field missing or empty (no evidence trail) | `evidence_gap` | No |
| `created` date ≥ 90 days before today with no `updated` field (stale) | `stale_note` | No |

**Cross-vault wikilinks:** links of the form `[[memory/...]]`, `[[10_Daily/...]]`,
or any path outside `vault/wiki/` are intentional cross-vault references. Do NOT
flag them as broken. Only flag links that start with `wiki/` or have no prefix
and resolve to nothing under `vault/wiki/`.

**Orphan detection:** a note is an orphan if it has zero `[[...]]` outgoing links
to other `vault/wiki/` notes AND is not referenced by any other wiki note.

**Missing cross-reference detection:**

```python
import re, pathlib

entity_stems = {p.stem for p in pathlib.Path("vault/wiki/entities").glob("*.md")}
for note in notes:
    existing_links = set(re.findall(r'\[\[([^\]]+)\]\]', note["text"]))
    linked_entities = {l.split("/")[-1].split("|")[0] for l in existing_links}
    for stem in entity_stems:
        if stem in note["text"] and stem not in linked_entities:
            findings.append({
                "path": str(note["path"]), "issue": f"missing_cross_reference:{stem}",
                "line": 0, "auto_fix": False
            })
```

**Evidence gap:** notes where `source_raw_id` is absent or empty have no traceable
evidence origin. Flag for manual review — do not auto-fix.

Collect all findings as a list of `{"path", "issue", "line", "auto_fix"}` dicts.

---

## Step 3 — Semantic checks (Ollama, light model)

**3a. Contradiction detection**

Compare pairs of notes in the same category. Ask Ollama if any two notes make
conflicting factual claims:

```python
contra_prompt = [
    {
        "role": "system",
        "content": (
            "You detect contradictions between knowledge notes. "
            "Given a list of notes (index: title + excerpt), return a JSON array "
            "of pairs where the notes contradict each other: "
            '[[i, j, "conflicting claim A", "conflicting claim B"], ...]'
            " Return [] if none."
        ),
    },
    {
        "role": "user",
        "content": "\n".join(
            f"[{i}] {n['path'].stem}: {n['text'][:400]}"
            for i, n in enumerate(notes)
        ),
    },
]
contra_result = generate(messages=contra_prompt, model=MODELS["light"])
try:
    contradictions = json.loads(contra_result.strip().strip("```json").strip("```").strip())
except (json.JSONDecodeError, TypeError):
    contradictions = []
```

**3b. Stale claim check**

For notes flagged as `stale_note` in Step 2, ask Ollama if any claims are likely
outdated given their `created` date vs. today:

```python
stale_prompt = [
    {
        "role": "system",
        "content": (
            "This KB note was written on {created}. Today is {today}. "
            "Identify any claims that may be stale or outdated. "
            'Reply JSON: {"stale_claims": ["<claim>", ...], "overall_stale": true/false}'
        ),
    },
    {"role": "user", "content": note_text[:2000]},
]
stale_result = generate(messages=stale_prompt, model=MODELS["light"])
```

**3c. Duplicate detection**

Embed note titles + first 200 chars via a pairwise similarity prompt:

```python
dup_prompt = [
    {
        "role": "system",
        "content": (
            "You detect near-duplicate knowledge notes. "
            "Given a list of notes (index: title + excerpt), return a JSON array "
            "of pairs that are likely duplicates: "
            '[[i, j, "reason"], ...]'
            " Return [] if none found."
        ),
    },
    {
        "role": "user",
        "content": "\n".join(
            f"[{i}] {n['path'].stem}: {n['text'][:200]}"
            for i, n in enumerate(notes)
        ),
    },
]
dup_result = generate(messages=dup_prompt, model=MODELS["light"])
```

**3d. Content quality scoring** (only for notes flagged in Step 2 or with
`created` > 90 days ago)

```python
quality_prompt = [
    {
        "role": "system",
        "content": (
            "Score this KB note on a scale of 1-5 for: "
            "completeness, clarity, factual density. "
            "Reply JSON: "
            '{"completeness": N, "clarity": N, "density": N, "suggestion": "..."}'
        ),
    },
    {"role": "user", "content": note_text[:2000]},
]
score = generate(messages=quality_prompt, model=MODELS["light"])
```

Flag notes with any score < 3 for review.

---

## Step 4 — Write patch plan

Save to `runtime/patches/kb-lint-<YYYY-MM-DD>.json`:

```json
{
  "generated": "YYYY-MM-DD",
  "total_notes": N,
  "findings": [
    {
      "path": "vault/wiki/concepts/foo.md",
      "issue": "missing_field:created",
      "line": 3,
      "auto_fix": false,
      "suggestion": "Add `created: YYYY-MM-DD` to frontmatter"
    }
  ],
  "duplicates": [
    {"note_a": "...", "note_b": "...", "reason": "..."}
  ],
  "contradictions": [
    {"note_a": "...", "note_b": "...", "claim_a": "...", "claim_b": "..."}
  ],
  "stale_notes": [
    {"path": "...", "stale_claims": ["..."], "created": "..."}
  ],
  "quality_flags": [
    {"path": "...", "scores": {...}, "suggestion": "..."}
  ],
  "auto_fixable": N
}
```

---

## Step 5 — Apply auto-fixes (optional)

Only when the user confirms. Accepted confirmation phrases include:
- English: `--fix`, "apply fixes", "fix it", "fix them"
- Korean: "고쳐줘", "수정해줘", "적용해줘", "자동 수정", "고치고 싶어"

If the user said only "점검해줘" or "확인해줘" **without a fix request**, produce
the patch plan and stop — do NOT apply fixes automatically.

- `tags_not_array`: convert string to single-element YAML list.
- `slug_mismatch`: rename file to match `slug` frontmatter value.

Print each fix:
```
AUTO-FIX: vault/wiki/concepts/foo.md — tags_not_array → converted to list
```

Do **not** auto-fix `broken_wikilink`, `missing_frontmatter`, or quality issues.
Those require human review.

---

## Step 6 — Update change log

Append one row to `vault/wiki/log.md`:

```
| <YYYY-MM-DD> | lint | <N> findings, <M> auto-fixed | obsidian-lint | patch: runtime/patches/kb-lint-<date>.json |
```

---

## Step 7 — Save lint summary to memory

After the patch plan is written, register a `save_memory` pointer so the lint
run is discoverable via `search_memory`:

```python
memory_payload = {
    "title": f"KB Lint {date}: {total_notes} notes, {total_findings} findings",
    "content": (
        f"Lint run on {date}. "
        f"{total_notes} notes scanned, {total_findings} findings "
        f"({auto_fixable} auto-fixable), {len(duplicates)} duplicate pairs, "
        f"{len(contradictions)} contradictions, {len(stale_notes)} stale.\n\n"
        f"Patch plan: runtime/patches/kb-lint-{date}.json\n"
        f"Audit trail: [[wiki/log]]"
    ),
    "roles": ["summary"],
    "topics": ["kb", "lint"],
    "entities": [],
    "projects": ["mcp_obsidian"],
    "tags": ["kb", "lint", "audit"],
    "raw_refs": [],
}
```

---

## Step 8 — Report

```
lint complete
  notes scanned    : N
  findings         : N (M auto-fixable)
  orphan pages     : N
  missing x-refs   : N
  evidence gaps    : N
  stale notes      : N
  contradictions   : N pairs
  duplicates       : N pairs
  quality flags    : N notes
  patch plan       : runtime/patches/kb-lint-<date>.json
  log updated      : vault/wiki/log.md
  memory id        : <MEM-ID>
```

---

## Stop conditions

- No wiki notes → report `vault/wiki/ is empty. Run obsidian-ingest first.`
- Ollama unreachable → run deterministic checks only; skip semantic steps;
  label output `[partial: Ollama unavailable — semantic checks skipped]`.
- JSON parse error from Ollama → skip that semantic check; log
  `WARN: <check> result unparseable, skipped`.


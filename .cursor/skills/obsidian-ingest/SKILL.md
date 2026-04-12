---
name: obsidian-ingest
description: >-
  Ingest a document, article, or reference material into the KB (vault/wiki/),
  extract structured knowledge with Gemma 4 via Ollama, archive the raw source,
  and create a pointer memory note. Use when the user asks to "ingest", "add to KB",
  "extract knowledge", "store in wiki", "KB에 추가", "위키에 저장", or provides a
  document/file/URL to add to the knowledge base.
  Do NOT use for conversation logs or chat transcripts — use paste-conversation-to-obsidian instead.
triggers:
  - "ingest해줘"
  - "위키에 넣어줘"
  - "obsidian-ingest"
  - "KB에 추가"
  - "raw 파일 처리"
  - "add to KB"
  - "extract knowledge"
  - "store in wiki"
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut

# obsidian-ingest

Ingest a source document or conversation excerpt into the KB (`vault/wiki/`),
extract structured knowledge, and create a pointer memory note via `save_memory`.

**Use this skill when** the user pastes text, provides a document path, or asks
to "ingest", "add to KB", "extract knowledge", or "store in wiki".

---

## Prerequisites

- Ollama running at `http://localhost:11434` with `gemma4:e4b` pulled.
- MCP server running (local or production) for `save_memory`.
- `scripts/ollama_kb.py` present in the repo root.

Check Ollama: `python - <<'EOF'
from scripts.ollama_kb import health_check; print("OK" if health_check() else "FAIL")
EOF`

---

## Shared Ollama Call Convention

All Ollama calls in this skill use `scripts/ollama_kb.py::generate()`.
Run Python from the **repo root** so the relative import resolves:

```python
import sys
sys.path.insert(0, ".")          # repo root must be cwd
from scripts.ollama_kb import generate, MODELS

response = generate(messages=messages, model=MODELS["primary"])
```

Never call `requests.post` directly. Model, timeout, and endpoint are defined in
`scripts/ollama_kb.py`.

---

## Step 1 — Receive input and archive raw

Accept one of:
- Pasted text (inline in the user message)
- A file path (`@path/to/file`)
- A URL (fetch first, then proceed with the text)

Determine a `slug` for the note (snake_case, max 40 chars, e.g. `gemma4_ollama_integration`).

**1a. Copy to vault/raw/ (immutable source layer)**

Before any processing, write the original unmodified input to:
`vault/raw/<input_type>/<slug>.md`

| Input type | vault/raw/ path |
|---|---|
| Web article / pasted text | `vault/raw/articles/<slug>.md` |
| PDF or document | `vault/raw/pdf/<slug>.md` |
| Manual note | `vault/raw/notes/<slug>.md` |

```python
import pathlib
from datetime import date

raw_path = pathlib.Path(f"vault/raw/articles/{slug}.md")
raw_path.parent.mkdir(parents=True, exist_ok=True)
raw_path.write_text(
    f"---\nslug: {slug}\ndate: {date.today().isoformat()}\nsource: obsidian-ingest\n---\n\n{input_text}",
    encoding="utf-8",
)
```

**1b. Archive raw to mcp_raw/**

Before analysis, archive the raw source via `archive_raw` so it is discoverable
via `search_memory` and linked in the wiki note's `source_raw_id` frontmatter:

```python
mcp_id = f"ingest-{slug}-{date}"   # e.g. ingest-gemma4_ollama_integration-2026-04-07
# call archive_raw tool:
# archive_raw(source="obsidian-ingest", mcp_id=mcp_id, body_markdown=input_text)
```

Skip `archive_raw` only if the input is already a known `mcp_id` (previously archived).

---

## Step 2 — Classify and decide wiki path

Ask Ollama to classify the input:

```python
classify_prompt = [
    {
        "role": "system",
        "content": (
            "You classify knowledge fragments for an Obsidian vault. "
            "Reply with exactly one JSON object: "
            '{"category": "<sources|concepts|entities|analyses>", '
            '"title": "<concise title, ≤60 chars>", '
            '"summary": "<one sentence>", '
            '"tags": ["<tag1>", "<tag2>"]}'
        ),
    },
    {"role": "user", "content": f"Classify this:\n\n{input_text[:4000]}"},
]
classification = generate(messages=classify_prompt, model=MODELS["primary"])
```

Parse the JSON. Map `category` to the vault path:

| category | vault path |
|---|---|
| sources | `vault/wiki/sources/<slug>.md` |
| concepts | `vault/wiki/concepts/<slug>.md` |
| entities | `vault/wiki/entities/<slug>.md` |
| analyses | `vault/wiki/analyses/<slug>.md` |

---

## Step 3 — Extract structured content

Ask Ollama to produce the full wiki note body:

```python
extract_prompt = [
    {
        "role": "system",
        "content": (
            "You are a structured knowledge-base compiler. "
            "Given source text, produce a clean Obsidian markdown note. "
            "Include: key facts, important quotes (with attribution), "
            "related concepts, open questions. "
            "Do not invent facts not present in the source."
        ),
    },
    {"role": "user", "content": input_text},
]
body = generate(messages=extract_prompt, model=MODELS["primary"])
```

---

## Step 4 — Write the wiki note

Construct the full note with frontmatter:

```markdown
---
note_kind: wiki
category: <category>
title: <title>
slug: <slug>
created: <YYYY-MM-DD>
tags: [<tag1>, <tag2>]
source_raw_id: <mcp_id if available, else "">
---

<body from Ollama>
```

Write to `vault/wiki/<category>/<slug>.md`. Use the `write_file` shell command
or direct file write — do **not** use `save_memory` for this step.

---

## Step 5 — Patch cross-links in related entity and concept notes

After writing the wiki note, find existing notes in `vault/wiki/entities/` and
`vault/wiki/concepts/` whose titles or slugs appear in the new note's content.
Add a `[[back-link]]` to the new note inside each related note if not already present:

```python
import re, pathlib

new_note_link = f"[[wiki/{category}/{slug}]]"
for related_dir in ("vault/wiki/entities", "vault/wiki/concepts"):
    for related_path in pathlib.Path(related_dir).glob("*.md"):
        related_text = related_path.read_text(encoding="utf-8")
        # if the new note mentions the related stem, add a link back
        if related_path.stem in body and new_note_link not in related_text:
            related_text += f"\n\n## Related\n\n- {new_note_link}\n"
            related_path.write_text(related_text, encoding="utf-8")
```

Also add `[[entities/<stem>]]` and `[[concepts/<stem>]]` links in the new note body
for any entity/concept stems that are mentioned but not yet linked.

---

## Step 6 — Update the change log and index

Append one row to `vault/wiki/log.md`:

```
| <YYYY-MM-DD> | ingest | <category>/<slug>.md | obsidian-ingest | <one-line summary> |
```

Also update `vault/wiki/index.md` **Recent Notes** section: prepend a
`[[<category>/<slug>]]` link under `## Recent Notes`, keeping the 10 most recent.
If the new note introduces a category previously empty, also add a link under that
category section.

---

## Step 7 — Create pointer memory note

Call `save_memory` with a compact pointer record following the
**Pointer Template Policy** in `AGENTS.md` and `docs/storage-routing.md`:

```python
memory_payload = {
    "title": f"KB: {title}",
    "content": (
        f"{summary}\n\n"
        f"See [[wiki/{category}/{slug}]] for full details."
    ),
    "roles": ["fact"],
    "topics": tags,
    "entities": [],
    "projects": ["mcp_obsidian"],
    "tags": ["kb", "wiki", category],
    "raw_refs": [mcp_id],   # link to archive_raw from Step 1b
}
```

**Must not** include the full wiki note body in `content`.
`raw_refs` must reference the `mcp_id` from Step 1b (`archive_raw`).

---

## Step 8 — Report

```
ingest OK
  raw copy  : vault/raw/articles/<slug>.md
  wiki note : vault/wiki/<category>/<slug>.md
  raw id    : <mcp_id>
  memory id : <MEM-ID>
  log entry : vault/wiki/log.md + index.md updated
```

---

## Stop conditions

- Ollama unreachable → stop, print `FAIL: Ollama not running at <base_url>`.
- `archive_raw` MCP call fails → stop, report error; do not proceed to wiki write.
- `save_memory` fails → report error; wiki note and log are already written, state manual recovery path.
- JSON parse error from classifier → retry once with a stricter prompt; if still
  failing, default `category` to `sources`.
- File write error → report path + OS error, do not silently skip.


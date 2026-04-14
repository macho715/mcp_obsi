---
name: obsidian-query
description: >-
  Query the KB (vault/wiki/) using natural language. Retrieve relevant wiki notes,
  synthesize an answer with Gemma 4 via Ollama, optionally save the analysis to
  wiki/analyses/, and register a save_memory pointer. Use when the user asks
  "what do we know about X", "find in KB", "search wiki", "query knowledge base",
  "KB에서 찾아줘", "우리가 알고 있는 게 뭐야", "위키에서 검색", or wants a grounded
  answer from stored knowledge.
triggers:
  - "wiki에서 찾아줘"
  - "KB에서 검색"
  - "obsidian-query"
  - "지식 베이스 조회"
  - "what do we know about"
  - "find in KB"
  - "search wiki"
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut

# obsidian-query

Query the KB (`vault/wiki/`) using natural language. Retrieve relevant wiki
notes, optionally synthesize an answer with Ollama, and return cited results.

**Use this skill when** the user asks "what do we know about X", "find in KB",
"search wiki", "query knowledge base", or wants a grounded answer from stored
knowledge.

---

## Prerequisites

- Ollama running at `http://localhost:11434` with `gemma4:e4b` pulled.
- `vault/wiki/` populated by prior `obsidian-ingest` runs.
- MCP server running for `search_memory` (optional; used to find pointer notes).

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

response = generate(messages=messages, model=MODELS["primary"])
```

---

## Step 1 — Parse the query

Extract:
- `query_text` — the natural language question
- `scope` — optional: `sources | concepts | entities | analyses | all` (default `all`)
- `max_results` — optional (default 5)

---

## Step 2 — Candidate retrieval

**2a. Check index.md first (primary navigation hub)**

Read `vault/wiki/index.md` and extract all `[[wikilinks]]` as candidate paths.
This surfaces notes already known to the index — often the most important ones:

```python
import re, pathlib

index_text = pathlib.Path("vault/wiki/index.md").read_text(encoding="utf-8")
index_links = re.findall(r'\[\[([^\]|#]+)', index_text)
# resolve each link relative to vault/wiki/
index_candidates = []
for link in index_links:
    candidate = pathlib.Path(f"vault/wiki/{link}.md")
    if candidate.exists():
        index_candidates.append({"path": str(candidate), "text": candidate.read_text(encoding="utf-8")})
```

Score these against `query_text` by keyword overlap and keep top matches.

**2b. Full-text search in all wiki files (secondary)**

```python
wiki_root = pathlib.Path("vault/wiki")
all_results = []
for md in wiki_root.rglob("*.md"):
    if md.name in ("index.md", "log.md"):
        continue
    text = md.read_text(encoding="utf-8")
    all_results.append({"path": str(md), "text": text})
```

Merge `index_candidates` + `all_results`, deduplicate by path, sort by keyword
overlap, keep top `max_results * 3` for re-ranking:

```python
seen_paths = set()
candidates = []
for item in index_candidates + all_results:
    p = item["path"]
    if p not in seen_paths:
        seen_paths.add(p)
        # score by keyword overlap
        score = sum(1 for word in query_text.lower().split() if word in item["text"].lower())
        candidates.append({**item, "score": score})
candidates.sort(key=lambda x: x["score"], reverse=True)
candidates = candidates[: max_results * 3]
```

**2c. Memory pointer search (tertiary, if MCP available)**

Call `search_memory` with the query text. Use returned `memory_id`s to cross-
reference wiki paths via frontmatter `slug`.

---

## Step 3 — Re-rank with Ollama

If `candidates` is empty, skip this step and proceed to Step 4 with an empty list.
The Stop conditions will handle the no-match report.

```python
import json

if not candidates:
    top_candidates = []
else:
    rerank_prompt = [
        {
            "role": "system",
            "content": (
                "You are a relevance scorer. Given a query and a list of document "
                "excerpts, return a JSON array of indices sorted by relevance "
                "(most relevant first). "
                "Format: [0, 2, 1, ...]"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Query: {query_text}\n\n"
                + "\n\n---\n\n".join(
                    f"[{i}] {r['path']}\n{r['text'][:800]}"
                    for i, r in enumerate(candidates)
                )
            ),
        },
    ]
    raw_rank = generate(messages=rerank_prompt, model=MODELS["primary"])
    try:
        # Strip markdown code fences if present
        clean = raw_rank.strip().strip("```json").strip("```").strip()
        ranked_indices = json.loads(clean)
        top_candidates = [candidates[i] for i in ranked_indices[:max_results] if i < len(candidates)]
    except (json.JSONDecodeError, IndexError, TypeError):
        # Fallback: use keyword-match order
        top_candidates = candidates[:max_results]
```

---

## Step 4 — Synthesize answer

```python
context_block = "\n\n---\n\n".join(
    f"Source: {c['path']}\n{c['text'][:1500]}"
    for c in top_candidates
)

synth_prompt = [
    {
        "role": "system",
        "content": (
            "You are a knowledge assistant. Answer the user's question using "
            "only the provided KB excerpts. Cite sources as [[wiki/path]]. "
            "If the answer is not in the KB, say so explicitly."
        ),
    },
    {
        "role": "user",
        "content": f"Question: {query_text}\n\nKB excerpts:\n{context_block}",
    },
]
answer = generate(messages=synth_prompt, model=MODELS["primary"])
```

---

## Step 5 — Optionally save analysis to wiki

If the synthesized answer has **reuse value** (non-trivial synthesis, comparison,
or conclusion not directly found in a single source note), save it to
`vault/wiki/analyses/<slug>.md`:

```markdown
---
note_kind: wiki
category: analyses
title: <synthesized answer title>
slug: <query-derived slug>
created: <YYYY-MM-DD>
tags: [analysis, kb]
query: "<original query_text>"
sources: [<path1>, <path2>]
---

<answer from Ollama>
```

Then register a `save_memory` pointer following the **Pointer Template Policy**:

```python
memory_payload = {
    "title": f"KB Analysis: {title}",
    "content": (
        f"{one_sentence_summary}\n\n"
        f"See [[wiki/analyses/{slug}]]."
    ),
    "roles": ["fact"],
    "topics": tags,
    "entities": [],
    "projects": ["mcp_obsidian"],
    "tags": ["kb", "analysis"],
    "raw_refs": [],
}
```

Skip this step for simple factual lookups where the answer is a direct quote from
one source note.

---

## Step 6 — Report

```
query: <query_text>
answer:
  <synthesized answer with [[wiki/...]] citations>

sources used:
  - vault/wiki/<path1>
  - vault/wiki/<path2>

analysis saved : vault/wiki/analyses/<slug>.md  (or "not saved: simple lookup")
memory pointer : <MEM-ID>  (or "skipped")
```

---

## Stop conditions

- Ollama unreachable → return raw keyword-match results without synthesis;
  label output `[no-synthesis: Ollama unavailable]`.
- No wiki notes found → report `KB empty or no match for query`.
- JSON parse error in re-rank → skip re-rank, use keyword-match order.


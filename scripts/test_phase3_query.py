"""
Phase 3: obsidian-query end-to-end test script.

Run from repo root:
    .venv\\\\Scripts\\\\python scripts/test_phase3_query.py

Flow:
  1. Ollama health check
  2. Candidate retrieval from vault/wiki/
  3. Re-rank with Ollama (gemma4:e4b)
  4. Synthesize answer with citations
  5. Report
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, ".")

from app.config import settings
from scripts.ollama_kb import MODELS, generate, health_check

VAULT_WIKI = pathlib.Path(settings.vault_path).resolve() / "wiki"
QUERY_TEXT = "Gemma 4 모델에 대해 우리가 알고 있는 것은? 크기와 특징을 알려줘."
MAX_RESULTS = 5


def banner(step: str) -> None:
    print(f"\n{'─' * 60}\n  {step}\n{'─' * 60}")


# ── Step 1: Ollama health ─────────────────────────────────────────────────────
banner("Step 1 — Ollama health check")
if not health_check():
    print("FAIL: Ollama not reachable")
    sys.exit(1)
print("OK: Ollama reachable")

# ── Step 2: Candidate retrieval ───────────────────────────────────────────────
banner("Step 2 — Candidate retrieval from vault/wiki/")
candidates = []
if not VAULT_WIKI.exists():
    print("FAIL: vault/wiki/ does not exist")
    sys.exit(1)

for md in sorted(VAULT_WIKI.rglob("*.md")):
    if md.name in ("index.md", "log.md"):
        continue
    text = md.read_text(encoding="utf-8")
    wiki_ref = f"[[wiki/{md.relative_to(VAULT_WIKI).with_suffix('').as_posix()}]]"
    # Keyword score: count query term overlaps
    q_terms = set(QUERY_TEXT.lower().split())
    score = sum(1 for t in q_terms if t in text.lower())
    candidates.append({"path": str(md), "wiki_ref": wiki_ref, "text": text, "score": score})

# Sort by keyword score, keep top candidates for re-rank
candidates.sort(key=lambda x: x["score"], reverse=True)
top_for_rerank = candidates[: MAX_RESULTS * 3]
print(f"  Total notes scanned: {len(candidates)}")
print(f"  Top candidates for re-rank: {len(top_for_rerank)}")
for c in top_for_rerank:
    print(f"    score={c['score']}  {c['path']}")

# ── Step 3: Re-rank with Ollama ───────────────────────────────────────────────
banner("Step 3 — Re-rank with Ollama (gemma4:e4b)")

if not top_for_rerank:
    print("SKIP: no candidates — KB empty or no match")
    top_candidates = []
else:
    rerank_prompt = [
        {
            "role": "system",
            "content": (
                "You are a relevance scorer. Given a query and document excerpts, "
                "return a JSON array of indices sorted by relevance (most relevant first). "
                "Format: [0, 2, 1, ...] — indices only, no explanation."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Query: {QUERY_TEXT}\n\n"
                + "\n\n---\n\n".join(
                    f"[{i}] {c['wiki_ref']}\n{c['text'][:600]}"
                    for i, c in enumerate(top_for_rerank)
                )
            ),
        },
    ]
    print("  Calling Ollama for re-rank...")
    raw_rank = generate(messages=rerank_prompt, model=MODELS["primary"])
    print(f"  Raw re-rank response: {raw_rank[:120]}")
    try:
        clean = (
            raw_rank.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
        # Extract first JSON array from response
        start = clean.find("[")
        end = clean.rfind("]") + 1
        if start >= 0 and end > start:
            ranked_indices = json.loads(clean[start:end])
        else:
            ranked_indices = list(range(len(top_for_rerank)))
        top_candidates = [
            top_for_rerank[i] for i in ranked_indices[:MAX_RESULTS] if i < len(top_for_rerank)
        ]
        print(f"  Re-ranked top {len(top_candidates)} candidates")
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        print(f"  WARN: re-rank parse failed ({e}), using keyword order")
        top_candidates = top_for_rerank[:MAX_RESULTS]

# ── Step 4: Synthesize answer ─────────────────────────────────────────────────
banner("Step 4 — Synthesize answer with Ollama")

if not top_candidates:
    print("SKIP: no candidates to synthesize")
    sys.exit(0)

context_block = "\n\n---\n\n".join(
    f"Source: {c['wiki_ref']}\n{c['text'][:1200]}" for c in top_candidates
)
synth_prompt = [
    {
        "role": "system",
        "content": (
            "You are a knowledge assistant. Answer in Korean using only the provided "
            "KB excerpts. Cite sources as [[wiki/path]]. "
            "If the answer is not in the KB, say so explicitly."
        ),
    },
    {
        "role": "user",
        "content": f"질문: {QUERY_TEXT}\n\nKB 내용:\n{context_block}",
    },
]
print("  Calling Ollama for synthesis...")
answer = generate(messages=synth_prompt, model=MODELS["primary"])
print(f"  Answer ({len(answer)} chars):\n")
print(answer)

# ── Step 5: Report ────────────────────────────────────────────────────────────
banner("Phase 3 COMPLETE")
print(f"""
  query         : {QUERY_TEXT}
  notes scanned : {len(candidates)}
  sources used  : {len(top_candidates)}
  answer length : {len(answer)} chars
  analysis saved: not saved (simple lookup)

  Sources:
""")
for c in top_candidates:
    print(f"    - {c['path']}")

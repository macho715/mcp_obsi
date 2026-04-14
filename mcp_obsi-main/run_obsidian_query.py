# ruff: noqa: E501
import json
import pathlib
import re
import sys

sys.path.insert(0, ".")
from scripts.ollama_kb import MODELS, generate, health_check


def run_query(query_text, max_results=5):
    if not health_check():
        print("[no-synthesis: Ollama unavailable]")
        return

    index_candidates = []
    index_path = pathlib.Path("vault/wiki/index.md")
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        index_links = re.findall(r"\[\[([^\]|#]+)", index_text)
        for link in index_links:
            candidate = pathlib.Path(f"vault/wiki/{link}.md")
            if candidate.exists():
                index_candidates.append(
                    {"path": str(candidate), "text": candidate.read_text(encoding="utf-8")}
                )

    wiki_root = pathlib.Path("vault/wiki")
    all_results = []
    if wiki_root.exists():
        for md in wiki_root.rglob("*.md"):
            if md.name in ("index.md", "log.md"):
                continue
            text = md.read_text(encoding="utf-8")
            all_results.append({"path": str(md), "text": text})

    seen_paths = set()
    candidates = []
    for item in index_candidates + all_results:
        p = item["path"]
        if p not in seen_paths:
            seen_paths.add(p)
            # Add basic keyword scoring
            score = sum(1 for word in query_text.lower().split() if word in item["text"].lower())
            candidates.append({**item, "score": score})

    candidates.sort(key=lambda x: x["score"], reverse=True)
    candidates = candidates[: max_results * 3]

    if not candidates:
        print("KB empty or no match for query")
        return

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
                    f"[{i}] {r['path']}\n{r['text'][:800]}" for i, r in enumerate(candidates)
                )
            ),
        },
    ]
    raw_rank = generate(messages=rerank_prompt, model=MODELS["primary"])
    try:
        clean = (
            raw_rank.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
        if not clean.startswith("["):
            clean = clean[clean.find("[") :]
        if not clean.endswith("]"):
            clean = clean[: clean.rfind("]") + 1]
        ranked_indices = json.loads(clean)
        top_candidates = [
            candidates[i] for i in ranked_indices[:max_results] if i < len(candidates)
        ]
    except Exception:
        top_candidates = candidates[:max_results]

    context_block = "\n\n---\n\n".join(
        f"Source: {c['path']}\n{c['text'][:1500]}" for c in top_candidates
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

    print(f"query: {query_text}")
    print("answer:")
    print(answer)
    print("\nsources used:")
    for c in top_candidates:
        print(f"  - {c['path']}")

    print("\nanalysis saved : not saved: simple lookup")
    print("memory pointer : skipped")


run_query("How does the llm-wiki-karpathy system handle knowledge accumulation and page types?")

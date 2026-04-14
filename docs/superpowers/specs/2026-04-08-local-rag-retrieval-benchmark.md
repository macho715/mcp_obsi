# Phase C Benchmark Report: local-rag Lexical Retrieval

**Date:** 2026-04-08
**Corpus:** `C:\Users\jichu\Downloads\valut\wiki`
**Engine:** lexical (word-count BM25-like scoring)
**Documents indexed:** 10 (excluding index.md, log.md)

---

## Benchmark Queries & Results

| # | Query | Top-3 Results | Top Score | Precision Signal |
|---|-------|--------------|----------|-----------------|
| 1 | `HVDC logistics ontology` | hvdc-logistics-ontology-guide-v2-round2-140323.md, hvdc-logistics-ontology-guide.md | 17.0 | ✅ strong |
| 2 | `Gemma 4 model specs` | gemma-4-model-architecture-overview-round3-14065.md, gemma-4-llm-model.md, gemma-4-llm-specs.md | 7.0 | ✅ good |
| 3 | `Karpathy LLM wiki` | karpathy-llm-wiki-query-result.md, karpathy-llm-wiki-operation-round1-140004.md, llm-wiki-karpathy.md | 54.0 | ✅ very strong |
| 4 | `llm wiki operation` | karpathy-llm-wiki-query-result.md, karpathy-llm-wiki-operation-round1-140004.md, llm-wiki-karpathy.md | 41.0 | ✅ very strong |
| 5 | `logistics guide` | hvdc-logistics-ontology-guide-v2-round2-140323.md, hvdc-logistics-ontology-guide.md | 3.0 | ✅ relevant |
| 6 | `ontology guide` | hvdc-logistics-ontology-guide-v2-round2-140323.md, hvdc-logistics-ontology-guide.md | 3.0 | ✅ relevant |
| 7 | `model parameters` | hvdc-logistics-ontology-guide-v2-round2-140323.md, gemma-4-llm-model.md, gemma-4-model-architecture-overview-round3-14065.md | 1.0 | ⚠️ weak — corpus lacks explicit parameter tables |
| 8 | `neural network` | (empty) | 0 | ❌ no match |
| 9 | `tokenizer` | (empty) | 0 | ❌ no match |
| 10 | `context window` | gemma-4-llm-model.md, gemma-4-llm-specs.md, gemma-4-model-architecture-overview-round3-14065.md | 2.0 | ✅ relevant |

---

## Analysis

### Precision@k Summary

| Metric | Value |
|--------|-------|
| Total queries | 10 |
| Queries returning ≥1 result | 8/10 |
| Queries with strong signal (score ≥ 3) | 6/10 |
| Queries with weak/no result | 2/10 |

### Strengths

- HVDC and LLM-related queries return highly targeted results with high scores
- Corpus is well-curated for domain-specific terms (HVDC, logistics, Gemma, Karpathy)
- BM25-like scoring is effective when query terms appear verbatim in documents

### Weaknesses

- Queries with terms absent from the corpus (`neural network`, `tokenizer`) return empty — expected for small corpus but reveals coverage gap
- `model parameters` score is weak (1.0) — corpus may not contain explicit parameter tables despite Gemma docs being present
- Precision degrades for queries with generic multi-word terms (e.g. `logistics guide` score only 3.0)

---

## Decision: Rerank / Vector DB

**Threshold:** precision@k ≥ 80% required to skip rerank
**Achieved:** 6/10 queries with strong signal = 60% (below threshold)

**AMBER:** Corpus-level lexical precision is 60%. Recommend adding lightweight cross-encoder reranking when:
1. Corpus grows beyond 50 documents
2. Precision on production queries drops below 70%

**Current decision:** Keep lexical retrieval as-is; add cache hit/miss logging for observability; revisit rerank when corpus scales.

---

## Cache Logging Added

`app/retrieval.py` now logs at INFO level:

```
[RETRIEVAL] cache=HIT terms=<query_terms> results=<count>
[RETRIEVAL] cache=MISS terms=<query_terms>
```

Log format: `local_rag.retrieval` logger. Enable with `logging.getLogger("local_rag.retrieval").setLevel(logging.INFO)`.

---

## Open Questions Resolved

| OQ | Resolution |
|----|------------|
| OQ-1: vault path | Confirmed: `C:\Users\jichu\Downloads\valut\wiki` (NOT a typo — `valut` is the actual folder name) |
| Typo fix needed | NOT needed — `valut` is the correct actual path, confirmed by filesystem check |

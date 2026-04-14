# Plan: mcp_obsidian Local AI Stack — B+C+D Upgrade

## Overview

Upgrade the local AI stack across three tracks: chat UI usability (B), retrieval quality (C), and memory persistence via mcp_obsidian integration (D).

**Purpose:** Make the stack more usable for daily work, improve answer quality, and connect conversation memory to the Obsidian-backed knowledge base.

---

## Goals

1. **B — UI Upgrade:** chat history, model selector, conversation context persistence
2. **C — local-rag Improvement:** rerank, optional vector DB, better retrieval
3. **D — mcp_obsidian Integration:** standalone → memory tools (save_memory, search_memory) connected

---

## Scope

### In Scope

- `standalone-package/src/docs-browser.ts` — chat UI enhancements
- `standalone-package/src/server.ts` — conversation history store
- `local-rag/` — retrieval quality improvements
- `myagent-copilot-kit/standalone-package/src/local-rag.ts` — mcp_obsidian API client
- `mcp_obsidian/app/services/memory_store.py` — memory tool surface
- `start-all.ps1` — add mcp_obsidian → standalone token/env sharing
- `docs/LOCAL_RAG_STANDALONE_GUIDE.md` — update after changes

### Out of Scope

- New vector DB unless evidence shows current retrieval is the bottleneck
- Obsidian plugin changes
- Changing MCP tool schemas
- Production deployment considerations

---

## Constraints

- Local-only stack; no external services beyond Ollama
- Must not break existing CORS behavior
- `standalone-package` auth remains token-per-service (no SSO)
- mcp_obsidian `/mcp` bearer token stays environment-driven

---

## Phases

```
Phase 1 │ Phase 2 │ Phase 3
B-UI    │ C-local-rag │ D-mcp_obsidian
```

### Phase 1 — B: UI Upgrade

**B1 — Chat History**
- Add in-memory conversation history array (last N messages)
- Render history above input in UI
- Persist to `localStorage` on each send

**B2 — Model Selector**
- Dropdown in UI: `gemma4:e4b` (default) / `gemma4:e2b`
- Send selected model as `model` param in POST body
- Fallback to `gemma4:e4b` if not specified

**B3 — Token Input Persistence**
- Save token input to `localStorage` (masked display)
- Pre-fill on page reload

**B4 — UI Polish**
- Loading state (spinner on send)
- Error banner for non-200 responses
- Clear chat button

### Phase 2 — C: local-rag Retrieval Quality

**C1 — Rerank Evaluation**
- Test current lexical retrieval precision on sample queries
- If precision < 80%, add simple cross-encoder rerank (or mark AMBER)

**C2 — Vector DB Investigation**
- Benchmark lexical retrieval vs. embeddings on sample corpus
- Decision: add embeddings or keep lexical based on evidence

**C3 — Retrieval Cache Audit**
- Confirm cache hit rate on repeated queries
- Add logging if TTL is too short for practical use

**C4 — Docs DIR Env Var Bug**
- `LOCAL_RAG_DOCS_DIR` in local-rag README says `C:\Users\jichu\Downloads\valut\wiki` (typo: `valut` vs `vault`)
- Fix typo; verify path is correct

### Phase 3 — D: mcp_obsidian Integration

**D1 — Token Sharing**
- Share `MYAGENT_LOCAL_RAG_TOKEN` / `MCP_API_TOKEN` env between standalone and mcp_obsidian
- Update `start-all.ps1` to export these before launching services

**D2 — standalone → mcp_obsidian API Client**
- In `standalone-package`, add `/api/memory/search` and `/api/memory/fetch` routes (proxied to mcp_obsidian `8000`)
- Use `MYAGENT_MEMORY_BASE_URL` and `MYAGENT_MEMORY_MCP_PATH`

**D3 — Memory Pointer Flow**
- After successful standalone chat, optionally save summary via mcp_obsidian `save_memory`
- Show "Saved to memory" indicator in UI

**D4 — mcp_obsidian MCP Tool Verification**
- Confirm `save_memory`, `search_memory`, `get_memory` tools reachable from standalone
- Document token header flow in `LOCAL_RAG_STANDALONE_GUIDE.md`

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| local-rag retrieval bottleneck unclear without benchmark | medium | medium | Phase 2 starts with benchmark; skip rerank if lexical already sufficient |
| token sharing introduces auth complexity | low | medium | Keep token per-service; shared secret only for internal routes |
| Phase 2/3 scope creep | medium | high | Lock phase deliverables before starting each phase |

---

## Review Criteria

- [ ] B: user can select model, see chat history, persist token across reloads
- [ ] C: lexical retrieval benchmarked; rerank decision documented
- [ ] D: standalone can proxy memory search/fetch to mcp_obsidian; save_memory works from UI
- [ ] All health endpoints still reachable after changes
- [ ] No new CORS errors introduced
- [ ] `pnpm build` passes after UI changes

---

## Deliverables

| Phase | File |
|-------|------|
| B | `standalone-package/src/docs-browser.ts` (updated UI) |
| B | `docs/LOCAL_RAG_STANDALONE_GUIDE.md` (B section added) |
| C | `local-rag/README.md` (typo fix + benchmark notes) |
| C | `local-rag/` (optional: rerank or vector DB if needed) |
| D | `myagent-copilot-kit/standalone-package/src/mcp-proxy.ts` (new file) |
| D | `start-all.ps1` (updated env sharing) |
| D | `docs/LOCAL_RAG_STANDALONE_GUIDE.md` (D section added) |
| All | `docs/superpowers/specs/2026-04-08-local-rag-standalone-guide-upgrade.md` (updated plan) |

---

## Assumption

- `C:\Users\jichu\Downloads\valut\wiki` in local-rag README is a typo for `vault`. Correct path assumed to be `C:\Users\jichu\Downloads\valut\wiki` — please confirm before Phase 2.
- No vector DB currently deployed; will decide in Phase 2 based on benchmark evidence.

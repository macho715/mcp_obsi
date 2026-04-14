# Task: mcp_obsidian Local AI Stack — B+C+D Upgrade

**Spec:** `Spec.md` (supersedes `docs/superpowers/specs/2026-04-08-local-rag-bcd-upgrade-plan.md`)

---

## Goal

Upgrade the local AI stack across three phases: UI usability (B), retrieval quality (C), mcp_obsidian integration (D). Phase-gated execution: each phase QA-passes before the next begins.

---

## Scope

### In Scope

- Phase B: `standalone-package/src/docs-browser.ts` UI enhancements
- Phase B: `docs/LOCAL_RAG_STANDALONE_GUIDE.md` (B section update)
- Phase C: `local-rag/README.md` typo fix + benchmark + optional rerank
- Phase C: `local-rag/` retrieval improvements
- Phase D: `myagent-copilot-kit/standalone-package/src/mcp-proxy.ts` (new)
- Phase D: `start-all.ps1` token env sharing
- Phase D: `docs/LOCAL_RAG_STANDALONE_GUIDE.md` (D section update)

### Out of Scope

- Vector DB deployment (decision deferred to Phase C benchmark)
- Obsidian plugin changes
- MCP tool schema changes
- Production deployment

---

## Inputs & References

| Input | Path / Source |
|-------|---------------|
| Spec | `Spec.md` |
| Approved plan | `docs/superpowers/specs/2026-04-08-local-rag-bcd-upgrade-plan.md` |
| Standalone server | `myagent-copilot-kit/standalone-package/src/server.ts` |
| Chat UI | `myagent-copilot-kit/standalone-package/src/docs-browser.ts` |
| local-rag README | `local-rag/README.md` |
| start-all.ps1 | `start-all.ps1` |
| local-rag main | `local-rag/app/main.py` |
| mcp_obsidian main | `app/main.py` |

---

## Deliverables

| Phase | File | Change |
|-------|------|--------|
| B | `standalone-package/src/docs-browser.ts` | Updated UI |
| B | `standalone-package/src/server.ts` | History store, proxy routes |
| B | `docs/LOCAL_RAG_STANDALONE_GUIDE.md` | B section added |
| C | `local-rag/README.md` | Typo fix, benchmark notes |
| C | `local-rag/app/main.py` | Cache logging |
| C | `docs/superpowers/specs/TASK-YYYY-MM-DD-001-benchmark.md` | Benchmark report |
| D | `myagent-copilot-kit/standalone-package/src/mcp-proxy.ts` | New file |
| D | `start-all.ps1` | Token env sharing |
| D | `docs/LOCAL_RAG_STANDALONE_GUIDE.md` | D section added |

---

## Acceptance Criteria

### Phase B

- [ ] **AC-B1:** `pnpm build` passes with no TypeScript errors
- [ ] **AC-B2:** Model dropdown visible in UI; switching to `gemma4:e2b` sends correct `model` in POST body
- [ ] **AC-B3:** Sending 3 messages, reloading page → 3 messages visible above input
- [ ] **AC-B4:** Entering token value, reloading → token field pre-filled (masked)
- [ ] **AC-B5:** With local-rag stopped, sending a message → error banner visible; send button re-enabled
- [ ] **AC-B6:** Clicking "Clear chat" → history cleared from UI and localStorage

### Phase C

- [ ] **AC-C1:** `local-rag/README.md` `LOCAL_RAG_DOCS_DIR` contains `vault`, not `valut`
- [ ] **AC-C2:** Benchmark report exists at `docs/superpowers/specs/TASK-*-benchmark.md` with precision@k for ≥10 queries
- [ ] **AC-C3:** If precision@k < 80%, rerank or vector DB implementation exists and passes `pytest -q`
- [ ] **AC-C4:** Cache hit/miss logged at INFO level per request in local-rag

### Phase D

- [ ] **AC-D1:** `GET /api/memory/search?q=...` returns HTTP 200 with valid memory search results
- [ ] **AC-D2:** `GET /api/memory/fetch?memory_id=...` returns HTTP 200 with valid memory note
- [ ] **AC-D3:** "Save to memory" button → `save_memory` call → "Saved to memory" indicator in UI
- [ ] **AC-D4:** `start-all.ps1` exports `MYAGENT_LOCAL_RAG_TOKEN`, `MCP_API_TOKEN`, `MYAGENT_MEMORY_TOKEN` before launching child processes
- [ ] **AC-D5:** Bearer token correctly forwarded from standalone to mcp_obsidian in proxy requests

### All Phases

- [ ] **AC-All1:** All 4 health endpoints return HTTP 200 after changes
- [ ] **AC-All2:** No new CORS errors in browser console

---

## Definition of Done

All of the following must be true:

1. Every AC checkbox above is checked
2. All modified/new files pass `pnpm build` (Phase B) or `pytest -q` (Phase C)
3. No unresolved `[NEEDS CLARIFICATION]` markers remain in this document
4. Git commit exists for each phase with descriptive message
5. PR created and reviewed for all Phase changes

---

## Task List

Phase B (executable now — no blocking open questions):

- [x] **TASK-B1:** Add conversation history array + `localStorage` persist to `docs-browser.ts`
- [x] **TASK-B2:** Add model selector dropdown (`gemma4:e4b`, `gemma4:e2b`) to chat UI
- [x] **TASK-B3:** Send selected model in POST body; fallback to `gemma4:e4b`
- [x] **TASK-B4:** Persist token input to `localStorage`; pre-fill + masked on reload
- [x] **TASK-B5:** Add loading spinner on send; re-enable button on complete/error
- [x] **TASK-B6:** Add error banner for non-200 responses
- [x] **TASK-B7:** Add "Clear chat" button (clears UI + localStorage)
- [x] **TASK-B8:** Update `docs/LOCAL_RAG_STANDALONE_GUIDE.md` with B section
- [x] **TASK-B9:** Run AC-B1 through AC-B6; verify all pass; commit

Phase C (blocked by OQ-1 — vault path confirmation):

- [x] **TASK-C1:** Confirm correct vault path; fix `valut` → `vault` in `local-rag/README.md`
- [x] **TASK-C2:** Run lexical retrieval benchmark (≥10 queries); write report to `docs/superpowers/specs/TASK-*-benchmark.md`
- [x] **TASK-C3:** If precision@k < 80% → implement rerank OR add vector DB (evidence-backed decision)
- [x] **TASK-C4:** Add INFO-level cache hit/miss logging per request to `local-rag/app/main.py`
- [x] **TASK-C5:** Run AC-C1 through AC-C4; verify all pass; commit

Phase D (blocked by OQ-2 — MCP tool surface verification):

- [x] **TASK-D1:** Verify `/chatgpt-mcp` exposes `save_memory`, `search_memory`, `get_memory` in `app/main.py`
- [x] **TASK-D2:** Implement `mcp-proxy.ts` with `/api/memory/search` and `/api/memory/fetch` proxy routes
- [x] **TASK-D3:** Update `start-all.ps1` to export `MYAGENT_LOCAL_RAG_TOKEN`, `MCP_API_TOKEN`, `MYAGENT_MEMORY_TOKEN`
- [x] **TASK-D4:** Add "Save to memory" button and indicator to chat UI
- [x] **TASK-D5:** Update `docs/LOCAL_RAG_STANDALONE_GUIDE.md` with D section
- [x] **TASK-D6:** Run AC-D1 through AC-D5; verify all pass; commit

---

## Dependencies & Risks

| Dependency / Risk | Blocking | Mitigation |
|-------------------|----------|------------|
| OQ-1: vault path confirmation | RESOLVED: `C:\Users\jichu\Downloads\valut\wiki` confirmed by filesystem check | n/a |
| OQ-2: MCP tool surface verification | Phase D | TASK-D1 verifies routes in `app/main.py` before D2 |
| OQ-3: chat history storage scope (localStorage only vs mcp_obsidian) | FR-B1 | [NEEDS CLARIFICATION: localStorage-only for now; flag for user decision] |
| Phase B scope creep | None | Lock B deliverables before starting C |
| Phase C rerank implementation | Phase C | Benchmark-first; evidence-only decision |

---

## Security & Privacy

- No raw bearer tokens in URLs or query strings
- Tokens stored in `localStorage` are masked in the UI; clear on "Clear chat"
- Proxy routes forward bearer token only in `Authorization` header, never in URL
- No raw conversation text persisted to `localStorage` beyond session scope
- mcp_obsidian proxy routes protected by same bearer token enforcement as `/mcp`

---

## Evidence

| Evidence | Location |
|----------|----------|
| Phase B build pass | CI / `pnpm build` output |
| Phase B functional test | Manual browser test against `http://127.0.0.1:3010/` |
| Phase C benchmark report | `docs/superpowers/specs/TASK-*-benchmark.md` |
| Phase C test pass | `pytest -q` output |
| Phase D proxy test | `curl` against `/api/memory/search` and `/api/memory/fetch` |
| Phase D save_memory | GET `/api/memory/fetch?memory_id=...` returns saved note |

---

## Change Log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-04-08 | Initial draft from Spec.md; 3 open questions flagged |

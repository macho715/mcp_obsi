# Spec: mcp_obsidian Local AI Stack — B+C+D Upgrade

> **Supersedes:** Option B plan from `docs/superpowers/specs/2026-04-08-local-rag-standalone-guide-upgrade.md`

---

## Summary

Upgrade the local AI stack across three independent tracks derived from the approved plan. Each phase is self-contained and may be reviewed independently before proceeding to the next.

---

## User Scenarios & Testing

### Phase B — UI Upgrade

**SC-B1: Chat History Persistence**
```
Given  a user has sent 3 messages in the chat UI
When   the user reloads the page
Then   the 3 messages are visible above the input field
And    the conversation context is preserved
```

**SC-B2: Model Selection**
```
Given  a user is on the chat page
When   the user selects "gemma4:e2b" from the model dropdown
And    sends a message
Then   the POST body contains model: "gemma4:e2b"
And    the response comes from the selected model
```

**SC-B3: Token Persistence**
```
Given  a user entered a value in the token input field
When   the page is reloaded
Then   the token field is pre-filled with the saved value
And    the value is masked (••••)
```

**SC-B4: Error Handling**
```
Given  the local-rag service is unreachable
When   the user sends a message
Then   an error banner is displayed with the failure reason
And    the send button is re-enabled
```

### Phase C — local-rag Retrieval Quality

**SC-C1: Lexical Retrieval Benchmark**
```
Given  a corpus of N documents in LOCAL_RAG_DOCS_DIR
When   benchmark is run against 10 sample queries
Then   precision@k is reported
And    if precision < 80%, rerank is triggered
```

**SC-C2: Docs Dir Path**
```
Given  LOCAL_RAG_DOCS_DIR is set
When   local-rag starts
Then   the path resolves to an accessible directory
And    no typo is present in the path string
```

### Phase D — mcp_obsidian Integration

**SC-D1: Memory Proxy Routes**
```
Given  standalone-package is running on :3010
When   the browser calls GET /api/memory/search?q=...
Then   the request is proxied to mcp_obsidian :8000/search_memory
And    the response is returned to the browser
```

**SC-D2: Save Memory from UI**
```
Given  a user completes a chat interaction
When   the user clicks "Save to memory"
Then   a save_memory call is made to mcp_obsidian
And    a "Saved to memory" indicator appears in the UI
```

---

## Requirements

### Phase B — UI

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-B1 | Chat history array persists across page reloads via `localStorage` | Last 50 messages; keyed by `chat_history` |
| FR-B2 | Model selector dropdown with options `gemma4:e4b` (default), `gemma4:e2b` | `model` field added to POST body |
| FR-B3 | Token input persists to `localStorage` | Masked display; pre-fill on load |
| FR-B4 | Loading spinner displayed while awaiting response | Re-enables send button on complete or error |
| FR-B5 | Error banner for non-200 responses | Shows HTTP status or "network error" |
| FR-B6 | Clear chat button resets history | Clears localStorage and UI |

### Phase C — local-rag

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-C1 | Lexical retrieval precision benchmark documented | Min 10 queries; precision@k ≥ 80% to skip rerank |
| FR-C2 | `LOCAL_RAG_DOCS_DIR` path typo corrected | `valut` → `vault` |
| FR-C3 | Retrieval cache hit rate logged | Add `INFO` log per request: cache hit/miss |
| NFR-C1 | Retrieval latency p95 < 2s | Measured on local corpus |

*Decision point (C2/C3): rerank or vector DB only if precision < 80% after benchmark.*

### Phase D — mcp_obsidian Integration

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-D1 | `start-all.ps1` exports shared token env | `MYAGENT_LOCAL_RAG_TOKEN` and `MCP_API_TOKEN` passed to child processes |
| FR-D2 | standalone exposes `/api/memory/search` proxy route | Proxies to `MYAGENT_MEMORY_BASE_URL` + `/chatgpt-mcp` |
| FR-D3 | standalone exposes `/api/memory/fetch` proxy route | Proxies to `MYAGENT_MEMORY_BASE_URL` + `/chatgpt-mcp` |
| FR-D4 | "Save to memory" button triggers `save_memory` | Via proxied mcp_obsidian endpoint |
| FR-D5 | mcp_obsidian bearer token passed correctly | Token from `MYAGENT_MEMORY_TOKEN` env var |
| NFR-D1 | Proxy latency < 500ms | Measured end-to-end for search + fetch |

---

## Assumptions & Dependencies

| Item | Assumption | Validation |
|------|-----------|------------|
| Docs dir path | `C:\Users\jichu\Downloads\valut\wiki` is typo; actual path is `C:\Users\jichu\Downloads\valut\wiki` | [NEEDS CLARIFICATION: confirm actual vault path] |
| Vector DB | Not currently deployed; decision deferred to Phase C benchmark | Evidence-only decision |
| Token scope | `MYAGENT_MEMORY_TOKEN` used for mcp_obsidian proxy auth | Falls back to `MCP_API_TOKEN` if unset |
| mcp_obsidian MCP path | `/chatgpt-mcp` is the correct path for memory tools | Verify against `app/main.py` routes |

---

## Open Questions

| # | Question | Owner | Blocking |
|---|----------|-------|---------|
| OQ-1 | What is the correct vault path? Is it `C:\Users\jichu\Downloads\valut\wiki` or a different path? | user | Phase C cannot start without this |
| OQ-2 | Does `/chatgpt-mcp` expose `save_memory` and `search_memory`? | need to verify | Phase D proxy cannot be implemented without this |
| OQ-3 | Should chat history also be saved to `mcp_obsidian` memory, or only `localStorage`? | user | FR-B1 scope |

---

## Success Criteria

- [ ] Phase B: `pnpm build` passes; model selector functional; chat history survives reload; token pre-fills; error banner shows on 503
- [ ] Phase C: `LOCAL_RAG_DOCS_DIR` typo fixed; benchmark report exists; precision ≥ 80% or rerank implemented
- [ ] Phase D: `/api/memory/search` and `/api/memory/fetch` return valid responses; "Save to memory" completes without error
- [ ] All phases: no new CORS errors; all 4 health endpoints still return 200

---

## Phase Sequence & Gates

```
B (implement) → B (review/qa) → C (implement) → C (review/qa) → D (implement) → D (review/qa) → ship
```

Each phase gates the next. Proceed to next phase only after current phase QA passes.

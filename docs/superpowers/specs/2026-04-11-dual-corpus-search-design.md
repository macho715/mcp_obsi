# Dual-Corpus Search Design

Date: 2026-04-11
Status: Approved design draft
Scope: `memory` + `wiki/analyses` unified search UX with separated MCP contracts

## 1. Summary

This design solves the current search gap where `wiki/analyses/...` notes exist in the vault but are not discoverable through the current MCP search flow.

The chosen direction is:

- User experience: one integrated search box
- Internal MCP contract: keep `memory` and `wiki` as separate corpora
- Canonical source of truth: `memory`
- Analytical overlay: `wiki`
- Merge location: UI or orchestration layer only

The design does **not** merge `wiki` results into existing `search_memory` or existing wrapper `fetch`.

## 2. Problem Definition

Current evidence suggests the issue is closer to corpus separation than search engine failure:

- `list_recent_memories` returns `memory/...` records normally
- `wiki/analyses/...` notes can exist in Obsidian while returning zero hits in current MCP search
- current search behavior is therefore likely scoped to the memory corpus, not the full wiki corpus

This means "recent memory works" does not imply "wiki notes are searchable."

## 3. Decision

Adopt Option 3.

- Preserve the current `memory` search and fetch semantics
- Add a wiki-specific read surface for `wiki/analyses`
- Keep unified search out of the MCP public tool surface in v1
- Perform fan-out and merge only in the UI or orchestration layer

Decision statement:

> User search experience is unified, but MCP internals keep `memory` and `wiki` as separate corpora. `search_memory` and existing memory fetch semantics remain unchanged. `search_wiki` and `fetch_wiki` are added, and results are merged only in the UI or orchestration layer.

## 4. Source-of-Truth Rules

- `memory` remains canonical SSOT
- `wiki` remains a compiled or analytical overlay
- `search_memory` must not silently include wiki results
- existing wrapper `fetch(id)` must not silently become a cross-corpus fetch
- wiki hits must remain identifiable as wiki hits

This follows the current repository direction:

- `memory` is the canonical retrieval layer
- `wiki` is a compiled or canonical note surface for analysis and reference
- pointer-based linking is preferred, but pointer absence must not block direct wiki read

## 5. MCP Tool Surface

### Existing tools preserved

- `search_memory(query, ...)`
- `get_memory(memory_id)`
- existing wrapper `fetch(id)`

### New wiki read tools

- `search_wiki(query, path_prefix="wiki/analyses", limit=8, tags=[], include_snippets=true)`
- `fetch_wiki(path=None, slug=None, include_frontmatter=true, include_body=true)`

### Explicit v1 non-goal

- No public MCP `unified_search` tool in v1

## 6. API Shape

### 6.1 `search_wiki` request

```json
{
  "query": "hazmat shu 2025-11-26",
  "limit": 8,
  "path_prefix": "wiki/analyses",
  "tags": [],
  "include_snippets": true
}
```

### 6.2 `fetch_wiki` request

Primary path form:

```json
{
  "path": "wiki/analyses/logistics_issue_shu_2025-11-26_3",
  "slug": null,
  "include_frontmatter": true,
  "include_body": true
}
```

Fallback slug form:

```json
{
  "path": null,
  "slug": "logistics_issue_shu_2025-11-26_3",
  "include_frontmatter": true,
  "include_body": true
}
```

Resolution rule:

- `path` wins over `slug`
- if both are missing, return validation error

### 6.3 `search_wiki` response hit

```json
{
  "source": "wiki",
  "id": "wiki:analyses/logistics_issue_shu_2025-11-26_3",
  "title": "[SHU Issue] 2025-11-26 Event #3",
  "slug": "logistics_issue_shu_2025-11-26_3",
  "path": "wiki/analyses/logistics_issue_shu_2025-11-26_3.md",
  "category": "analyses",
  "tags": ["analysis", "logistics", "shu", "delivery", "hazmat"],
  "snippet": "...",
  "score": 0.82,
  "fetch_route": "fetch_wiki",
  "related_memory_id": null
}
```

### 6.4 `fetch_wiki` response

```json
{
  "source": "wiki",
  "id": "wiki:analyses/logistics_issue_shu_2025-11-26_3",
  "title": "[SHU Issue] 2025-11-26 Event #3",
  "slug": "logistics_issue_shu_2025-11-26_3",
  "path": "wiki/analyses/logistics_issue_shu_2025-11-26_3.md",
  "category": "analyses",
  "frontmatter": {
    "tags": ["analysis", "logistics", "shu", "delivery", "hazmat"]
  },
  "body": "..."
}
```

## 7. Unified Search Merge Rules

The integrated search UX runs one user query against both corpora:

```text
user query
-> search_memory
-> search_wiki
-> normalize scores per source
-> dedupe carefully
-> return merged result list
```

Important rule:

- merge happens only after corpus-specific search completes
- corpus-specific tools do not include each other's results

## 8. Score Policy

Raw scores should not be merged directly across corpora.

Recommended merge score model:

```text
final_score
= corpus_score_normalized
+ source_bonus
+ exact_match_bonus
+ cross_link_bonus
- stale_penalty
```

Recommended starting policy:

- `memory` gets slight canonical priority
- `wiki` remains visible as analytical context
- exact slug or title matches get strong boosts
- stale wiki penalties stay weak in v1

## 9. Dedupe Rules

### Strong dedupe

Allow collapse only when there is strong evidence:

- explicit `related_memory_id`
- explicit `related_wiki_path`
- exact path match
- exact slug match

### Weak similarity

Do **not** collapse on weak signals alone:

- similar normalized title
- same date
- overlapping tags or entities

Weak similarity should remain as separate results or "related candidate" grouping.

## 10. Badge Rules

Every merged result must show its origin clearly.

### Required badges

- source badge: `Memory` or `Wiki`
- role badge: `Canonical`, `Pointer`, or `Analyses`
- optional relation badge: `Linked`

Examples:

- `[Memory][Canonical]`
- `[Memory][Pointer]`
- `[Wiki][Analyses]`
- `[Wiki][Analyses][Linked]`

## 11. Click and Fetch Routing

Search can be unified. Fetch must remain source-specific.

### Memory result click

- use `get_memory` or existing wrapper `fetch`
- show memory content
- show related wiki links when available

### Wiki result click

- use `fetch_wiki`
- show wiki body and frontmatter
- show related memory link when available

Strict rule:

- no hidden unified fetch in v1
- no automatic redirect from wiki hit to memory fetch
- no automatic redirect from memory hit to wiki fetch

## 12. Rollout Plan

### Phase 1

- implement `search_wiki`
- implement `fetch_wiki`
- limit scope to `wiki/analyses`

### Phase 2

- add UI or orchestration fan-out
- add source badges
- add minimal merge and click routing

### Phase 3

- pointer backfill
- related-link enrichment
- relevance tuning
- wider wiki scope beyond `wiki/analyses`

## 13. Test Strategy

### Unit tests

- `search_wiki` path scoping
- `search_wiki` title, slug, tags, and body matching
- `fetch_wiki` path-first resolution
- `fetch_wiki` slug fallback
- merge helper keeps source labels
- merge helper dedupes only on strong link evidence

### Integration tests

- existing `search_memory`, `get_memory`, and wrapper `fetch` unchanged
- `search_wiki` and `fetch_wiki` remain read-only
- no public MCP `unified_search` in v1

### Manual tests

1. query `hazmat shu 2025-11-26`
2. click a memory result and verify memory fetch path
3. click a wiki result and verify wiki fetch path

## 14. Feature Gates

Recommended initial gates:

- `WIKI_SEARCH_ENABLED=true`
- `UNIFIED_SEARCH_UI_ENABLED=true`

This allows:

- backend read surface first
- UI merge second
- immediate rollback to memory-only mode if needed

## 15. Rollback Rules

Rollback immediately if any of the following occurs:

- existing memory search behavior changes
- wiki result click routes to memory fetch incorrectly
- source badges disappear
- search escapes `wiki/analyses` unintentionally in v1

Rollback action:

- disable `search_wiki` and `fetch_wiki`
- disable unified search UI
- fall back to memory-only search UX

## 16. Explicit Non-Goals

v1 does not include:

- public MCP `unified_search`
- pointer backfill
- cross-corpus automatic write behavior
- hidden or automatic fetch unification
- broad wiki scope beyond `wiki/analyses`

## 17. Self-Review

Spec check completed:

- no placeholder markers left
- no contradiction with memory-as-SSOT rule
- no contradiction with wiki-as-overlay rule
- scope kept to v1 read-only expansion plus orchestration merge
- implementation file map intentionally deferred to planning stage

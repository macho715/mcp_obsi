# Dual-Corpus Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `wiki/analyses` read-only search and fetch support without changing canonical memory semantics, then expose a unified search UX through the standalone orchestration layer.

**Architecture:** Keep MCP contracts split by corpus. `app/` gains `search_wiki` and `fetch_wiki` as explicit read-only tools alongside existing memory tools. `myagent-copilot-kit/standalone-package/` performs fan-out, score normalization, dedupe, and click-route branching so the user sees one search experience while fetch stays source-specific. This plan intentionally spans two targets in the same workspace: repo-owned MCP runtime under `app/` and the workspace-local companion runtime under `myagent-copilot-kit/standalone-package/`; the companion edits are explicit scope, not accidental ownership expansion.

**Tech Stack:** FastAPI, FastMCP, Python services/tests with pytest, TypeScript + Express + node:test in `standalone-package`

---

## File Structure

## Execution Boundary

- `app/`, `tests/`, `scripts/`, and root/docs changes belong to the MCP server contract owned by this repo.
- `myagent-copilot-kit/standalone-package/` changes are part of this approved implementation scope because unified search is intentionally defined as an orchestration or UI-layer concern.
- Do not expand beyond the listed companion files in this plan without a new approval pass.
- Do not treat the companion runtime as a reason to rewrite existing `memory` MCP semantics. MCP remains corpus-split; orchestration is the only merge layer.

### Create

- `app/services/wiki_search_service.py`
  Read-only wiki corpus search and fetch for `wiki/analyses`
- `tests/test_wiki_search_service.py`
  Unit tests for path scoping, snippets, path fetch, slug fetch
- `tests/test_dual_corpus_mcp.py`
  MCP-level tests for `search_wiki` and `fetch_wiki`
- `myagent-copilot-kit/standalone-package/src/unified-search.ts`
  UI/orchestration-only fan-out, normalization, dedupe, and route labeling
- `myagent-copilot-kit/standalone-package/src/unified-search.test.ts`
  Node tests for merge ordering, dedupe, and badge/source preservation

### Modify

- `app/mcp_server.py`
  Register `search_wiki` and `fetch_wiki` on the main MCP surface
- `app/chatgpt_mcp_server.py`
  Add read-only `search_wiki` and `fetch_wiki` to the ChatGPT specialist surface
- `app/claude_mcp_server.py`
  Add read-only `search_wiki` and `fetch_wiki` to the Claude specialist surface
- `tests/test_chatgpt_mcp_server.py`
  Update expected read-only and write-capable tool surfaces
- `tests/test_claude_mcp_server.py`
  Update expected read-only and write-capable tool surfaces
- `scripts/verify_chatgpt_mcp_readonly.py`
  Accept `search_wiki` and `fetch_wiki` on read-only specialist routes
- `scripts/verify_claude_mcp_readonly.py`
  Accept `search_wiki` and `fetch_wiki` on read-only specialist routes
- `scripts/mcp_local_tool_smoke.py`
  Update expected read-only tool set and wrapper smoke assumptions
- `myagent-copilot-kit/standalone-package/src/mcp-memory-client.ts`
  Add `searchWiki()` and `fetchWiki()` helpers while keeping memory helpers unchanged
- `myagent-copilot-kit/standalone-package/src/server.ts`
  Add `/api/wiki/search`, `/api/wiki/fetch`, and `/api/search/unified`
- `myagent-copilot-kit/standalone-package/src/docs-browser.ts`
  Add a single search form and result list with source badges and source-specific fetch routing
- `myagent-copilot-kit/standalone-package/README.md`
  Document new unified search and wiki fetch routes
- `README.md`
  Document dual-corpus search rollout and current scope (`wiki/analyses` only)
- `SYSTEM_ARCHITECTURE.md`
  Document new read-only wiki MCP surface and orchestration-only merge
- `docs/CHATGPT_MCP.md`
  Document read-only specialist additions
- `docs/CLAUDE_MCP.md`
  Document read-only specialist additions
- `changelog.md`
  Record the dual-corpus implementation

## Task 1: Build Read-Only Wiki Search Service

**Files:**
- Create: `app/services/wiki_search_service.py`
- Test: `tests/test_wiki_search_service.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from app.services.wiki_search_service import WikiSearchService


def test_search_wiki_limits_to_analyses_prefix(tmp_path: Path):
    vault = tmp_path / "vault"
    analyses = vault / "wiki" / "analyses"
    concepts = vault / "wiki" / "concepts"
    analyses.mkdir(parents=True)
    concepts.mkdir(parents=True)

    (analyses / "logistics_issue_shu_2025-11-26_3.md").write_text(
        "---\n"
        "tags:\n"
        "  - analysis\n"
        "  - hazmat\n"
        "---\n\n"
        "# [SHU Issue] 2025-11-26 Event #3\n\n"
        "hazmat delivery hold at SHU\n",
        encoding="utf-8",
    )
    (concepts / "shu-hazmat.md").write_text(
        "# SHU Hazmat Concept\n\nhazmat concept only\n",
        encoding="utf-8",
    )

    service = WikiSearchService(vault)
    result = service.search(
        query="hazmat shu 2025-11-26",
        path_prefix="wiki/analyses",
        limit=5,
    )

    assert [item["path"] for item in result["results"]] == [
        "wiki/analyses/logistics_issue_shu_2025-11-26_3.md"
    ]
    assert result["results"][0]["fetch_route"] == "fetch_wiki"


def test_fetch_wiki_prefers_path_and_falls_back_to_slug(tmp_path: Path):
    vault = tmp_path / "vault"
    analyses = vault / "wiki" / "analyses"
    analyses.mkdir(parents=True)
    note_path = analyses / "logistics_issue_shu_2025-11-26_3.md"
    note_path.write_text(
        "---\n"
        "tags:\n"
        "  - analysis\n"
        "  - hazmat\n"
        "---\n\n"
        "# [SHU Issue] 2025-11-26 Event #3\n\n"
        "hazmat delivery hold at SHU\n",
        encoding="utf-8",
    )

    service = WikiSearchService(vault)

    by_path = service.fetch(path="wiki/analyses/logistics_issue_shu_2025-11-26_3")
    by_slug = service.fetch(slug="logistics_issue_shu_2025-11-26_3")

    assert by_path["path"] == "wiki/analyses/logistics_issue_shu_2025-11-26_3.md"
    assert by_slug["slug"] == "logistics_issue_shu_2025-11-26_3"
    assert "hazmat delivery hold" in by_slug["body"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_wiki_search_service.py -q
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `app.services.wiki_search_service`.

- [ ] **Step 3: Write the minimal implementation**

```python
from pathlib import Path
import re
import yaml


class WikiSearchService:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path

    def search(self, query: str, path_prefix: str = "wiki/analyses", limit: int = 8) -> dict:
        terms = [term.casefold() for term in query.split() if term.strip()]
        prefix = self.vault_path / Path(path_prefix)
        results = []
        for path in prefix.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            frontmatter, body = self._split_frontmatter(text)
            title = self._extract_title(body, path.stem)
            haystack = "\n".join(
                [
                    title,
                    body,
                    " ".join(frontmatter.get("tags", [])),
                    path.stem,
                ]
            ).casefold()
            score = sum(1 for term in terms if term in haystack)
            if score <= 0:
                continue
            rel_path = path.relative_to(self.vault_path).as_posix()
            results.append(
                {
                    "source": "wiki",
                    "id": f"wiki:{rel_path.removesuffix('.md')}",
                    "title": title,
                    "slug": path.stem,
                    "path": rel_path,
                    "category": rel_path.split('/')[1] if rel_path.count('/') >= 1 else None,
                    "tags": frontmatter.get("tags", []),
                    "snippet": body[:240].strip(),
                    "score": float(score),
                    "fetch_route": "fetch_wiki",
                    "related_memory_id": frontmatter.get("related_memory_id"),
                }
            )
        results.sort(key=lambda item: (-item["score"], item["title"]))
        return {"results": results[:limit]}

    def fetch(self, path: str | None = None, slug: str | None = None) -> dict:
        note_path = self._resolve_path(path=path, slug=slug)
        if note_path is None or not note_path.exists():
            return {"status": "not_found", "source": "wiki"}
        text = note_path.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(text)
        rel_path = note_path.relative_to(self.vault_path).as_posix()
        return {
            "source": "wiki",
            "id": f"wiki:{rel_path.removesuffix('.md')}",
            "title": self._extract_title(body, note_path.stem),
            "slug": note_path.stem,
            "path": rel_path,
            "category": rel_path.split('/')[1] if rel_path.count('/') >= 1 else None,
            "frontmatter": frontmatter,
            "body": body.strip(),
            "related_memory_id": frontmatter.get("related_memory_id"),
        }

    def _resolve_path(self, path: str | None, slug: str | None) -> Path | None:
        if path:
            clean = path.strip().strip("/")
            candidate = self.vault_path / clean
            return candidate if candidate.suffix == ".md" else candidate.with_suffix(".md")
        if slug:
            matches = list((self.vault_path / "wiki" / "analyses").rglob(f"{slug}.md"))
            return matches[0] if matches else None
        return None

    def _split_frontmatter(self, text: str) -> tuple[dict, str]:
        if text.startswith("---\n"):
            _, raw_frontmatter, body = text.split("---\n", 2)
            return yaml.safe_load(raw_frontmatter) or {}, body
        return {}, text

    def _extract_title(self, body: str, fallback: str) -> str:
        match = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
        return match.group(1).strip() if match else fallback
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_wiki_search_service.py -q
```

Expected: PASS with `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add app/services/wiki_search_service.py tests/test_wiki_search_service.py
git commit -m "feat: add wiki search service"
```

## Task 2: Expose Wiki Read Tools on MCP Surfaces

**Files:**
- Modify: `app/mcp_server.py`
- Modify: `app/chatgpt_mcp_server.py`
- Modify: `app/claude_mcp_server.py`
- Create: `tests/test_dual_corpus_mcp.py`
- Modify: `tests/test_chatgpt_mcp_server.py`
- Modify: `tests/test_claude_mcp_server.py`

- [ ] **Step 1: Write the failing MCP tests**

```python
from pathlib import Path

from app.chatgpt_mcp_server import create_chatgpt_mcp_server
from app.claude_mcp_server import create_claude_mcp_server
from app.services.memory_store import MemoryStore


def test_chatgpt_readonly_surface_includes_wiki_read_tools(tmp_path: Path):
    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_chatgpt_mcp_server(store)
    names = set(server._tool_manager._tools)
    assert "search_wiki" in names
    assert "fetch_wiki" in names
    assert "save_memory" not in names


def test_claude_write_surface_keeps_memory_tools_and_adds_wiki_read_tools(tmp_path: Path):
    store = MemoryStore(tmp_path / "vault", tmp_path / "data" / "memory_index.sqlite3")
    server = create_claude_mcp_server(store, include_write_tools=True)
    names = set(server._tool_manager._tools)
    assert {"search", "fetch", "list_recent_memories", "save_memory", "get_memory", "update_memory"}.issubset(names)
    assert {"search_wiki", "fetch_wiki"}.issubset(names)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_dual_corpus_mcp.py tests\test_chatgpt_mcp_server.py tests\test_claude_mcp_server.py -q
```

Expected: FAIL because `search_wiki` and `fetch_wiki` are not registered yet.

- [ ] **Step 3: Register the new tools**

```python
# app/mcp_server.py
from app.services.wiki_search_service import WikiSearchService

def create_mcp_server(store: MemoryStore):
    ...
    wiki_search = WikiSearchService(store.vault_path)

    @mcp.tool()
    async def search_wiki(
        query: str,
        path_prefix: str = "wiki/analyses",
        limit: int = 8,
        tags: list[str] | None = None,
        include_snippets: bool = True,
    ) -> dict:
        result = wiki_search.search(query=query, path_prefix=path_prefix, limit=limit)
        if not include_snippets:
            for item in result["results"]:
                item["snippet"] = None
        if tags:
            wanted = {tag.casefold() for tag in tags}
            result["results"] = [
                item
                for item in result["results"]
                if wanted.intersection(tag.casefold() for tag in item.get("tags", []))
            ]
        return result

    @mcp.tool()
    async def fetch_wiki(
        path: str | None = None,
        slug: str | None = None,
        include_frontmatter: bool = True,
        include_body: bool = True,
    ) -> dict:
        payload = wiki_search.fetch(path=path, slug=slug)
        if not include_frontmatter:
            payload["frontmatter"] = None
        if not include_body:
            payload["body"] = ""
        return payload
```

```python
# app/chatgpt_mcp_server.py and app/claude_mcp_server.py
wiki_search = WikiSearchService(store.vault_path)

@mcp.tool(name="search_wiki", title="Search wiki analyses", structured_output=False)
async def search_wiki(query: str, path_prefix: str = "wiki/analyses", limit: int = 8) -> str:
    return json.dumps(
        wiki_search.search(query=query, path_prefix=path_prefix, limit=limit),
        ensure_ascii=False,
    )

@mcp.tool(name="fetch_wiki", title="Fetch wiki note", structured_output=False)
async def fetch_wiki(
    path: str | None = None,
    slug: str | None = None,
    include_frontmatter: bool = True,
    include_body: bool = True,
) -> str:
    payload = wiki_search.fetch(path=path, slug=slug)
    if not include_frontmatter:
        payload["frontmatter"] = None
    if not include_body:
        payload["body"] = ""
    return json.dumps(payload, ensure_ascii=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_dual_corpus_mcp.py tests\test_chatgpt_mcp_server.py tests\test_claude_mcp_server.py -q
```

Expected: PASS and the existing memory tool expectations remain green.

- [ ] **Step 5: Commit**

```bash
git add app/mcp_server.py app/chatgpt_mcp_server.py app/claude_mcp_server.py tests/test_dual_corpus_mcp.py tests/test_chatgpt_mcp_server.py tests/test_claude_mcp_server.py
git commit -m "feat: expose wiki read tools on MCP routes"
```

## Task 3: Update Local Verification Scripts for the New Read-Only Surface

**Files:**
- Modify: `scripts/verify_chatgpt_mcp_readonly.py`
- Modify: `scripts/verify_claude_mcp_readonly.py`
- Modify: `scripts/mcp_local_tool_smoke.py`

- [ ] **Step 1: Write the failing assertions into the scripts**

```python
# verify_chatgpt_mcp_readonly.py and verify_claude_mcp_readonly.py
expected_tools = ["search", "fetch", "list_recent_memories", "search_wiki", "fetch_wiki"]
if tool_names != expected_tools:
    raise RuntimeError(f"unexpected tool surface: {tool_names}")
```

```python
# scripts/mcp_local_tool_smoke.py
def expected_tool_names(mode: str) -> set[str]:
    if mode == "wrapper":
        return {"search", "fetch", "list_recent_memories", "search_wiki", "fetch_wiki"}
    return {"search_memory", "list_recent_memories", "get_memory", "search_wiki", "fetch_wiki"}
```

- [ ] **Step 2: Run the scripts against local MCP and verify they fail before code changes land**

Run:

```powershell
.venv\Scripts\python.exe scripts\verify_chatgpt_mcp_readonly.py --server-url http://127.0.0.1:8000/chatgpt-mcp/
.venv\Scripts\python.exe scripts\verify_claude_mcp_readonly.py --server-url http://127.0.0.1:8000/claude-mcp/
```

Expected: FAIL on unexpected tool list if Task 2 is not complete yet.

Local-only note:

- This task updates local route verification expectations only.
- Do not change production expected outcomes here. Deployed production may still lag the local code surface until redeploy.

- [ ] **Step 3: Implement the final verification updates**

```python
# scripts/verify_chatgpt_mcp_readonly.py
wiki_search = await session.call_tool("search_wiki", {"query": resolved_title, "path_prefix": "wiki/analyses", "limit": 3})
wiki_fetch = None
wiki_results = parse_tool_payload(wiki_search).get("results", [])
if wiki_results:
    first = wiki_results[0]
    wiki_fetch = await session.call_tool("fetch_wiki", {"path": first["path"].removesuffix(".md")})
```

```python
# scripts/mcp_local_tool_smoke.py
if "search_wiki" in tool_names:
    await session.call_tool("search_wiki", {"query": "hazmat", "path_prefix": "wiki/analyses", "limit": 1})
```

- [ ] **Step 4: Run the scripts again**

Run:

```powershell
.venv\Scripts\python.exe scripts\verify_chatgpt_mcp_readonly.py --server-url http://127.0.0.1:8000/chatgpt-mcp/
.venv\Scripts\python.exe scripts\verify_claude_mcp_readonly.py --server-url http://127.0.0.1:8000/claude-mcp/
.venv\Scripts\python.exe scripts\mcp_local_tool_smoke.py --server-url http://127.0.0.1:8000/chatgpt-mcp/ --mode wrapper
```

Expected: PASS locally with the expanded read-only tool set.

Do not interpret this as a production pass. This is only the local contract gate.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify_chatgpt_mcp_readonly.py scripts/verify_claude_mcp_readonly.py scripts/mcp_local_tool_smoke.py
git commit -m "test: update readonly verification for wiki search"
```

## Task 4: Add Standalone Wiki Client and Merge Helper

**Files:**
- Modify: `myagent-copilot-kit/standalone-package/src/mcp-memory-client.ts`
- Create: `myagent-copilot-kit/standalone-package/src/unified-search.ts`
- Create: `myagent-copilot-kit/standalone-package/src/unified-search.test.ts`

- [ ] **Step 1: Write the failing merge tests**

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { mergeSearchResults } from "./unified-search.js";

test("mergeSearchResults keeps source labels and memory priority", () => {
  const result = mergeSearchResults({
    memory: [
      {
        source: "memory",
        id: "MEM-1",
        title: "KB: SHU issue pointer",
        score: 0.8,
        fetchRoute: "fetch",
        relatedWikiPath: "wiki/analyses/logistics_issue_shu_2025-11-26_3.md",
      },
    ],
    wiki: [
      {
        source: "wiki",
        id: "wiki:analyses/logistics_issue_shu_2025-11-26_3",
        title: "[SHU Issue] 2025-11-26 Event #3",
        score: 0.9,
        fetchRoute: "fetch_wiki",
        path: "wiki/analyses/logistics_issue_shu_2025-11-26_3.md",
      },
    ],
    limit: 5,
  });

  assert.equal(result[0].source, "memory");
  assert.equal(result[1].source, "wiki");
  assert.equal(result[1].badges.includes("Linked"), true);
});
```

- [ ] **Step 2: Run the node tests to verify they fail**

Run:

```powershell
cd myagent-copilot-kit\standalone-package
node --import tsx --test src/unified-search.test.ts
```

Expected: FAIL because `src/unified-search.ts` does not exist yet.

- [ ] **Step 3: Implement the client helpers and merge helper**

```ts
// src/mcp-memory-client.ts
export type WikiSearchItem = {
  source: "wiki";
  id: string;
  title: string;
  slug?: string | null;
  path?: string | null;
  category?: string | null;
  tags?: string[];
  snippet?: string | null;
  score: number;
  fetch_route: "fetch_wiki";
  related_memory_id?: string | null;
};

export async function searchWiki(
  options: MemoryClientOptions,
  params: { query: string; pathPrefix?: string; limit?: number },
): Promise<{ results: WikiSearchItem[] }> {
  const envelope = await callTool<ToolEnvelope<{ results: WikiSearchItem[] }>>(
    options,
    "search_wiki",
    {
      query: params.query,
      path_prefix: params.pathPrefix ?? "wiki/analyses",
      limit: params.limit ?? 8,
    },
  );
  return unwrapToolResult(envelope);
}

export async function fetchWiki(
  options: MemoryClientOptions,
  params: { path?: string; slug?: string },
) {
  const envelope = await callTool<ToolEnvelope<Record<string, unknown>>>(
    options,
    "fetch_wiki",
    params.path ? { path: params.path } : { slug: params.slug },
  );
  return unwrapToolResult(envelope);
}
```

```ts
// src/unified-search.ts
export function mergeSearchResults(params: {
  memory: Array<Record<string, unknown>>;
  wiki: Array<Record<string, unknown>>;
  limit: number;
}) {
  const normalizedMemory = params.memory.map((item) => ({
    ...item,
    source: "memory",
    normalizedScore: Number(item.score ?? 0) + 0.08,
    badges: ["Memory", "Canonical"],
  }));
  const normalizedWiki = params.wiki.map((item) => ({
    ...item,
    source: "wiki",
    normalizedScore: Number(item.score ?? 0),
    badges: [
      "Wiki",
      "Analyses",
      item.related_memory_id ? "Linked" : null,
    ].filter(Boolean),
  }));
  return [...normalizedMemory, ...normalizedWiki]
    .sort((a, b) => Number(b.normalizedScore) - Number(a.normalizedScore))
    .slice(0, params.limit);
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
cd myagent-copilot-kit\standalone-package
node --import tsx --test src/unified-search.test.ts
```

Expected: PASS with the merge helper preserving source and memory priority.

- [ ] **Step 5: Commit**

```bash
git add myagent-copilot-kit/standalone-package/src/mcp-memory-client.ts myagent-copilot-kit/standalone-package/src/unified-search.ts myagent-copilot-kit/standalone-package/src/unified-search.test.ts
git commit -m "feat: add standalone dual-corpus merge helper"
```

## Task 5: Add Standalone Unified Search Endpoints and Browser UI

**Files:**
- Modify: `myagent-copilot-kit/standalone-package/src/server.ts`
- Modify: `myagent-copilot-kit/standalone-package/src/docs-browser.ts`
- Modify: `myagent-copilot-kit/standalone-package/README.md`

- [ ] **Step 1: Write the failing endpoint and UI expectations**

```ts
// Add to README-driven acceptance checklist:
// GET /api/wiki/search?q=hazmat
// GET /api/wiki/fetch?path=wiki/analyses/logistics_issue_shu_2025-11-26_3
// GET /api/search/unified?q=hazmat
```

```html
<!-- docs-browser.ts target UI fragment -->
<div class="card">
  <strong>Unified Search</strong>
  <input id="search-query" placeholder="예: hazmat shu 2025-11-26" />
  <button id="run-search" type="button">검색</button>
  <ul id="search-results"></ul>
</div>
```

- [ ] **Step 2: Add the server endpoints**

```ts
// src/server.ts
import { fetchWiki, searchWiki } from "./mcp-memory-client.js";
import { mergeSearchResults } from "./unified-search.js";

app.get("/api/wiki/search", authTokenMiddleware, async (req, res) => {
  const query = readSingleValue(req.query.q);
  if (!query) {
    res.status(400).json({ error: "WIKI_QUERY_REQUIRED", detail: "Pass a non-empty `q`." });
    return;
  }
  const payload = await searchWiki(memoryClientOptions, {
    query,
    pathPrefix: "wiki/analyses",
    limit: 8,
  });
  res.json(payload);
});

app.get("/api/wiki/fetch", authTokenMiddleware, async (req, res) => {
  const path = readSingleValue(req.query.path);
  const slug = readSingleValue(req.query.slug);
  if (!path && !slug) {
    res.status(400).json({ error: "WIKI_PATH_OR_SLUG_REQUIRED", detail: "Pass `path` or `slug`." });
    return;
  }
  const payload = await fetchWiki(memoryClientOptions, path ? { path } : { slug });
  res.status(payload.status === "not_found" ? 404 : 200).json(payload);
});

app.get("/api/search/unified", authTokenMiddleware, async (req, res) => {
  const query = readSingleValue(req.query.q);
  if (!query) {
    res.status(400).json({ error: "SEARCH_QUERY_REQUIRED", detail: "Pass a non-empty `q`." });
    return;
  }
  const [memory, wiki] = await Promise.all([
    searchMemory(memoryClientOptions, { query }),
    searchWiki(memoryClientOptions, { query, pathPrefix: "wiki/analyses", limit: 8 }),
  ]);
  const results = mergeSearchResults({
    memory: memory.results,
    wiki: wiki.results,
    limit: 10,
  });
  res.json({ query, results, meta: { sources_searched: ["memory", "wiki"] } });
});
```

- [ ] **Step 3: Add the browser-side search box and source-specific fetch routing**

```html
<!-- src/docs-browser.ts inside renderChatHtml() -->
<div class="card">
  <strong>Unified Search</strong>
  <div class="controls" style="margin-top:10px">
    <input id="search-query" type="text" placeholder="예: hazmat shu 2025-11-26" />
    <button id="run-search" type="button" class="secondary">검색</button>
  </div>
  <ul id="search-results"></ul>
</div>
```

```js
const searchQueryEl = document.getElementById("search-query");
const runSearchEl = document.getElementById("run-search");
const searchResultsEl = document.getElementById("search-results");

runSearchEl.addEventListener("click", async function () {
  const query = searchQueryEl.value.trim();
  if (!query) return;
  const headers = {};
  if (tokenEl.value.trim()) { headers["x-ai-proxy-token"] = tokenEl.value.trim(); }
  const response = await fetch("/api/search/unified?q=" + encodeURIComponent(query), { headers });
  const payload = await response.json();
  searchResultsEl.innerHTML = "";
  (payload.results || []).forEach(function (item) {
    const li = document.createElement("li");
    const badges = (item.badges || []).map(function (badge) {
      return "[" + badge + "]";
    }).join("");
    const button = document.createElement("button");
    button.textContent = badges + " " + item.title;
    button.addEventListener("click", async function () {
      const route = item.source === "wiki"
        ? "/api/wiki/fetch?path=" + encodeURIComponent(item.path.replace(/\\.md$/, ""))
        : "/api/memory/fetch?id=" + encodeURIComponent(item.id);
      const fetchRes = await fetch(route, { headers });
      const fetchPayload = await fetchRes.json();
      answerEl.textContent = fetchPayload.body || fetchPayload.text || JSON.stringify(fetchPayload, null, 2);
    });
    li.appendChild(button);
    searchResultsEl.appendChild(li);
  });
});
```

- [ ] **Step 4: Run targeted verification**

Run:

```powershell
cd myagent-copilot-kit\standalone-package
node --import tsx --test src/unified-search.test.ts
pnpm check
```

Then manual:

```powershell
curl "http://127.0.0.1:3010/api/wiki/search?q=hazmat"
curl "http://127.0.0.1:3010/api/search/unified?q=hazmat"
curl "http://127.0.0.1:3010/api/wiki/fetch?path=wiki/analyses/logistics_issue_shu_2025-11-26_3"
```

Expected:

- `/api/wiki/search` returns only wiki results
- `/api/search/unified` returns mixed results with source badges
- `/api/wiki/fetch` returns wiki body/frontmatter without touching memory fetch

- [ ] **Step 5: Commit**

```bash
git add myagent-copilot-kit/standalone-package/src/server.ts myagent-copilot-kit/standalone-package/src/docs-browser.ts myagent-copilot-kit/standalone-package/README.md
git commit -m "feat: add standalone unified search routes"
```

## Task 6: Final Docs and Regression Pass

**Files:**
- Modify: `README.md`
- Modify: `SYSTEM_ARCHITECTURE.md`
- Modify: `docs/CHATGPT_MCP.md`
- Modify: `docs/CLAUDE_MCP.md`
- Modify: `changelog.md`

- [ ] **Step 1: Update the docs with the exact new contract**

```md
- `search_memory` remains canonical memory search only
- `search_wiki` and `fetch_wiki` are read-only wiki tools scoped to `wiki/analyses` in v1
- unified search is implemented in the standalone orchestration layer, not as a public MCP tool
```

- [ ] **Step 2: Run the Python regression suite**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_wiki_search_service.py tests\test_dual_corpus_mcp.py tests\test_chatgpt_mcp_server.py tests\test_claude_mcp_server.py tests\test_search_v2.py -q
.venv\Scripts\python.exe -m ruff check app tests\test_wiki_search_service.py tests\test_dual_corpus_mcp.py tests\test_chatgpt_mcp_server.py tests\test_claude_mcp_server.py
.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"
```

Expected:

- pytest PASS
- ruff PASS
- import prints `obsidian-mcp`

- [ ] **Step 3: Run the standalone regression checks**

Run:

```powershell
cd myagent-copilot-kit\standalone-package
node --import tsx --test src/unified-search.test.ts src/proxy-middleware.test.ts
pnpm check
```

Expected: PASS with no new route or typing regressions.

- [ ] **Step 4: Manual click-through**

Manual flow:

1. Open `/chat`
2. Search `hazmat shu 2025-11-26`
3. Verify one memory hit and one wiki hit can coexist
4. Click memory hit and confirm memory fetch path
5. Click wiki hit and confirm wiki fetch path
6. Confirm badges remain visible

- [ ] **Step 5: Run the post-redeploy production gate**

Run only after the updated code has been deployed:

```powershell
.venv\Scripts\python.exe scripts\verify_chatgpt_mcp_readonly.py --server-url https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp/
.venv\Scripts\python.exe scripts\verify_claude_mcp_readonly.py --server-url https://mcp-server-production-90cb.up.railway.app/claude-mcp/
```

Expected:

- PASS only after the production deployment exposes `search_wiki` and `fetch_wiki`
- if production still returns the old tool list, stop here and treat it as deployment lag, not implementation failure

- [ ] **Step 6: Commit**

```bash
git add README.md SYSTEM_ARCHITECTURE.md docs/CHATGPT_MCP.md docs/CLAUDE_MCP.md changelog.md
git commit -m "docs: record dual-corpus search rollout"
```

## Spec Coverage Check

- `search_wiki` and `fetch_wiki` added: covered by Tasks 1 and 2
- `wiki/analyses` only in v1: covered by Tasks 1, 4, and 6
- unified search in UI/orchestration only: covered by Tasks 4 and 6
- source-specific fetch routing: covered by Task 5
- source badges and dedupe policy: covered by Tasks 4 and 5
- no public MCP `unified_search`: enforced in Tasks 2 and 6

## Placeholder Scan

No `TODO`, `TBD`, or implicit "handle later" language remains in this plan. Every task includes exact files, code, commands, and expected outcomes.

## Type Consistency Check

- MCP wiki tools use `search_wiki` and `fetch_wiki` consistently
- standalone merge helper is named `mergeSearchResults` consistently
- UI routes use `/api/wiki/search`, `/api/wiki/fetch`, and `/api/search/unified` consistently
